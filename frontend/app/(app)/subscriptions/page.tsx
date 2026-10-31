"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, message, page, type Paginated } from "@/lib/api";
import type { Subscription } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";

const emptyPage: Paginated<Subscription> = { count: 0, next: null, previous: null, results: [] };

export default function Subscriptions() {
  const [data, setData] = useState<Paginated<Subscription>>(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const load = useCallback((path = "/subscriptions/") => { setLoading(true); list<Subscription>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false)); }, []);
  useEffect(() => { void load(); }, [load]);
  async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await api("/subscriptions/", { method: "POST", body: JSON.stringify({ customer: Number(form.get("customer")), plan: Number(form.get("plan")), start_date: form.get("start_date"), expiry_date: form.get("expiry_date"), payment_terms_days: Number(form.get("terms")), lines: [{ product: Number(form.get("product")), variant: form.get("variant") ? Number(form.get("variant")) : null, quantity: Number(form.get("quantity")), tax_rule: form.get("tax_rule") ? Number(form.get("tax_rule")) : null }] }) }); setOpen(false); void load(); } catch (err) { setError(message(err)); } }
  return <><PageHeader title="Subscriptions" description="Manage lifecycle, plan lines and billing readiness."><button className="btn" onClick={() => setOpen(true)}>Create subscription</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}{open && <form onSubmit={create} className="card mb-5 grid gap-3 p-5 md:grid-cols-3"><label><span className="label">Customer ID</span><input className="field" name="customer" type="number" min="1" required /></label><input className="field" name="plan" type="number" placeholder="Plan ID" required /><input className="field" name="product" type="number" placeholder="Product ID" required /><input className="field" name="variant" type="number" placeholder="Variant ID (optional)" /><input className="field" name="tax_rule" type="number" placeholder="Tax rule ID (optional)" /><input className="field" name="quantity" type="number" min="1" defaultValue="1" required /><input className="field" name="start_date" type="date" required /><input className="field" name="expiry_date" type="date" required /><input className="field" name="terms" type="number" defaultValue="30" min="0" required /><p className="text-xs text-slate-500 md:col-span-3">The backend does not expose a customer-directory endpoint, so subscription creation requires a customer ID.</p><div className="flex gap-2 md:col-span-3"><button className="btn">Create</button><button type="button" className="btn-secondary" onClick={() => setOpen(false)}>Cancel</button></div></form>}{loading ? <Loading /> : !data.results.length ? <Empty>No subscriptions found.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Number</th><th>Customer</th><th>Dates</th><th>Status</th><th /></tr></thead><tbody>{data.results.map((subscription) => <tr key={subscription.id}><td className="font-medium">{subscription.number}</td><td>{subscription.customer_email}</td><td>{subscription.start_date} – {subscription.expiry_date}</td><td><StatusBadge value={subscription.status} /></td><td><Link className="text-brand" href={`/subscriptions/${subscription.id}`}>View</Link></td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}
