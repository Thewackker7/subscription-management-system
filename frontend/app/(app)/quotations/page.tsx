"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, listAll, message, page, type Paginated } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Empty, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";
import { Pagination } from "@/components/pagination";

type Quote = { id: number; number: string; customer_email: string; valid_until: string; status: string; converted_subscription?: number };
type TemplateLine = { id?: number; product: number; variant: number | null; quantity: number; tax_rule: number | null };
type Template = { id: number; name: string; plan: number; validity_days: number; is_active: boolean; lines: TemplateLine[] };
const emptyPage: Paginated<Quote> = { count: 0, next: null, previous: null, results: [] };

export default function Quotations() {
  const [data, setData] = useState<Paginated<Quote>>(emptyPage);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quoteFormOpen, setQuoteFormOpen] = useState(false);
  const [templateFormOpen, setTemplateFormOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const load = useCallback((path = "/subscriptions/quotations/") => { setLoading(true); list<Quote>(path).then((value) => setData(page(value))).catch((error) => setError(message(error))).finally(() => setLoading(false)); }, []);
  const loadTemplates = useCallback(() => { listAll<Template>("/subscriptions/quotation-templates/").then(setTemplates).catch((error) => setError(message(error))); }, []);
  useEffect(() => { void load(); loadTemplates(); }, [load, loadTemplates]);

  async function createQuotation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api("/subscriptions/quotations/", { method: "POST", body: JSON.stringify({ customer: Number(form.get("customer")), template: Number(form.get("template")) }) });
      setQuoteFormOpen(false);
      void load();
    } catch (error) { setError(message(error)); }
  }
  async function saveTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values = { name: String(form.get("name")), plan: Number(form.get("plan")), validity_days: Number(form.get("validity_days")), is_active: form.get("is_active") === "on" };
    const line: TemplateLine = { product: Number(form.get("product")), variant: form.get("variant") ? Number(form.get("variant")) : null, quantity: Number(form.get("quantity")), tax_rule: form.get("tax_rule") ? Number(form.get("tax_rule")) : null };
    const payload = editingTemplate ? { name: values.name, validity_days: values.validity_days, is_active: values.is_active } : { ...values, lines: [line] };
    try {
      await api(`/subscriptions/quotation-templates/${editingTemplate ? `${editingTemplate.id}/` : ""}`, { method: editingTemplate ? "PATCH" : "POST", body: JSON.stringify(payload) });
      setTemplateFormOpen(false);
      setEditingTemplate(null);
      loadTemplates();
    } catch (error) { setError(message(error)); }
  }
  async function removeTemplate(id: number) { if (!confirm("Delete this quotation template?")) return; try { await api(`/subscriptions/quotation-templates/${id}/`, { method: "DELETE" }); loadTemplates(); } catch (error) { setError(message(error)); } }
  async function convert(id: number) { const start = prompt("Start date (YYYY-MM-DD)"); const expiry = prompt("Expiry date (YYYY-MM-DD)"); if (!start || !expiry) return; try { await api(`/subscriptions/quotations/${id}/convert/`, { method: "POST", body: JSON.stringify({ start_date: start, expiry_date: expiry, payment_terms_days: 30 }) }); void load(); } catch (error) { setError(message(error)); } }
  function editTemplate(template: Template | null) { setEditingTemplate(template); setTemplateFormOpen(true); }

  return <><PageHeader title="Quotations" description="Create from reusable templates and convert only valid quotes."><div className="flex gap-2"><button className="btn-secondary" onClick={() => editTemplate(null)}>Manage templates</button><button className="btn" onClick={() => setQuoteFormOpen(true)}>New from template</button></div></PageHeader>{error && <ErrorState>{error}</ErrorState>}{quoteFormOpen && <form className="card mb-5 grid gap-3 p-4 md:grid-cols-3" onSubmit={createQuotation}><label><span className="label">Customer ID</span><input className="field" name="customer" type="number" min="1" required /></label><label className="md:col-span-2"><span className="label">Quotation template</span><select className="field" name="template" required><option value="">Select an active template…</option>{templates.filter((template) => template.is_active).map((template) => <option key={template.id} value={template.id}>{template.name} · {template.validity_days} days</option>)}</select></label><p className="text-xs text-slate-500 md:col-span-3">The backend currently has no customer-directory endpoint, so a customer ID is required.</p><div className="flex gap-2 md:col-span-3"><button className="btn">Create quotation</button><button className="btn-secondary" type="button" onClick={() => setQuoteFormOpen(false)}>Cancel</button></div></form>}{templateFormOpen && <TemplateForm template={editingTemplate} onClose={() => { setTemplateFormOpen(false); setEditingTemplate(null); }} onSubmit={saveTemplate} />}{loading ? <Loading /> : !data.results.length ? <Empty>No quotations found.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Number</th><th>Customer</th><th>Valid until</th><th>Status</th><th /></tr></thead><tbody>{data.results.map((quote) => <tr key={quote.id}><td>{quote.number}</td><td>{quote.customer_email}</td><td>{quote.valid_until}</td><td><StatusBadge value={quote.status} /></td><td>{!quote.converted_subscription && <button className="text-brand" onClick={() => void convert(quote.id)}>Convert</button>}</td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}<section className="mt-8"><h2 className="mb-3 text-lg font-semibold">Quotation templates</h2>{!templates.length ? <Empty>No templates yet. Create one to start a quotation.</Empty> : <div className="card table-wrap"><table className="table"><thead><tr><th>Name</th><th>Plan ID</th><th>Validity</th><th>Lines</th><th>Status</th><th /></tr></thead><tbody>{templates.map((template) => <tr key={template.id}><td>{template.name}</td><td>{template.plan}</td><td>{template.validity_days} days</td><td>{template.lines.length}</td><td><StatusBadge value={template.is_active ? "ACTIVE" : "INACTIVE"} /></td><td><div className="flex gap-2"><button className="text-brand" onClick={() => editTemplate(template)}>Edit</button><button className="text-red-600" onClick={() => void removeTemplate(template.id)}>Delete</button></div></td></tr>)}</tbody></table></div>}</section></>;
}

function TemplateForm({ template, onClose, onSubmit }: { template: Template | null; onClose: () => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  const line = template?.lines[0];
  return <form className="card mb-6 grid gap-3 p-5 md:grid-cols-3" onSubmit={onSubmit}><h2 className="text-lg font-semibold md:col-span-3">{template ? "Edit quotation template" : "New quotation template"}</h2><label><span className="label">Name</span><input className="field" name="name" defaultValue={template?.name ?? ""} required /></label><label><span className="label">Plan ID</span><input className="field" name="plan" type="number" min="1" defaultValue={template?.plan ?? ""} readOnly={Boolean(template)} required /></label><label><span className="label">Validity days</span><input className="field" name="validity_days" type="number" min="1" defaultValue={template?.validity_days ?? 30} required /></label>{template ? <p className="text-sm text-slate-500 md:col-span-3">Plan and {template.lines.length} existing line(s) are retained because the backend does not support nested line updates.</p> : <><label><span className="label">Product ID</span><input className="field" name="product" type="number" min="1" defaultValue={line?.product ?? ""} required /></label><label><span className="label">Variant ID (optional)</span><input className="field" name="variant" type="number" min="1" defaultValue={line?.variant ?? ""} /></label><label><span className="label">Quantity</span><input className="field" name="quantity" type="number" min="1" defaultValue={line?.quantity ?? 1} required /></label><label><span className="label">Tax rule ID (optional)</span><input className="field" name="tax_rule" type="number" min="1" defaultValue={line?.tax_rule ?? ""} /></label></>}<label className="flex items-center gap-2 pt-7"><input name="is_active" type="checkbox" defaultChecked={template?.is_active ?? true} />Active</label><div className="flex gap-2 md:col-span-3"><button className="btn">Save template</button><button className="btn-secondary" type="button" onClick={onClose}>Cancel</button></div></form>;
}
