/**
 * Regression coverage for a real bug: an earlier rewrite of OrgGate.tsx
 * called setOrganizationId(...) directly in its render body (inside a
 * useQuery-driven auto-select branch) instead of inside a useEffect.
 * Because useOrgState's setOrganizationId synchronously notifies
 * external-store listeners (see hooks/useOrgState.ts), this triggered
 * React's "Cannot update a component while rendering a different
 * component" error in the browser — caught only by a real user's browser
 * console, not by ESLint, tsc, or `next build`.
 *
 * Two layers of coverage here:
 * 1. A behavioral test proving the FIXED pattern (setOrganizationId called
 *    from a useEffect) never produces a console error, using the real
 *    useOrgState/useOrganization implementation end to end.
 * 2. A source-level guard against the exact historical bug shape
 *    reappearing in OrgGate.tsx specifically.
 *
 * Note on why this isn't a jsdom reproduction of the actual browser
 * warning: React's "Cannot update a component while rendering a different
 * component" check depends on scheduler/fiber timing that React Testing
 * Library's act()-wrapped render (and even a raw createRoot render) does
 * not reliably reproduce outside real browser/Next.js scheduling — this
 * was verified directly (three different rendering approaches were tried
 * against a deliberately-reintroduced copy of the buggy pattern, and none
 * reproduced the warning here, despite it firing in the real browser).
 * The source-level check below is the reliable substitute: it can't catch
 * a *new* instance of this bug elsewhere, but it guarantees this specific,
 * already-diagnosed regression can't silently reappear in this file.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { readFileSync } from "fs";
import { join } from "path";
import { render } from "@testing-library/react";
import { useEffect } from "react";
import { OrganizationContext, useOrganization } from "@/hooks/useOrganization";
import { useOrgState } from "@/hooks/useOrgState";

function Root({ children }: { children: React.ReactNode }) {
  const orgState = useOrgState();
  return <OrganizationContext.Provider value={orgState}>{children}</OrganizationContext.Provider>;
}

/** The fixed pattern: setOrganizationId called from useEffect, not inline
 * during render — this is what OrgGate.tsx actually does now. */
function ComponentCallingFromEffect() {
  const { setOrganizationId, organizationId } = useOrganization();
  useEffect(() => {
    if (!organizationId) {
      setOrganizationId("org_1", "Test Org");
    }
  }, [organizationId, setOrganizationId]);
  return <div>ok</div>;
}

describe("useOrgState — cross-component render-safety", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    sessionStorage.clear();
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("the fixed pattern — calling setOrganizationId from useEffect — produces zero console errors", () => {
    render(
      <Root>
        <ComponentCallingFromEffect />
      </Root>
    );
    expect(consoleErrorSpy).not.toHaveBeenCalled();
  });
});

describe("OrgGate.tsx — source-level regression guard", () => {
  const source = readFileSync(join(__dirname, "..", "components", "OrgGate.tsx"), "utf-8");

  it("does not call setOrganizationId directly followed by a loading-state return (the historical bug shape)", () => {
    // The exact buggy code was:
    //   setOrganizationId(orgs[0].id, orgs[0].name);
    //   return <div ...>Loading your workspace…</div>;
    // i.e. a direct call immediately followed by returning JSX in the same
    // branch, with no useEffect/callback boundary in between.
    expect(source).not.toMatch(/setOrganizationId\([^)]*\);\s*\n\s*return\s*</);
  });

  it("calls setOrganizationId for the auto-select-single-org case from inside a useEffect", () => {
    const autoSelectEffectPattern =
      /useEffect\(\(\)\s*=>\s*\{[^}]*orgs\.length === 1[^}]*setOrganizationId/s;
    expect(source).toMatch(autoSelectEffectPattern);
  });
});
