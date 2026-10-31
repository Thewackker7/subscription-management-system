"use client";

import type { User } from "./types";

const ACCESS = "sms_access";
const REFRESH = "sms_refresh";
const USER = "sms_user";

export function saveSession(access: string, refresh: string, user: User) { sessionStorage.setItem(ACCESS, access); sessionStorage.setItem(REFRESH, refresh); sessionStorage.setItem(USER, JSON.stringify(user)); }
export function sessionUser(): User | null { try { const value = sessionStorage.getItem(USER); return value ? JSON.parse(value) as User : null; } catch { return null; } }
export function accessToken() { return sessionStorage.getItem(ACCESS); }
export function refreshToken() { return sessionStorage.getItem(REFRESH); }
export function clearSession() { [ACCESS, REFRESH, USER].forEach((key) => sessionStorage.removeItem(key)); }
