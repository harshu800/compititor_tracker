"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from "recharts";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { ReportData } from "@/types";
import { useAuth } from "@clerk/nextjs";

const PERIODS = [
  { label: "Last 7 days", value: 7 },
  { label: "Last 30 days", value: 30 },
  { label: "Last 90 days", value: 90 },
];

export default function ReportsPage() {
  const { call, organizationId } = useApi();
  const { getToken } = useAuth();
  const [periodDays, setPeriodDays] = useState(30);

  async function handleExportCsv() {
    const token = await getToken();
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/changes/export/csv?days=${periodDays}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Organization-Id": organizationId || "",
      },
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "changes.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  }

  const { data, isLoading } = useQuery({
    queryKey: ["reports", organizationId, periodDays],
    queryFn: () => call<ReportData>("/api/v1/reports", { params: { period_days: periodDays } }),
    enabled: !!organizationId,
  });

  const typeData = data ? Object.entries(data.changes_by_type).map(([name, count]) => ({ name, count })) : [];
  const importanceData = data ? Object.entries(data.changes_by_importance).map(([name, count]) => ({ name, count })) : [];
  const competitorData = data ? Object.entries(data.changes_by_competitor).map(([name, count]) => ({ name, count })) : [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Reports</h1>
          <p className="text-gray-500">Trends across all your tracked competitors.</p>
        </div>
        <select value={periodDays} onChange={(e) => setPeriodDays(Number(e.target.value))} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
      </div>

      {isLoading && <p className="text-gray-400">Loading…</p>}

      {data && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Changes over time</h2>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.changes_over_time}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#111827" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Changes by importance</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={importanceData}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#111827" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Changes by type</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={typeData} layout="vertical">
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#6B7280" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Changes by competitor</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={competitorData} layout="vertical">
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#111827" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="mt-6">
        <button
          onClick={handleExportCsv}
          className="inline-block border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium hover:bg-gray-50"
        >
          Export CSV
        </button>
      </div>
    </AppShell>
  );
}
