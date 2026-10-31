"use client";
import { useEffect, useState } from "react";
import { api, money, message } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Loading } from "@/components/state";
type Summary = { received: string; outstanding: string; paid_invoice_count: number; overdue_invoice_count: number; discount_total: string };
export default function Reports() { const [value, setValue] = useState<Summary | null>(null); const [error, setError] = useState(""); useEffect(() => { api<Summary>("/reports/payment-summary/").then(setValue).catch((e) => setError(message(e))); }, []); return <><PageHeader title="Payment reporting" description="Operational payment metrics from the backend." />{error ? <ErrorState>{error}</ErrorState> : !value ? <Loading /> : <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">{[["Received", money(value.received)], ["Outstanding", money(value.outstanding)], ["Paid", value.paid_invoice_count], ["Overdue", value.overdue_invoice_count], ["Discounts", money(value.discount_total)]].map(([label, figure]) => <div className="card p-5" key={String(label)}><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold">{figure}</p></div>)}</div>}</>; }
