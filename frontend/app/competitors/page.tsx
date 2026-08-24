"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { Competitor } from "@/types";
import { AddCompetitorModal } from "@/components/AddCompetitorModal";

export default function CompetitorsPage() {
  const { call, organizationId } = useApi();
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);

  const { data: competitors, isLoading } = useQuery({
    queryKey: ["competitors", organizationId],
    queryFn: () => call<Competitor[]>("/api/v1/competitors", { params: { status: "active" } }),
    enabled: !!organizationId,
  });

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Competitors</h1>
          <p className="text-gray-500">Who you&apos;re tracking.</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium"
        >
          Add competitor
        </button>
      </div>

      {isLoading && <p className="text-gray-400">Loading…</p>}

      {competitors && competitors.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 px-5 py-12 text-center">
          <p className="text-gray-500 mb-4">No competitors yet. Add your first one to start monitoring.</p>
          <button onClick={() => setShowAdd(true)} className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium">
            Add competitor
          </button>
        </div>
      )}

      {competitors && competitors.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {competitors.map((c) => (
            <Link key={c.id} href={`/competitors/${c.id}`}
              className="bg-white rounded-xl border border-gray-200 px-5 py-4 hover:border-gray-400 transition-colors">
              <div className="font-medium text-gray-900">{c.name}</div>
              <div className="text-sm text-gray-500 mt-0.5">{c.website_url}</div>
              {c.industry && <div className="text-xs text-gray-400 mt-2">{c.industry}</div>}
            </Link>
          ))}
        </div>
      )}

      {showAdd && (
        <AddCompetitorModal
          onClose={() => setShowAdd(false)}
          onCreated={() => {
            queryClient.invalidateQueries({ queryKey: ["competitors", organizationId] });
          }}
        />
      )}
    </AppShell>
  );
}
