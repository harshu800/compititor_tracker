"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { SeverityEmoji } from "@/components/SeverityBadge";
import { ChangeTypeBadge } from "@/components/ChangeTypeBadge";
import { DashboardData } from "@/types";
import { timeAgo } from "@/lib/format";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 px-5 py-4">
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { call, organizationId } = useApi();

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard", organizationId],
    queryFn: () => call<DashboardData>("/api/v1/dashboard"),
    enabled: !!organizationId,
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Overview</h1>
      <p className="text-gray-500 mb-6">What your competitors changed, at a glance.</p>

      {isLoading && <p className="text-gray-400">Loading…</p>}
      {error && <p className="text-red-600">Couldn&apos;t load your dashboard. Try refreshing.</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Competitors" value={data.competitors} />
            <StatCard label="Changes this week" value={data.changes_this_week} />
            <StatCard label="Important changes" value={data.important_changes} />
            <StatCard label="Unreviewed" value={data.unreviewed} />
          </div>

          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent important changes</h2>
          {data.recent_important_changes.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 px-5 py-8 text-center text-gray-500">
              No important changes yet. Once you add competitors and monitoring picks something up, it&apos;ll show here.
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
              {data.recent_important_changes.map((c) => (
                <Link
                  key={c.change_id}
                  href={`/changes/${c.change_id}`}
                  className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <SeverityEmoji importance={c.importance} />
                    <div>
                      <div className="font-medium text-gray-900">
                        {c.competitor_name} — <ChangeTypeBadge type={c.change_type} />
                      </div>
                      <div className="text-sm text-gray-500 mt-0.5">{c.summary}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 whitespace-nowrap">{timeAgo(c.created_at)}</div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
