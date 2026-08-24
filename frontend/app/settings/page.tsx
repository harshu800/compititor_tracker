"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/hooks/useApi";
import { AppShell } from "@/components/AppShell";
import { BillingSection } from "@/components/BillingSection";

interface NotificationSettings {
  critical_email: boolean;
  high_email: boolean;
  medium_email: boolean;
  low_email: boolean;
  weekly_digest: boolean;
}

const ROWS: { key: keyof NotificationSettings; label: string }[] = [
  { key: "critical_email", label: "Critical" },
  { key: "high_email", label: "High" },
  { key: "medium_email", label: "Medium" },
  { key: "low_email", label: "Low" },
];

export default function SettingsPage() {
  const { call, organizationId } = useApi();
  const queryClient = useQueryClient();
  const [seeding, setSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const { data: settings } = useQuery({
    queryKey: ["notification-settings", organizationId],
    queryFn: () => call<NotificationSettings>("/api/v1/settings/notifications"),
    enabled: !!organizationId,
  });

  async function toggle(key: keyof NotificationSettings, value: boolean) {
    await call("/api/v1/settings/notifications", { method: "PATCH", body: { [key]: value } });
    queryClient.invalidateQueries({ queryKey: ["notification-settings", organizationId] });
  }

  async function handleSeedDemo() {
    setSeeding(true);
    setSeedMessage(null);
    try {
      const result = await call<{ competitors: number; pages: number; changes: number }>("/api/v1/demo/seed", { method: "POST" });
      setSeedMessage(`Added ${result.competitors} demo competitors, ${result.pages} pages, ${result.changes} changes.`);
      queryClient.invalidateQueries();
    } catch (e) {
      setSeedMessage(e instanceof Error ? e.message : "Failed to seed demo data.");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <AppShell>
      <h1 className="text-2xl font-semibold text-gray-900 mb-1">Settings</h1>
      <p className="text-gray-500 mb-6">Alert preferences and workspace tools.</p>

      <div className="mb-6">
        <BillingSection />
      </div>

      <section className="bg-white rounded-xl border border-gray-200 p-5 mb-6 max-w-lg">
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Email alerts by severity</h2>
        <p className="text-xs text-gray-500 mb-4">In-app alerts are always on for every severity. Choose which also send email.</p>
        <div className="space-y-3">
          {ROWS.map((row) => (
            <label key={row.key} className="flex items-center justify-between text-sm">
              <span>{row.label}</span>
              <input
                type="checkbox"
                checked={settings ? settings[row.key] : false}
                onChange={(e) => toggle(row.key, e.target.checked)}
              />
            </label>
          ))}
          <div className="border-t border-gray-100 pt-3 flex items-center justify-between text-sm">
            <span>Weekly digest</span>
            <input
              type="checkbox"
              checked={settings?.weekly_digest ?? false}
              onChange={(e) => toggle("weekly_digest", e.target.checked)}
            />
          </div>
        </div>
      </section>

      <section className="bg-white rounded-xl border border-gray-200 p-5 max-w-lg">
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Demo data</h2>
        <p className="text-xs text-gray-500 mb-4">
          Populate this workspace with realistic, clearly-labeled demo competitors and changes — no API keys required.
        </p>
        <button
          onClick={handleSeedDemo}
          disabled={seeding}
          className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {seeding ? "Seeding…" : "Seed demo data"}
        </button>
        {seedMessage && <p className="text-sm text-gray-600 mt-3">{seedMessage}</p>}
      </section>
    </AppShell>
  );
}
