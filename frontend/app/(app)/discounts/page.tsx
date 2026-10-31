"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, list, listAll, message, page, type Paginated } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Empty, ErrorState, Loading } from "@/components/state";
import { Pagination } from "@/components/pagination";

type Product = { id: number; name: string; is_active: boolean };
type DiscountRule = { id: number; name: string; discount_type: "FIXED" | "PERCENTAGE"; value: string; scope: "SUBSCRIPTION" | "PRODUCT"; products: number[]; minimum_purchase_amount: string; minimum_quantity: number; starts_on: string; ends_on: string | null; maximum_uses: number | null; is_active: boolean };
const emptyPage: Paginated<DiscountRule> = { count: 0, next: null, previous: null, results: [] };

export default function Discounts() {
  const [data, setData] = useState<Paginated<DiscountRule>>(emptyPage);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DiscountRule | null>(null);
  const [discountType, setDiscountType] = useState<DiscountRule["discount_type"]>("PERCENTAGE");
  const [scope, setScope] = useState<DiscountRule["scope"]>("SUBSCRIPTION");
  const [selectedProducts, setSelectedProducts] = useState<number[]>([]);
  const load = useCallback((path = "/discounts/") => { setLoading(true); list<DiscountRule>(path).then((value) => setData(page(value))).catch((e) => setError(message(e))).finally(() => setLoading(false)); }, []);
  useEffect(() => { void load(); listAll<Product>("/catalog/products/").then(setProducts).catch((e) => setError(message(e))); }, [load]);
  function openForm(rule: DiscountRule | null) { setEditing(rule); setDiscountType(rule?.discount_type ?? "PERCENTAGE"); setScope(rule?.scope ?? "SUBSCRIPTION"); setSelectedProducts(rule?.products ?? []); setFormOpen(true); }
  function closeForm() { setFormOpen(false); setEditing(null); }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (scope === "PRODUCT" && !selectedProducts.length) { setError("Select at least one product for a product-scoped discount."); return; }
    const payload = {
      name: String(form.get("name")), discount_type: String(form.get("discount_type")), value: String(form.get("value")), scope, products: scope === "PRODUCT" ? selectedProducts : [],
      minimum_purchase_amount: String(form.get("minimum_purchase_amount") || "0"), minimum_quantity: Number(form.get("minimum_quantity") || 0), starts_on: String(form.get("starts_on")),
      ends_on: form.get("ends_on") || null, maximum_uses: form.get("maximum_uses") || null, is_active: form.get("is_active") === "on",
    };
    try { await api(`/discounts/${editing ? `${editing.id}/` : ""}`, { method: editing ? "PATCH" : "POST", body: JSON.stringify(payload) }); closeForm(); void load(); } catch (err) { setError(message(err)); }
  }
  async function remove(id: number) { if (!confirm("Delete this discount rule?")) return; try { await api(`/discounts/${id}/`, { method: "DELETE" }); void load(); } catch (err) { setError(message(err)); } }
  return <><PageHeader title="Discount rules" description="Admin-only rules automatically applied to eligible new invoices."><button className="btn" onClick={() => openForm(null)}>New discount</button></PageHeader>{error && <ErrorState>{error}</ErrorState>}<DiscountForm open={formOpen} rule={editing} discountType={discountType} scope={scope} selectedProducts={selectedProducts} products={products} onClose={closeForm} onDiscountTypeChange={setDiscountType} onScopeChange={setScope} onProductsChange={setSelectedProducts} onSubmit={submit} />{loading ? <Loading /> : !data.results.length ? <Empty>No discount rules found.</Empty> : <><div className="card table-wrap"><table className="table"><thead><tr><th>Name</th><th>Type</th><th>Scope</th><th>Products</th><th>Value</th><th /></tr></thead><tbody>{data.results.map((rule) => <tr key={rule.id}><td>{rule.name}</td><td>{rule.discount_type}</td><td>{rule.scope}</td><td>{rule.products.map((id) => products.find((product) => product.id === id)?.name ?? `#${id}`).join(", ") || "—"}</td><td>{rule.value}</td><td><div className="flex gap-2"><button className="text-brand" onClick={() => openForm(rule)}>Edit</button><button className="text-red-600" onClick={() => void remove(rule.id)}>Delete</button></div></td></tr>)}</tbody></table></div><Pagination page={data} onNavigate={load} /></>}</>;
}

function DiscountForm({ open, rule, discountType, scope, selectedProducts, products, onClose, onDiscountTypeChange, onScopeChange, onProductsChange, onSubmit }: { open: boolean; rule: DiscountRule | null; discountType: DiscountRule["discount_type"]; scope: DiscountRule["scope"]; selectedProducts: number[]; products: Product[]; onClose: () => void; onDiscountTypeChange: (value: DiscountRule["discount_type"]) => void; onScopeChange: (value: DiscountRule["scope"]) => void; onProductsChange: (value: number[]) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  if (!open) return null;
  return <form onSubmit={onSubmit} className="card mb-6 grid gap-4 p-5 md:grid-cols-2"><label><span className="label">Name</span><input className="field" name="name" defaultValue={rule?.name ?? ""} required /></label><label><span className="label">Type</span><select className="field" name="discount_type" value={discountType} onChange={(event) => onDiscountTypeChange(event.target.value as DiscountRule["discount_type"])} required><option value="FIXED">Fixed amount</option><option value="PERCENTAGE">Percentage</option></select></label><label><span className="label">Value</span><input className="field" name="value" type="number" step="0.01" min="0.01" max={discountType === "PERCENTAGE" ? 100 : undefined} defaultValue={rule?.value ?? ""} required /></label><label><span className="label">Scope</span><select className="field" name="scope" value={scope} onChange={(event) => onScopeChange(event.target.value as DiscountRule["scope"])}><option value="SUBSCRIPTION">Subscription-wide</option><option value="PRODUCT">Product-specific</option></select></label>{scope === "PRODUCT" && <label className="md:col-span-2"><span className="label">Eligible products</span><select className="field min-h-32" multiple value={selectedProducts.map(String)} onChange={(event) => onProductsChange(Array.from(event.currentTarget.selectedOptions, (option) => Number(option.value)))} required>{products.map((product) => <option key={product.id} value={product.id}>{product.name}{product.is_active ? "" : " (inactive)"}</option>)}</select><span className="mt-1 block text-xs text-slate-500">Hold Ctrl or ⌘ to select multiple products.</span></label>}<label><span className="label">Minimum purchase</span><input className="field" name="minimum_purchase_amount" type="number" step="0.01" min="0" defaultValue={rule?.minimum_purchase_amount ?? "0"} /></label><label><span className="label">Minimum quantity</span><input className="field" name="minimum_quantity" type="number" min="0" defaultValue={rule?.minimum_quantity ?? 0} /></label><label><span className="label">Starts on</span><input className="field" name="starts_on" type="date" defaultValue={rule?.starts_on ?? ""} required /></label><label><span className="label">Ends on</span><input className="field" name="ends_on" type="date" defaultValue={rule?.ends_on ?? ""} /></label><label><span className="label">Maximum uses</span><input className="field" name="maximum_uses" type="number" min="1" defaultValue={rule?.maximum_uses ?? ""} /></label><label className="flex items-center gap-2 pt-7"><input name="is_active" type="checkbox" defaultChecked={rule?.is_active ?? true} />Active</label><div className="flex gap-2 md:col-span-2"><button className="btn">Save discount</button><button className="btn-secondary" type="button" onClick={onClose}>Cancel</button></div></form>;
}
