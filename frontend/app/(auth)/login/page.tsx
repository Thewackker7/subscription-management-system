"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login, message } from "@/lib/api";

export default function LoginPage() { const router = useRouter(); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setBusy(true); setError(""); const form = new FormData(event.currentTarget); try { const user = await login(String(form.get("email")), String(form.get("password"))); router.replace(user.role === "CUSTOMER" ? "/portal" : "/dashboard"); } catch (err) { setError(message(err)); } finally { setBusy(false); } }
  return <><h2 className="text-3xl font-bold">Welcome back</h2><p className="mt-2 text-slate-500">Sign in to manage Brightloop.</p>{error && <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<form onSubmit={submit} className="mt-7 space-y-4"><label className="block"><span className="label">Email</span><input className="field" type="email" name="email" required /></label><label className="block"><span className="label">Password</span><input className="field" type="password" name="password" required /></label><div className="flex justify-end"><Link className="text-sm font-medium text-brand" href="/forgot-password">Forgot password?</Link></div><button className="btn w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form><p className="mt-6 text-sm text-slate-600">New customer? <Link className="font-semibold text-brand" href="/register">Create an account</Link></p></>; }
