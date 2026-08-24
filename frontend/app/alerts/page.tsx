"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { SeverityEmoji } from "@/components/SeverityBadge";
import { timeAgo } from "@/lib/format";
import { Importance } from "@/types";

interface AlertItem {
  id: string;
  change_id: string;
  channel: "email" | "in_app";
  severity: Importance;
  sent: boolean;
  created_at: string;
}

export default function AlertsPage() {
  const { call, organizationId } = useApi();
  const { data: alerts, isLoading } = useQuery({
    queryKey: ["alerts", organizationId],
    queryFn: () => call<AlertItem[]>("/api/v1/alerts"),
    enabled: !!organizationId,
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Alerts</h1>
      <p className="text-gray-500 mb-6">Every alert we&apos;ve sent — in-app and email.</p>

      {isLoading && <p className="text-gray-400">Loading…</p>}

      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {alerts?.map((a) => (
          <Link key={a.id} href={`/changes/${a.change_id}`} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <SeverityEmoji importance={a.severity} />
              <div>
                <div className="font-medium text-gray-900 capitalize">{a.severity} · {a.channel === "email" ? "Email" : "In-app"}</div>
                <div className="text-xs text-gray-400">{a.sent ? "Sent" : "Pending"}</div>
              </div>
            </div>
            <div className="text-xs text-gray-400 whitespace-nowrap">{timeAgo(a.created_at)}</div>
          </Link>
        ))}
        {alerts?.length === 0 && !isLoading && (
          <div className="px-5 py-10 text-center text-gray-400">No alerts yet.</div>
        )}
      </div>
    </AppShell>
  );
}
