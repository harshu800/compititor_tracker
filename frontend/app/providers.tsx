"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { OrganizationContext } from "@/hooks/useOrganization";
import { useOrgState } from "@/hooks/useOrgState";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
  }));
  const orgState = useOrgState();
  const contextValue = useMemo(() => orgState, [orgState]);

  return (
    <ClerkProvider>
      <QueryClientProvider client={queryClient}>
        <OrganizationContext.Provider value={contextValue}>
          {children}
        </OrganizationContext.Provider>
      </QueryClientProvider>
    </ClerkProvider>
  );
}
