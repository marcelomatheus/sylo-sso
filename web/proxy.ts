import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const ACCESS_COOKIE = "sylo_access_token";
const REFRESH_COOKIE = "sylo_refresh_token";
const EXPIRES_COOKIE = "sylo_expires_at";
const ROLE_COOKIE = "sylo_user_role";

function hasUsableSession(request: NextRequest) {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  const expiresAt = request.cookies.get(EXPIRES_COOKIE)?.value;

  if (refreshToken) {
    return true;
  }
  if (!accessToken || !expiresAt) {
    return false;
  }
  return new Date(expiresAt).getTime() > Date.now();
}

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const isAdminArea = pathname === "/admin" || pathname.startsWith("/admin/");
  const isAdminLogin = pathname === "/admin/login";
  const hasSession = hasUsableSession(request);
  const role = request.cookies.get(ROLE_COOKIE)?.value;

  if (!isAdminArea) {
    return NextResponse.next();
  }

  if (isAdminLogin) {
    if (hasSession && role === "ADMIN") {
      return NextResponse.redirect(new URL("/admin", request.url));
    }
    return NextResponse.next();
  }

  if (!hasSession || role !== "ADMIN") {
    const loginUrl = new URL("/admin/login", request.url);
    loginUrl.searchParams.set("next", pathname + search);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
