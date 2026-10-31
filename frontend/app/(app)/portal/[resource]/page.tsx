"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, message, money, page, type Paginated } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";

const emptyPage: Paginated<Record<string, unknown>> = { count: 0, next: null, previous: null, results: [] };

export default function PortalResource() {
  const { resource } = useParams<{ resource: string }>();
  const [data, setData] = useState<Paginated<Record<string, unknown>>>(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const endpoint = `/portal/${resource}/`;
  const load = useCallback((path = endpoint) => {
    if (resource === "profile") return;
    setLoading(true);
    list<Record<string, unknown>>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false));
  }, [endpoint, resource]);
  useEffect(() => {
    if (resource === "profile") { setLoading(true); api<Record<string, unknown>>(endpoint).then(setProfile).catch((e) => setError(message(e))).finally(() => setLoading(false)); }
    else void load();
  }, [endpoint, load, resource]);
  async function update(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { setProfile(await api<Record<string, unknown>>(endpoint, { method: "PATCH", body: JSON.stringify({ first_name: form.get("first_name") || "", last_name: form.get("last_name") || "" }) })); } catch (err) { setError(message(err)); } }
  if (error) return <ErrorState>{error}</ErrorState>;
  if (resource === "profile") return loading || !profile ? <Loading /> : <><PageHeader title="Profile" description="Manage your customer profile." /><form onSubmit={update} className="card max-w-xl space-y-4 p-5"><input className="field" value={String(profile.email ?? "")} disabled /><input className="field" name="first_name" defaultValue={String(profile.first_name ?? "")} placeholder="First name" /><input className="field" name="last_name" defaultValue={String(profile.last_name ?? "")} placeholder="Last name" /><button className="btn">Save profile</button></form></>;
  const title = resource === "subscriptions" ? "My subscriptions" : resource === "invoices" ? "My invoices" : "Payment history";
  return <><PageHeader title={title} description="Only records belonging to this account are returned by the API." />{loading ? <Loading /> : !data.results.length ? <Empty>No records found.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr>{resource === "subscriptions" ? <><th>Subscription</th><th>Status</th><th>Next billing</th><th /></> : resource === "invoices" ? <><th>Invoice</th><th>Status</th><th>Total</th><th>Balance</th></> : <><th>Payment</th><th>Invoice</th><th>Amount</th><th>Date</th></>}</tr></thead><tbody>{data.results.map((item) => resource === "subscriptions" ? <tr key={String(item.id)}><td>{String(item.number)}</td><td><StatusBadge value={String(item.status)} /></td><td>{String(item.next_billing_date ?? "—")}</td><td><Link className="text-brand" href={`/portal/subscriptions/${item.id}`}>View</Link></td></tr> : resource === "invoices" ? <tr key={String(item.id)}><td>{String(item.number)}</td><td><StatusBadge value={String(item.status)} /></td><td>{money(String(item.total))}</td><td>{money(String(item.balance))}</td></tr> : <tr key={String(item.id)}><td>{String(item.identifier)}</td><td>{String(item.invoice_number)}</td><td>{money(String(item.amount))}</td><td>{String(item.payment_date)}</td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}
