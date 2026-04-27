"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useState } from "react";
import { ToastContainer } from "react-toastify";
import { authStore } from "@/features/auth/store/auth-store";

import "react-toastify/dist/ReactToastify.css";

export function AppProvider({ children }: { children: ReactNode }) {
  const session = authStore((state) => state.session);
  const hydrated = authStore((state) => state.hydrated);
  const restoreFromCookies = authStore((state) => state.restoreFromCookies);
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  useEffect(() => {
    if (hydrated && !session) {
      restoreFromCookies();
    }
  }, [hydrated, restoreFromCookies, session]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ToastContainer position="bottom-right" theme="light" />
    </QueryClientProvider>
  );
}
