"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, message, money, page, type Paginated } from "@/lib/api";
import type { Payment } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { Pagination } from "@/components/pagination";

const emptyPage: Paginated<Payment> = { count: 0, next: null, previous: null, results: [] };

export default function Payments() {
  const [data, setData] = useState<Paginated<Payment>>(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const load = useCallback((path = "/payments/") => { setLoading(true); list<Payment>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false)); }, []);
  useEffect(() => { void load(); }, [load]);
  async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await api("/payments/", { method: "POST", body: JSON.stringify({ invoice: Number(form.get("invoice")), method: form.get("method"), amount: form.get("amount"), payment_date: form.get("payment_date"), note: form.get("note") || "", external_reference: form.get("reference") || "" }) }); setOpen(false); void load(); } catch (err) { setError(message(err)); } }
  return <><PageHeader title="Payments" description="Record partial and full invoice settlements."><button className="btn" onClick={() => setOpen(true)}>Record payment</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}{open && <form className="card mb-5 grid gap-3 p-5 md:grid-cols-3" onSubmit={create}><input className="field" type="number" name="invoice" placeholder="Invoice ID" required /><select className="field" name="method"><option>CASH</option><option>CARD</option><option>BANK_TRANSFER</option><option>UPI</option><option>OTHER</option></select><input className="field" type="number" step="0.01" name="amount" placeholder="Amount" required /><input className="field" type="date" name="payment_date" required /><input className="field" name="reference" placeholder="External reference" /><input className="field" name="note" placeholder="Note" /><div className="flex gap-2 md:col-span-3"><button className="btn">Save payment</button><button className="btn-secondary" type="button" onClick={() => setOpen(false)}>Cancel</button></div></form>}{loading ? <Loading /> : !data.results.length ? <Empty>No payments recorded.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Payment</th><th>Invoice</th><th>Method</th><th>Amount</th><th>Date</th><th>Balance after</th></tr></thead><tbody>{data.results.map((payment) => <tr key={payment.id}><td>{payment.identifier}</td><td>{payment.invoice_number}</td><td>{payment.method}</td><td>{money(payment.amount)}</td><td>{payment.payment_date}</td><td>{money(payment.balance_after)}</td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}
