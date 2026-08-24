"use client";

import { useAuth } from "@clerk/nextjs";
import { useOrganization } from "@/hooks/useOrganization";
import { apiRequest } from "@/lib/api";
import { useCallback } from "react";

/** Returns a `call` function pre-wired with the current Clerk token and
 * active organization id — every page/component uses this instead of
 * touching fetch/localStorage directly. */
export function useApi() {
  const { getToken } = useAuth();
  const { organizationId } = useOrganization();

  const call = useCallback(
    async <T,>(path: string, options?: Parameters<typeof apiRequest>[3]) => {
      const token = await getToken();
      return apiRequest<T>(path, token, organizationId, options);
    },
    [getToken, organizationId]
  );

  return { call, organizationId };
}
