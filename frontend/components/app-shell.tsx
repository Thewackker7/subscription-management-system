"use client";

import { BarChart3, Boxes, CreditCard, FileText, LayoutDashboard, LogOut, ReceiptIndianRupee, Settings2, Tag, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearSession, sessionUser } from "@/lib/auth";
import type { Role, User } from "@/lib/types";

const adminLinks = [
  ["Dashboard", "/dashboard", LayoutDashboard], ["Products", "/catalog/products", Boxes], ["Variants", "/catalog/variants", Boxes], ["Plans", "/catalog/plans", Settings2], ["Taxes", "/catalog/taxes", ReceiptIndianRupee], ["Discounts", "/discounts", Tag], ["Subscriptions", "/subscriptions", FileText], ["Quotations", "/quotations", FileText], ["Invoices", "/invoices", ReceiptIndianRupee], ["Payments", "/payments", CreditCard], ["Reports", "/reports", BarChart3]
] as const;
const customerLinks = [["My dashboard", "/portal", LayoutDashboard], ["My subscriptions", "/portal/subscriptions", FileText], ["My invoices", "/portal/invoices", ReceiptIndianRupee], ["Payment history", "/portal/payments", CreditCard], ["Profile", "/portal/profile", UserRound]] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter(); const pathname = usePathname(); const [user, setUser] = useState<User | null>(null);
  useEffect(() => { const current = sessionUser(); if (!current) router.replace("/login"); else setUser(current); }, [router]);
  if (!user) return <main className="grid min-h-screen place-items-center text-sm text-slate-500">Checking your session…</main>;
  const links = user.role === "CUSTOMER" ? customerLinks : adminLinks;
  return <div className="min-h-screen md:flex"><aside className="border-b border-slate-200 bg-ink px-4 py-5 text-slate-200 md:min-h-screen md:w-64 md:border-b-0">
    <Link href={user.role === "CUSTOMER" ? "/portal" : "/dashboard"} className="mb-7 flex items-center gap-3 px-2 text-lg font-bold text-white"><span className="grid h-8 w-8 place-items-center rounded-lg bg-brand">B</span>Brightloop</Link>
    <p className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">{user.role === "CUSTOMER" ? "Customer portal" : user.role === "ADMIN" ? "Administration" : "Operations"}</p>
    <nav className="flex gap-1 overflow-x-auto md:flex-col">{links.filter(([name]) => user.role === "ADMIN" || !["Products", "Variants", "Plans", "Taxes", "Discounts", "Reports"].includes(name)).map(([name, href, Icon]) => <Link key={href} href={href} className={`flex shrink-0 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${pathname === href ? "bg-white/15 text-white" : "hover:bg-white/10"}`}><Icon size={17} />{name}</Link>)}</nav>
    <div className="mt-6 border-t border-white/10 pt-4 md:mt-auto"><p className="truncate px-2 text-sm text-white">{user.email}</p><button className="mt-2 flex items-center gap-2 px-2 py-2 text-sm hover:text-white" onClick={() => { clearSession(); router.replace("/login"); }}><LogOut size={16} />Log out</button></div>
  </aside><main className="min-w-0 flex-1 p-4 sm:p-7">{children}</main></div>;
}
