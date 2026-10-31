"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, list, message, page, type Paginated } from "@/lib/api";
import type { Invoice } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";
import { money } from "@/lib/api";

const emptyPage: Paginated<Invoice> = { count: 0, next: null, previous: null, results: [] };

export default function Invoices() {
  const [data, setData] = useState<Paginated<Invoice>>(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback((path = "/billing/invoices/") => { setLoading(true); list<Invoice>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false)); }, []);
  useEffect(() => { void load(); }, [load]);
  async function generate() { try { await api("/billing/generate/", { method: "POST", body: "{}" }); void load(); } catch (e) { setError(message(e)); } }
  return <><PageHeader title="Invoices" description="Live billing periods, tax, discounts and settlement status."><button className="btn" onClick={() => void generate()}>Generate due invoices</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}{loading ? <Loading /> : !data.results.length ? <Empty>No invoices found.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Invoice</th><th>Customer</th><th>Due</th><th>Total</th><th>Balance</th><th>Status</th><th /></tr></thead><tbody>{data.results.map((invoice) => <tr key={invoice.id}><td>{invoice.number}</td><td>{invoice.customer_email}</td><td>{invoice.due_date}</td><td>{money(invoice.total)}</td><td>{money(invoice.balance)}</td><td><StatusBadge value={invoice.status} /></td><td><Link className="text-brand" href={`/invoices/${invoice.id}`}>View</Link></td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}
