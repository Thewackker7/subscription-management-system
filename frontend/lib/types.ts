export type Role = "ADMIN" | "STAFF" | "CUSTOMER";
export type User = { id: number; email: string; role: Role };
export type Page<T> = { count?: number; next?: string | null; previous?: string | null; results?: T[] };
export type ApiError = { detail?: string; [key: string]: unknown };
export type Invoice = { id: number; number: string; customer_email: string; customer_name?: string; subscription: number; billing_period_start: string; billing_period_end: string; due_date: string; status: string; subtotal: string; tax_total: string; discount_total: string; total: string; amount_paid: string; balance: string; is_overdue: boolean; lines: InvoiceLine[]; discount_applications: { id: number; rule_name: string; amount: string }[] };
export type InvoiceLine = { id: number; description: string; quantity: number; unit_price: string; tax_amount: string; total: string };
export type Subscription = { id: number; number: string; customer: number; customer_email: string; plan: number; start_date: string; expiry_date: string; payment_terms_days: number; status: string; next_billing_date: string | null; is_paused: boolean; lines: { id: number; description: string; quantity: number; unit_price: string; total: string }[] };
export type Payment = { id: number; identifier: string; invoice: number; invoice_number: string; method: string; amount: string; payment_date: string; note: string; external_reference?: string; balance_after: string };
