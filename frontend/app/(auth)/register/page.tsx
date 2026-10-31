"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { api, message } from "@/lib/api";

export default function RegisterPage() { const [state, setState] = useState<{ error?: string; done?: boolean }>({});
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setState({}); const f = new FormData(event.currentTarget); try { await api("/auth/register/", { method: "POST", body: JSON.stringify({ email: f.get("email"), first_name: f.get("first_name"), last_name: f.get("last_name"), password: f.get("password") }) }); setState({ done: true }); } catch (e) { setState({ error: message(e) }); } }
  return <><h2 className="text-3xl font-bold">Create customer account</h2><p className="mt-2 text-slate-500">Passwords need 9+ characters, uppercase, lowercase and a special character.</p>{state.done ? <p className="mt-6 rounded-lg bg-emerald-50 p-4 text-sm text-emerald-700">Account created. <Link className="font-semibold underline" href="/login">Sign in</Link>.</p> : <form onSubmit={submit} className="mt-7 space-y-4">{state.error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{state.error}</p>}<input className="field" name="first_name" placeholder="First name" /><input className="field" name="last_name" placeholder="Last name" /><input className="field" type="email" name="email" placeholder="Email" required /><input className="field" type="password" name="password" placeholder="Password" required /><button className="btn w-full">Create account</button></form>}</>; }
