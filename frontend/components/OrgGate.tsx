"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest, ApiError } from "@/lib/api";
import { useOrganization } from "@/hooks/useOrganization";
import { Organization } from "@/types";

/**
 * Ensures the user has an active workspace before rendering the app shell.
 * On first login: lists their orgs (server-derived from Clerk user id),
 * auto-selects if exactly one exists, otherwise prompts to create one.
 * The organization id chosen here is only ever used as "which of MY orgs
 * am I viewing" — the backend independently verifies membership on every
 * subsequent request.
 *
 * Uses useQuery (not a hand-rolled useEffect+setState fetch) for the same
 * reason every other data-fetching component in this app does — it's the
 * established pattern here, and it means a failed fetch surfaces as a
 * real, visible error instead of leaving the screen stuck on "Loading…"
 * forever, which a raw useEffect version of this component previously did.
 */
export function OrgGate({ children }: { children: React.ReactNode }) {
  const { getToken, isLoaded } = useAuth();
  const { organizationId, setOrganizationId } = useOrganization();
  const queryClient = useQueryClient();
  const [newOrgName, setNewOrgName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const {
    data: orgs,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["my-organizations"],
    queryFn: async () => {
      const token = await getToken();
      return apiRequest<Organization[]>("/api/v1/organizations", token, null);
    },
    enabled: isLoaded && !organizationId,
  });

  // Auto-select the user's org when there's exactly one — done in an
  // effect, not inline during render. Calling setOrganizationId directly
  // in the render body (as an earlier version of this component did)
  // synchronously updates Providers' external-store state while React is
  // still mid-render of this component, which React explicitly disallows
  // ("Cannot update a component while rendering a different component").
  useEffect(() => {
    if (orgs && orgs.length === 1 && !organizationId) {
      setOrganizationId(orgs[0].id, orgs[0].name);
    }
  }, [orgs, organizationId, setOrganizationId]);

  if (organizationId) return <>{children}</>;

  if (!isLoaded || isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading your workspace…</div>;
  }

  if (isError) {
    const message =
      error instanceof ApiError ? `${error.status}: ${error.message}` : error instanceof Error ? error.message : "Failed to load workspaces";
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-xl border border-gray-200 w-full max-w-sm space-y-3 text-center">
          <h1 className="text-lg font-semibold text-gray-900">Couldn&apos;t load your workspace</h1>
          <p className="text-sm text-red-600 break-words">{message}</p>
          <p className="text-xs text-gray-400">
            This usually means the backend couldn&apos;t verify your sign-in — check that
            NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY (frontend) and CLERK_JWKS_URL/CLERK_ISSUER (backend)
            are from the same Clerk application.
          </p>
          <button
            onClick={() => refetch()}
            className="w-full bg-gray-900 text-white rounded-lg py-2 text-sm font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (orgs && orgs.length === 1 && !organizationId) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading your workspace…</div>;
  }

  if (orgs && orgs.length > 1) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-xl border border-gray-200 w-full max-w-sm space-y-3">
          <h1 className="text-lg font-semibold">Choose a workspace</h1>
          {orgs.map((o) => (
            <button
              key={o.id}
              onClick={() => setOrganizationId(o.id, o.name)}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-900 transition-colors"
            >
              <div className="font-medium">{o.name}</div>
              <div className="text-xs text-gray-500 capitalize">{o.role} · {o.plan} plan</div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // orgs is an empty array — first-time onboarding.
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl border border-gray-200 w-full max-w-sm space-y-4">
        <h1 className="text-lg font-semibold">Create your workspace</h1>
        <p className="text-sm text-gray-500">This is where you&apos;ll track your competitors.</p>
        <input
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          placeholder="e.g. Acme Inc."
          value={newOrgName}
          onChange={(e) => setNewOrgName(e.target.value)}
        />
        {createError && <p className="text-sm text-red-600">{createError}</p>}
        <button
          disabled={!newOrgName.trim() || creating}
          onClick={async () => {
            setCreating(true);
            setCreateError(null);
            try {
              const token = await getToken();
              const org = await apiRequest<{ id: string; name: string }>(
                "/api/v1/organizations", token, null, { method: "POST", body: { name: newOrgName.trim() } }
              );
              queryClient.invalidateQueries({ queryKey: ["my-organizations"] });
              setOrganizationId(org.id, org.name);
            } catch (e) {
              setCreateError(e instanceof Error ? e.message : "Failed to create workspace");
            } finally {
              setCreating(false);
            }
          }}
          className="w-full bg-gray-900 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50"
        >
          {creating ? "Creating…" : "Create workspace"}
        </button>
      </div>
    </div>
  );
}
