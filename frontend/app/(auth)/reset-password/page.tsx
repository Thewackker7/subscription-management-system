"use client";
import { useSearchParams, useRouter } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { api, message } from "@/lib/api";
function ResetPasswordForm() { const query = useSearchParams(); const router = useRouter(); const [error, setError] = useState(""); async function submit(e: FormEvent<HTMLFormElement>) { e.preventDefault(); const f = new FormData(e.currentTarget); try { await api("/auth/password-reset/confirm/", { method: "POST", body: JSON.stringify({ uid: query.get("uid"), token: query.get("token"), password: f.get("password") }) }); router.replace("/login"); } catch (err) { setError(message(err)); } } return <><h2 className="text-3xl font-bold">Choose a new password</h2><form onSubmit={submit} className="mt-7 space-y-4">{error && <p className="text-sm text-red-700">{error}</p>}<input className="field" name="password" type="password" placeholder="New password" required /><button className="btn w-full">Reset password</button></form></>; }
export default function ResetPassword() { return <Suspense fallback={<p className="text-sm text-slate-500">Loading reset form…</p>}><ResetPasswordForm /></Suspense>; }
