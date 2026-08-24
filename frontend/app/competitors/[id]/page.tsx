"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { SeverityEmoji } from "@/components/SeverityBadge";
import { ChangeTypeBadge } from "@/components/ChangeTypeBadge";
import { Competitor, MonitoredPage, Change } from "@/types";
import { timeAgo } from "@/lib/format";

export default function CompetitorDetailPage() {
  const params = useParams<{ id: string }>();
  const { call, organizationId } = useApi();

  const { data: competitor } = useQuery({
    queryKey: ["competitor", params.id],
    queryFn: () => call<Competitor>(`/api/v1/competitors/${params.id}`),
    enabled: !!organizationId,
  });

  const { data: pages } = useQuery({
    queryKey: ["competitor-pages", params.id],
    queryFn: () => call<MonitoredPage[]>(`/api/v1/competitors/${params.id}/pages`),
    enabled: !!organizationId,
  });

  const { data: changes } = useQuery({
    queryKey: ["competitor-changes", params.id],
    queryFn: () => call<Change[]>("/api/v1/changes", { params: { competitor_id: params.id, limit: 30 } }),
    enabled: !!organizationId,
  });

  const changesLast30d = changes?.length ?? 0;
  const highImpact = changes?.filter((c) => c.importance === "critical" || c.importance === "high").length ?? 0;

  return (
    <AppShell>
      {competitor && (
        <>
          <h1 className="text-2xl font-semibold text-gray-900">{competitor.name}</h1>
          <p className="text-gray-500 mb-6">{competitor.website_url}</p>

          <div className="grid grid-cols-3 gap-4 mb-8 max-w-lg">
            <div className="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <div className="text-xl font-semibold">{pages?.length ?? 0}</div>
              <div className="text-xs text-gray-500 mt-1">Pages monitored</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <div className="text-xl font-semibold">{changesLast30d}</div>
              <div className="text-xs text-gray-500 mt-1">Recent changes</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 px-4 py-3">
              <div className="text-xl font-semibold">{highImpact}</div>
              <div className="text-xs text-gray-500 mt-1">High-impact</div>
            </div>
          </div>

          <h2 className="text-lg font-semibold text-gray-900 mb-3">Monitored pages</h2>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100 mb-8">
            {pages?.map((p) => (
              <div key={p.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <span className="font-medium capitalize">{p.page_type}</span>
                  <span className="text-sm text-gray-500 ml-2">{p.url}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {p.last_checked_at ? `Checked ${timeAgo(p.last_checked_at)}` : "Not checked yet"}
                </div>
              </div>
            ))}
            {pages?.length === 0 && <div className="px-5 py-6 text-sm text-gray-400">No pages added yet.</div>}
          </div>

          <h2 className="text-lg font-semibold text-gray-900 mb-3">Change history</h2>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {changes?.map((c) => (
              <Link key={c.id} href={`/changes/${c.id}`} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <SeverityEmoji importance={c.importance} />
                  <div>
                    <ChangeTypeBadge type={c.change_type} />
                    <div className="text-sm text-gray-600 mt-1">{c.summary}</div>
                  </div>
                </div>
                <div className="text-xs text-gray-400 whitespace-nowrap">{timeAgo(c.created_at)}</div>
              </Link>
            ))}
            {changes?.length === 0 && <div className="px-5 py-6 text-sm text-gray-400">No changes detected yet.</div>}
          </div>
        </>
      )}
    </AppShell>
  );
}
