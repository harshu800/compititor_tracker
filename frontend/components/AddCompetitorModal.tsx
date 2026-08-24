"use client";

import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { ApiError } from "@/lib/api";
import { Competitor, CheckFrequency, PageType } from "@/types";

type Step = "basics" | "pages" | "frequency" | "creating";

interface Suggestion {
  page_type: PageType;
  url: string;
  exists: boolean;
}

/** The 4-step add-competitor flow from spec section 24:
 * 1. Name + URL  2. Suggested pages (user approves which to add)
 * 3. Monitoring frequency  4. Start monitoring
 * No page is ever added without the user explicitly approving it here. */
export function AddCompetitorModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { call } = useApi();
  const [step, setStep] = useState<Step>("basics");
  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [industry, setIndustry] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [approved, setApproved] = useState<Set<string>>(new Set());
  const [frequency, setFrequency] = useState<CheckFrequency>("daily");
  const [error, setError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);

  async function handleContinueFromBasics() {
    setError(null);
    setDiscovering(true);
    try {
      const result = await call<{ homepage_reachable: boolean; suggestions: Suggestion[] }>(
        "/api/v1/pages/discover", { method: "POST", params: { website_url: websiteUrl } }
      );
      setSuggestions(result.suggestions);
      setApproved(new Set(result.suggestions.map((s) => s.url))); // pre-check all found pages; user can uncheck
      setStep("pages");
    } catch (e) {
      // Discovery is best-effort — if it fails, let the user proceed and add pages manually later.
      setSuggestions([]);
      setStep("pages");
    } finally {
      setDiscovering(false);
    }
  }

  async function handleStartMonitoring() {
    setStep("creating");
    setError(null);
    try {
      const competitor = await call<Competitor>("/api/v1/competitors", {
        method: "POST",
        body: { name, website_url: websiteUrl, industry: industry || undefined },
      });

      const toAdd = suggestions.filter((s) => approved.has(s.url));
      for (const s of toAdd) {
        await call(`/api/v1/competitors/${competitor.id}/pages`, {
          method: "POST",
          body: { url: s.url, page_type: s.page_type, check_frequency: frequency },
        });
      }

      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Please try again.");
      setStep("pages");
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-md p-6 space-y-4">
        {step === "basics" && (
          <>
            <h2 className="text-lg font-semibold">Add a competitor</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700">Competitor name</label>
                <input value={name} onChange={(e) => setName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1" placeholder="Acme CRM" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Website URL</label>
                <input value={websiteUrl} onChange={(e) => setWebsiteUrl(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1" placeholder="https://acme.com" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Industry (optional)</label>
                <input value={industry} onChange={(e) => setIndustry(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1" placeholder="CRM SaaS" />
              </div>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
              <button
                disabled={!name.trim() || !websiteUrl.trim() || discovering}
                onClick={handleContinueFromBasics}
                className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                {discovering ? "Looking for pages…" : "Continue"}
              </button>
            </div>
          </>
        )}

        {step === "pages" && (
          <>
            <h2 className="text-lg font-semibold">Pages to monitor</h2>
            <p className="text-sm text-gray-500">We only suggest pages we could actually find — uncheck any you don&apos;t want.</p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {suggestions.length === 0 && (
                <p className="text-sm text-gray-400">We couldn&apos;t auto-detect pages. You can add specific URLs later from the competitor page.</p>
              )}
              {suggestions.map((s) => (
                <label key={s.url} className="flex items-center gap-3 border border-gray-200 rounded-lg px-3 py-2 text-sm">
                  <input type="checkbox" checked={approved.has(s.url)}
                    onChange={(e) => {
                      const next = new Set(approved);
                      e.target.checked ? next.add(s.url) : next.delete(s.url);
                      setApproved(next);
                    }} />
                  <div>
                    <div className="font-medium capitalize">{s.page_type} ✓</div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">{s.url}</div>
                  </div>
                </label>
              ))}
            </div>
            <div className="flex justify-between pt-2">
              <button onClick={() => setStep("basics")} className="px-4 py-2 text-sm text-gray-600">Back</button>
              <button onClick={() => setStep("frequency")} className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium">
                Continue
              </button>
            </div>
          </>
        )}

        {step === "frequency" && (
          <>
            <h2 className="text-lg font-semibold">Monitoring frequency</h2>
            <div className="space-y-2">
              {(["daily", "weekly"] as CheckFrequency[]).map((f) => (
                <label key={f} className="flex items-center gap-3 border border-gray-200 rounded-lg px-3 py-3 text-sm cursor-pointer">
                  <input type="radio" name="freq" checked={frequency === f} onChange={() => setFrequency(f)} />
                  <span className="capitalize font-medium">{f}</span>
                </label>
              ))}
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-between pt-2">
              <button onClick={() => setStep("pages")} className="px-4 py-2 text-sm text-gray-600">Back</button>
              <button onClick={handleStartMonitoring} className="bg-gray-900 text-white rounded-lg px-4 py-2 text-sm font-medium">
                Start monitoring
              </button>
            </div>
          </>
        )}

        {step === "creating" && <p className="text-center text-gray-500 py-8">Setting up monitoring…</p>}
      </div>
    </div>
  );
}
