"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, list, money, results, message } from "@/lib/api";
import type { Invoice } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
export default function Invoices() { const [items, setItems] = useState<Invoice[]>([]); const [error, setError] = useState(""); const load = () => list<Invoice>("/billing/invoices/").then((v) => setItems(results(v))).catch((e) => setError(message(e))); useEffect(() => { void load(); }, []); async function generate() { try { await api("/billing/generate/", { method: "POST", body: "{}" }); void load(); } catch (e) { setError(message(e)); } } return <><PageHeader title="Invoices" description="Live billing periods, tax, discounts and settlement status."><button className="btn" onClick={() => void generate()}>Generate due invoices</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}<div className="card table-wrap"><table className="table"><thead><tr><th>Invoice</th><th>Customer</th><th>Due</th><th>Total</th><th>Balance</th><th>Status</th><th /></tr></thead><tbody>{items.map((i) => <tr key={i.id}><td>{i.number}</td><td>{i.customer_email}</td><td>{i.due_date}</td><td>{money(i.total)}</td><td>{money(i.balance)}</td><td><StatusBadge value={i.status} /></td><td><Link className="text-brand" href={`/invoices/${i.id}`}>View</Link></td></tr>)}</tbody></table></div>{!items.length && <Empty>No invoices found.</Empty>}</>; }
