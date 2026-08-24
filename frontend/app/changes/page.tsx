"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { SeverityEmoji } from "@/components/SeverityBadge";
import { ChangeTypeBadge } from "@/components/ChangeTypeBadge";
import { Change, ChangeType, Importance } from "@/types";
import { timeAgo } from "@/lib/format";

const CHANGE_TYPES: ChangeType[] = ["pricing", "feature", "positioning", "product", "offer", "cta", "content", "messaging", "legal", "design", "other"];
const IMPORTANCES: Importance[] = ["critical", "high", "medium", "low"];

export default function ChangesFeedPage() {
  const { call, organizationId } = useApi();
  const [search, setSearch] = useState("");
  const [changeType, setChangeType] = useState<string>("");
  const [importance, setImportance] = useState<string>("");
  const [days, setDays] = useState<string>("30");

  const { data: changes, isLoading } = useQuery({
    queryKey: ["changes-feed", organizationId, search, changeType, importance, days],
    queryFn: () => call<Change[]>("/api/v1/changes", {
      params: {
        search: search || undefined,
        change_type: changeType || undefined,
        importance: importance || undefined,
        days: days ? Number(days) : undefined,
        limit: 100,
      },
    }),
    enabled: !!organizationId,
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Changes</h1>
      <p className="text-gray-500 mb-6">Everything meaningful we&apos;ve detected across your competitors.</p>

      <div className="flex flex-wrap gap-3 mb-5">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search pricing, AI, feature, competitor…"
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1 min-w-[200px]"
        />
        <select value={changeType} onChange={(e) => setChangeType(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">All types</option>
          {CHANGE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={importance} onChange={(e) => setImportance(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">All importance</option>
          {IMPORTANCES.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>
        <select value={days} onChange={(e) => setDays(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      {isLoading && <p className="text-gray-400">Loading…</p>}

      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {changes?.map((c) => (
          <Link key={c.id} href={`/changes/${c.id}`} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <SeverityEmoji importance={c.importance} />
              <div>
                <div className="flex items-center gap-2">
                  <ChangeTypeBadge type={c.change_type} />
                  {c.review_status === "unread" && <span className="text-xs text-blue-600 font-medium">New</span>}
                </div>
                <div className="text-sm text-gray-600 mt-1">{c.summary}</div>
              </div>
            </div>
            <div className="text-xs text-gray-400 whitespace-nowrap">{timeAgo(c.created_at)}</div>
          </Link>
        ))}
        {changes?.length === 0 && !isLoading && (
          <div className="px-5 py-10 text-center text-gray-400">No changes match these filters.</div>
        )}
      </div>
    </AppShell>
  );
}
