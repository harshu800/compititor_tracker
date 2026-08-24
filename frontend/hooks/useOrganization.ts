"use client";

import { createContext, useContext } from "react";

/** The user's ACTIVE workspace (organization) for this session. Set once
 * after org selection/creation on first login; every API call reads this
 * to populate X-Organization-Id. The backend independently verifies
 * membership — this context only decides which of the user's own orgs
 * they're currently viewing. */
export interface OrganizationContextValue {
  organizationId: string | null;
  organizationName: string | null;
  setOrganizationId: (id: string, name: string) => void;
}

export const OrganizationContext = createContext<OrganizationContextValue>({
  organizationId: null,
  organizationName: null,
  setOrganizationId: () => {},
});

export function useOrganization() {
  return useContext(OrganizationContext);
}
