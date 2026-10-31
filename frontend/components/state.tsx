export function Loading() { return <div className="card p-8 text-center text-sm text-slate-500">Loading live data…</div>; }
export function Empty({ children }: { children: React.ReactNode }) { return <div className="card p-8 text-center text-sm text-slate-500">{children}</div>; }
export function ErrorState({ children }: { children: React.ReactNode }) { return <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{children}</div>; }
