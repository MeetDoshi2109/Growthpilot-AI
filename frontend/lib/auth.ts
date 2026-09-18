/**
 * Auth state helpers — reads/writes the current user from localStorage
 * (JWT is in httpOnly cookie, so we only store non-sensitive profile info)
 */
"use client";

export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  merchant_id: string;
  merchant_name: string;
}

const KEY = "gp_user";

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function storeUser(user: AuthUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(KEY, JSON.stringify(user));
}

export function clearUser(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}
