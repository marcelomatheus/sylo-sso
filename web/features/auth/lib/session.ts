"use client";

export type SessionUser = {
  id: string;
  tenantId: string;
  email: string;
  name: string;
  role: string;
} | null;

export type SessionState = {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
  user: SessionUser;
};

const COOKIE_PREFIX = "sylo";
const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

function setCookie(name: string, value: string, maxAge = COOKIE_MAX_AGE_SECONDS) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
}

function clearCookie(name: string) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const target = `${name}=`;
  const found = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(target));
  if (!found) {
    return null;
  }
  return decodeURIComponent(found.slice(target.length));
}

export function isSessionExpired(expiresAt: string | null | undefined) {
  if (!expiresAt) {
    return true;
  }
  return new Date(expiresAt).getTime() <= Date.now();
}

export function writeSessionCookies(session: SessionState) {
  setCookie(`${COOKIE_PREFIX}_access_token`, session.accessToken);
  setCookie(`${COOKIE_PREFIX}_refresh_token`, session.refreshToken);
  setCookie(`${COOKIE_PREFIX}_expires_at`, session.expiresAt);
  setCookie(`${COOKIE_PREFIX}_user_role`, session.user?.role ?? "");
  setCookie(`${COOKIE_PREFIX}_user`, JSON.stringify(session.user));
}

export function clearSessionCookies() {
  clearCookie(`${COOKIE_PREFIX}_access_token`);
  clearCookie(`${COOKIE_PREFIX}_refresh_token`);
  clearCookie(`${COOKIE_PREFIX}_expires_at`);
  clearCookie(`${COOKIE_PREFIX}_user_role`);
  clearCookie(`${COOKIE_PREFIX}_user`);
}

export function readSessionCookies(): SessionState | null {
  const accessToken = readCookie(`${COOKIE_PREFIX}_access_token`);
  const refreshToken = readCookie(`${COOKIE_PREFIX}_refresh_token`);
  const expiresAt = readCookie(`${COOKIE_PREFIX}_expires_at`);
  const userRaw = readCookie(`${COOKIE_PREFIX}_user`);
  if (!accessToken || !refreshToken || !expiresAt || !userRaw) {
    return null;
  }
  try {
    const user = JSON.parse(userRaw) as SessionUser;
    return {
      accessToken,
      refreshToken,
      expiresAt,
      user,
    };
  } catch {
    return null;
  }
}
