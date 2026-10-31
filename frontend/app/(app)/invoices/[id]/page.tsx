"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, message, money } from "@/lib/api";
import type { Invoice } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";

function InvoicePrintLayout({ invoice }: { invoice: Invoice }) {
  return <section className="hidden print:block" data-print-invoice>
    <header className="mb-8 border-b pb-4">
      <h1 className="text-2xl font-bold">Invoice {invoice.number}</h1>
      <p>{invoice.customer_name || invoice.customer_email}</p>
      {invoice.customer_name && <p>{invoice.customer_email}</p>}
      <p>Billing period: {invoice.billing_period_start} to {invoice.billing_period_end}</p>
      <p>Due date: {invoice.due_date}</p>
    </header>
    <table className="w-full border-collapse text-left text-sm">
      <thead><tr><th className="border-b p-2">Description</th><th className="border-b p-2">Qty</th><th className="border-b p-2">Rate</th><th className="border-b p-2">Tax</th><th className="border-b p-2">Total</th></tr></thead>
      <tbody>{invoice.lines.map((line) => <tr key={line.id}><td className="border-b p-2">{line.description}</td><td className="border-b p-2">{line.quantity}</td><td className="border-b p-2">{money(line.unit_price)}</td><td className="border-b p-2">{money(line.tax_amount)}</td><td className="border-b p-2">{money(line.total)}</td></tr>)}</tbody>
    </table>
    <dl className="ml-auto mt-6 grid w-64 grid-cols-2 gap-2"><dt>Subtotal</dt><dd>{money(invoice.subtotal)}</dd><dt>Discount</dt><dd>{money(invoice.discount_total)}</dd><dt>Tax</dt><dd>{money(invoice.tax_total)}</dd><dt className="font-bold">Total</dt><dd className="font-bold">{money(invoice.total)}</dd></dl>
  </section>;
}

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [printInvoice, setPrintInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const load = useCallback(() => api<Invoice>(`/billing/invoices/${id}/`).then(setInvoice).catch((e) => setError(message(e))), [id]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!printInvoice) return;
    const resetPrintState = () => setPrintInvoice(null);
    const frame = window.requestAnimationFrame(() => {
      try { window.print(); } finally { resetPrintState(); }
    });
    window.addEventListener("afterprint", resetPrintState, { once: true });
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("afterprint", resetPrintState);
    };
  }, [printInvoice]);

  async function act(action: "confirm" | "cancel" | "send" | "print_ready") {
    try {
      setNotice("");
      if (action === "print_ready") {
        setPrintInvoice(await api<Invoice>(`/billing/invoices/${id}/print_ready/`));
        return;
      }
      await api(`/billing/invoices/${id}/${action}/`, { method: "POST" });
      if (action === "send") setNotice("Invoice marked as sent. No email delivery was attempted.");
      void load();
    } catch (e) { setError(message(e)); }
  }

  if (!invoice) return error ? <ErrorState>{error}</ErrorState> : <Loading />;
  const printableInvoice = printInvoice ?? invoice;
  return <><InvoicePrintLayout invoice={printableInvoice} /><main className="print:hidden"><PageHeader title={invoice.number} description={`Billing period ${invoice.billing_period_start} to ${invoice.billing_period_end}`}><div className="flex gap-2"><StatusBadge value={invoice.status} /><button className="btn-secondary" onClick={() => void act("print_ready")}>Print</button>{invoice.status === "DRAFT" && <button className="btn-secondary" onClick={() => void act("confirm")}>Confirm</button>}{["DRAFT", "CONFIRMED"].includes(invoice.status) && <button className="btn-secondary" onClick={() => void act("cancel")}>Cancel</button>}{["DRAFT", "CONFIRMED"].includes(invoice.status) && <button className="btn" onClick={() => void act("send")}>Mark as sent</button>}</div></PageHeader>{error && <ErrorState>{error}</ErrorState>}{notice && <p className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">{notice}</p>}<div className="grid gap-4 md:grid-cols-4">{[["Subtotal", invoice.subtotal], ["Discount", invoice.discount_total], ["Tax", invoice.tax_total], ["Outstanding", invoice.balance]].map(([label, value]) => <div className="card p-4" key={String(label)}><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-bold">{money(String(value))}</p></div>)}</div><div className="card mt-6 table-wrap"><table className="table"><thead><tr><th>Line</th><th>Qty</th><th>Rate</th><th>Tax</th><th>Total</th></tr></thead><tbody>{invoice.lines.map((line) => <tr key={line.id}><td>{line.description}</td><td>{line.quantity}</td><td>{money(line.unit_price)}</td><td>{money(line.tax_amount)}</td><td>{money(line.total)}</td></tr>)}</tbody></table></div></main></>;
}
