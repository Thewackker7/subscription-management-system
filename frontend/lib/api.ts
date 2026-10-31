"use client";

import { accessToken, clearSession, refreshToken, saveSession, sessionUser } from "./auth";
import type { ApiError, Page, User } from "./types";

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");
export class RequestError extends Error { constructor(public status: number, public payload: ApiError) { super(String(payload.detail ?? "Request failed")); } }

function apiUrl(path: string) {
  if (!/^https?:\/\//i.test(path)) return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const requested = new URL(path);
  if (requested.origin !== new URL(baseUrl).origin) {
    throw new RequestError(400, { detail: "Unexpected pagination URL origin." });
  }
  return requested.toString();
}

async function refreshAccess(): Promise<string | null> {
  const refresh = refreshToken();
  if (!refresh) return null;
  const response = await fetch(`${baseUrl}/auth/token/refresh/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh }) });
  if (!response.ok) { clearSession(); return null; }
  const data = await response.json() as { access: string };
  const user = sessionUser();
  if (user) saveSession(data.access, refresh, user);
  return data.access;
}

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const url = apiUrl(path);
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = accessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401 && retry && await refreshAccess()) return api<T>(path, options, false);
  if (!response.ok) { let payload: ApiError = {}; try { payload = await response.json() as ApiError; } catch { payload = { detail: response.statusText }; } throw new RequestError(response.status, payload); }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const data = await api<{ access: string; refresh: string; user: User }>("/auth/login/", { method: "POST", body: JSON.stringify({ email, password }) });
  saveSession(data.access, data.refresh, data.user); return data.user;
}
export function list<T>(path: string) { return api<Page<T> | T[]>(path); }
export type Paginated<T> = Required<Pick<Page<T>, "count" | "next" | "previous" | "results">>;
export function page<T>(value: Page<T> | T[]): Paginated<T> {
  return Array.isArray(value)
    ? { count: value.length, next: null, previous: null, results: value }
    : { count: value.count ?? value.results?.length ?? 0, next: value.next ?? null, previous: value.previous ?? null, results: value.results ?? [] };
}
export async function listAll<T>(path: string): Promise<T[]> {
  const first = page(await list<T>(path));
  const items = [...first.results];
  let next = first.next;
  while (next) {
    const response = page(await list<T>(next));
    items.push(...response.results);
    next = response.next;
  }
  return items;
}
export function money(value?: string | number) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Number(value ?? 0)); }
export function message(error: unknown) { if (error instanceof RequestError) return typeof error.payload.detail === "string" ? error.payload.detail : Object.values(error.payload).flat().join(" "); return "Unable to reach the API. Check NEXT_PUBLIC_API_BASE_URL and the backend server."; }
