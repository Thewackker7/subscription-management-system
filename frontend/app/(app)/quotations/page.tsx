"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, message, page, type Paginated } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Empty, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";

type Quote = { id: number; number: string; customer_email: string; valid_until: string; status: string; converted_subscription?: number };
const emptyPage: Paginated<Quote> = { count: 0, next: null, previous: null, results: [] };

export default function Quotations() {
  const [data, setData] = useState<Paginated<Quote>>(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [template, setTemplate] = useState(false);
  const load = useCallback((path = "/subscriptions/quotations/") => { setLoading(true); list<Quote>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false)); }, []);
  useEffect(() => { void load(); }, [load]);
  async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await api("/subscriptions/quotations/", { method: "POST", body: JSON.stringify({ customer: Number(form.get("customer")), template: Number(form.get("template")) }) }); setTemplate(false); void load(); } catch (err) { setError(message(err)); } }
  async function convert(id: number) { const start = prompt("Start date (YYYY-MM-DD)"); const expiry = prompt("Expiry date (YYYY-MM-DD)"); if (!start || !expiry) return; try { await api(`/subscriptions/quotations/${id}/convert/`, { method: "POST", body: JSON.stringify({ start_date: start, expiry_date: expiry, payment_terms_days: 30 }) }); void load(); } catch (error) { setError(message(error)); } }
  return <><PageHeader title="Quotations" description="Create from reusable templates and convert only valid quotes."><button className="btn" onClick={() => setTemplate(true)}>New from template</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}{template && <form className="card mb-5 flex flex-wrap gap-3 p-4" onSubmit={create}><input className="field max-w-xs" name="customer" type="number" placeholder="Customer ID" required /><input className="field max-w-xs" name="template" type="number" placeholder="Template ID" required /><button className="btn">Create</button><button className="btn-secondary" type="button" onClick={() => setTemplate(false)}>Cancel</button></form>}{loading ? <Loading /> : !data.results.length ? <Empty>No quotations yet. The current API exposes templates, but template listing/creation is available at `/subscriptions/quotation-templates/`.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Number</th><th>Customer</th><th>Valid until</th><th>Status</th><th /></tr></thead><tbody>{data.results.map((quote) => <tr key={quote.id}><td>{quote.number}</td><td>{quote.customer_email}</td><td>{quote.valid_until}</td><td><StatusBadge value={quote.status} /></td><td>{!quote.converted_subscription && <button className="text-brand" onClick={() => void convert(quote.id)}>Convert</button>}</td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}
