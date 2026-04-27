"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { clearSessionCookies, readSessionCookies, writeSessionCookies, type SessionState } from "@/features/auth/lib/session";

type AuthState = {
  session: SessionState | null;
  hydrated: boolean;
  setSession: (session: SessionState) => void;
  clearSession: () => void;
  restoreFromCookies: () => void;
  markHydrated: () => void;
};

export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      session: null,
      hydrated: false,
      setSession: (session) => {
        writeSessionCookies(session);
        set({ session });
      },
      clearSession: () => {
        clearSessionCookies();
        set({ session: null });
      },
      restoreFromCookies: () => {
        const session = readSessionCookies();
        if (session) {
          set({ session });
        }
      },
      markHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "sylo-auth",
      partialize: (state) => ({ session: state.session }),
      onRehydrateStorage: () => (state) => {
        if (state?.session) {
          writeSessionCookies(state.session);
        }
        state?.markHydrated();
      },
    },
  ),
);
