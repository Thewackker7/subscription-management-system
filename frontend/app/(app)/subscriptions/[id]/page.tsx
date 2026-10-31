"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, message, money } from "@/lib/api";
import type { Subscription } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ErrorState, Loading } from "@/components/state";
import { StatusBadge } from "@/components/status-badge";

const transitions: Record<string, string[]> = {
  DRAFT: ["QUOTATION", "CLOSED"],
  QUOTATION: ["CONFIRMED", "CLOSED"],
  CONFIRMED: ["ACTIVE", "CLOSED"],
  ACTIVE: ["CLOSED"],
  CLOSED: [],
};

export default function SubscriptionDetail() {
  const { id } = useParams<{ id: string }>();
  const [item, setItem] = useState<Subscription | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(() => api<Subscription>(`/subscriptions/${id}/`).then(setItem).catch((error) => setError(message(error))), [id]);
  useEffect(() => { void load(); }, [load]);
  async function act(path: string, body?: object) { try { await api(`/subscriptions/${id}/${path}/`, { method: "POST", body: body ? JSON.stringify(body) : undefined }); void load(); } catch (error) { setError(message(error)); } }
  if (!item) return error ? <ErrorState>{error}</ErrorState> : <Loading />;
  const allowedTransitions = transitions[item.status] ?? [];
  return <><PageHeader title={item.number} description={`${item.customer_email} · ${item.start_date} to ${item.expiry_date}`}><div className="flex flex-wrap gap-2"><StatusBadge value={item.status} />{allowedTransitions.map((status) => <button key={status} className="btn-secondary" onClick={() => void act("transition", { status })}>{status === "CLOSED" ? "Close" : `Mark ${status}`}</button>)}{item.status === "ACTIVE" && <button className="btn-secondary" onClick={() => void act(item.is_paused ? "resume" : "pause")}>{item.is_paused ? "Resume" : "Pause"}</button>}{item.status === "CLOSED" && <button className="btn-secondary" onClick={() => { const next = prompt("New expiry date (YYYY-MM-DD)"); if (next) void act("renew", { expiry_date: next }); }}>Renew</button>}</div></PageHeader>{error && <ErrorState>{error}</ErrorState>}<div className="card table-wrap"><table className="table"><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Total</th></tr></thead><tbody>{item.lines.map((line) => <tr key={line.id}><td>{line.description}</td><td>{line.quantity}</td><td>{money(line.unit_price)}</td><td>{money(line.total)}</td></tr>)}</tbody></table></div></>;
}
