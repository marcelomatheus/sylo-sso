"use client";

import axios, { AxiosError } from "axios";

import { isSessionExpired, type SessionState } from "@/features/auth/lib/session";
import { config } from "@/lib/config";
import { authStore } from "@/features/auth/store/auth-store";

type RetryableRequest = {
  _retry?: boolean;
  headers?: Record<string, string>;
};

export const http = axios.create({
  baseURL: config.apiBaseUrl,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

let refreshPromise: Promise<SessionState> | null = null;

async function refreshAdminSession(refreshToken: string): Promise<SessionState> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${config.apiBaseUrl}/oauth/v1/token`, {
        grant_type: "refresh_token",
        refresh_token: refreshToken,
      })
      .then((response) => {
        const current = authStore.getState().session;
        const nextSession: SessionState = {
          accessToken: response.data.access_token,
          refreshToken: response.data.refresh_token,
          expiresAt: response.data.expires_at,
          user: current?.user ?? null,
        };
        authStore.getState().setSession(nextSession);
        return nextSession;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

http.interceptors.request.use(async (request) => {
  const session = authStore.getState().session;
  if (session?.refreshToken && isSessionExpired(session.expiresAt)) {
    try {
      await refreshAdminSession(session.refreshToken);
    } catch {
      authStore.getState().clearSession();
      return request;
    }
  }
  const accessToken = authStore.getState().session?.accessToken;
  if (accessToken) {
    request.headers.Authorization = `Bearer ${accessToken}`;
  }
  return request;
});

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & RetryableRequest;
    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry) {
      throw error;
    }

    const refreshToken = authStore.getState().session?.refreshToken;
    if (!refreshToken) {
      authStore.getState().clearSession();
      throw error;
    }

    originalRequest._retry = true;
    try {
      const nextSession = await refreshAdminSession(refreshToken);
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${nextSession.accessToken}`;
      }
      return http(originalRequest);
    } catch (refreshError) {
      authStore.getState().clearSession();
      throw refreshError;
    }
  },
);
