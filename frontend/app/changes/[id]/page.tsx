"use client";

import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ChangeTypeBadge } from "@/components/ChangeTypeBadge";
import { Change, ReviewStatus } from "@/types";
import { formatDate } from "@/lib/format";

function DiffBlock({ change }: { change: Change }) {
  const diff = change.diff_json;
  if (!diff) return null;
  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3 text-sm">
      {diff.removed.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Removed</div>
          {diff.removed.map((r, i) => (
            <div key={i} className="bg-red-50 text-red-800 px-2 py-1 rounded mb-1 line-through decoration-red-400">{r}</div>
          ))}
        </div>
      )}
      {diff.added.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Added</div>
          {diff.added.map((a, i) => (
            <div key={i} className="bg-green-50 text-green-800 px-2 py-1 rounded mb-1">{a}</div>
          ))}
        </div>
      )}
      {diff.modified.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Changed</div>
          {diff.modified.map((m, i) => (
            <div key={i} className="mb-2">
              <div className="bg-red-50 text-red-800 px-2 py-1 rounded line-through decoration-red-400">{m.before}</div>
              <div className="bg-green-50 text-green-800 px-2 py-1 rounded mt-1">{m.after}</div>
            </div>
          ))}
        </div>
      )}
      {diff.added.length === 0 && diff.removed.length === 0 && diff.modified.length === 0 && (
        <p className="text-gray-400">Structural changes only — see the summary above.</p>
      )}
    </div>
  );
}

const REVIEW_ACTIONS: { status: ReviewStatus; label: string }[] = [
  { status: "reviewed", label: "Mark reviewed" },
  { status: "important", label: "Mark important" },
  { status: "ignored", label: "Ignore" },
];

export default function ChangeDetailPage() {
  const params = useParams<{ id: string }>();
  const { call, organizationId } = useApi();
  const queryClient = useQueryClient();

  const { data: change, isLoading } = useQuery({
    queryKey: ["change", params.id],
    queryFn: () => call<Change>(`/api/v1/changes/${params.id}`),
    enabled: !!organizationId,
  });

  async function setReview(status: ReviewStatus) {
    await call(`/api/v1/changes/${params.id}/review`, { method: "PATCH", body: { review_status: status } });
    queryClient.invalidateQueries({ queryKey: ["change", params.id] });
  }

  if (isLoading || !change) {
    return <AppShell><p className="text-gray-400">Loading…</p></AppShell>;
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-2">
        <ChangeTypeBadge type={change.change_type} />
        <SeverityBadge importance={change.importance} />
      </div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">{change.summary}</h1>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">What changed?</h2>
            <p className="text-gray-700 text-sm">{change.what_changed}</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Diff</h2>
            <DiffBlock change={change} />
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Why it matters</h2>
            <p className="text-gray-700 text-sm">{change.why_it_matters}</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Recommended action</h2>
            <p className="text-gray-700 text-sm bg-blue-50 border border-blue-100 rounded-lg p-3">{change.recommended_action}</p>
          </section>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-xl p-4 text-sm space-y-2">
            <div className="flex justify-between"><span className="text-gray-500">Impact score</span><span className="font-medium">{change.impact_score}/100</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Detected</span><span className="font-medium">{formatDate(change.created_at)}</span></div>
            {change.ai_confidence !== null && (
              <div className="flex justify-between"><span className="text-gray-500">AI confidence</span><span className="font-medium">{Math.round(change.ai_confidence * 100)}%</span></div>
            )}
            <div className="flex justify-between"><span className="text-gray-500">Status</span><span className="font-medium capitalize">{change.review_status}</span></div>
          </div>

          <div className="space-y-2">
            {REVIEW_ACTIONS.map((a) => (
              <button
                key={a.status}
                onClick={() => setReview(a.status)}
                disabled={change.review_status === a.status}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-40 hover:bg-gray-50"
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
