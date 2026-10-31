"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, money, message } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";

export default function PortalDetail() { const { resource, id } = useParams<{ resource: string; id: string }>(); const [item, setItem] = useState<Record<string, unknown> | null>(null); const [error, setError] = useState(""); useEffect(() => { api<Record<string, unknown>>(`/portal/${resource}/${id}/`).then(setItem).catch((e) => setError(message(e))); }, [resource, id]); if (error) return <ErrorState>{error}</ErrorState>; if (!item) return <Loading />; const lines = Array.isArray(item.lines) ? item.lines as Record<string, unknown>[] : []; return <><PageHeader title={String(item.number ?? "Subscription")} description={resource === "subscriptions" ? `Status: ${item.status}` : "Invoice details"}><StatusBadge value={String(item.status ?? "ACTIVE")} /></PageHeader><div className="grid gap-4 sm:grid-cols-3">{resource === "invoices" && [["Total", item.total], ["Paid", item.amount_paid], ["Balance", item.balance]].map(([label, value]) => <div className="card p-4" key={String(label)}><p className="text-sm text-slate-500">{String(label)}</p><p className="mt-2 text-xl font-bold">{money(String(value))}</p></div>)}</div>{lines.length > 0 && <div className="card mt-6 table-wrap"><table className="table"><thead><tr><th>Description</th><th>Quantity</th><th>Total</th></tr></thead><tbody>{lines.map((line) => <tr key={String(line.id)}><td>{String(line.description)}</td><td>{String(line.quantity)}</td><td>{money(String(line.total))}</td></tr>)}</tbody></table></div>}</>; }
