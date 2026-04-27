import type { Metadata } from "next";

import { AppProvider } from "@/providers/app-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sylo SSO",
  description: "Headless identity platform for multi-tenant B2B applications.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full text-foreground">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
