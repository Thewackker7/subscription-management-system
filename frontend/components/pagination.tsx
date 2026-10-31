"use client";

import type { Paginated } from "@/lib/api";

export function Pagination<T>({ page, onNavigate }: { page: Paginated<T>; onNavigate: (url: string) => void }) {
  if (!page.next && !page.previous) return null;
  return (
    <nav className="mt-4 flex items-center justify-between gap-3" aria-label="Pagination">
      <p className="text-sm text-slate-500">{page.count} total records</p>
      <div className="flex gap-2">
        <button className="btn-secondary" disabled={!page.previous} onClick={() => page.previous && onNavigate(page.previous)}>Previous</button>
        <button className="btn-secondary" disabled={!page.next} onClick={() => page.next && onNavigate(page.next)}>Next</button>
      </div>
    </nav>
  );
}
