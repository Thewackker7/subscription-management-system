"use client";
import { useEffect, useState } from "react";
import { api, money, message } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Loading } from "@/components/state";
type Summary = { active_subscriptions: number; outstanding_balance: string; paid_invoice_count: number; overdue_invoice_count: number };
export default function Portal() { const [summary, setSummary] = useState<Summary | null>(null); const [error, setError] = useState(""); useEffect(() => { api<Summary>("/portal/summary/").then(setSummary).catch((e) => setError(message(e))); }, []); return <><PageHeader title="My account" description="Your subscriptions, invoices, and payment position." />{error ? <ErrorState>{error}</ErrorState> : !summary ? <Loading /> : <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[["Active subscriptions", summary.active_subscriptions], ["Outstanding", money(summary.outstanding_balance)], ["Paid invoices", summary.paid_invoice_count], ["Overdue invoices", summary.overdue_invoice_count]].map(([title, value]) => <div className="card p-5" key={String(title)}><p className="text-sm text-slate-500">{title}</p><p className="mt-2 text-2xl font-bold">{value}</p></div>)}</div>}</>; }
