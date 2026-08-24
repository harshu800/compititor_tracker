"use client";

import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "ct_active_org";

interface StoredOrg {
  id: string;
  name: string;
}

let currentValue: StoredOrg | null = null;
let initialized = false;
const listeners = new Set<() => void>();

function readFromStorage(): StoredOrg | null {
  if (typeof window === "undefined") return null;
  const stored = sessionStorage.getItem(STORAGE_KEY);
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

function getSnapshot(): StoredOrg | null {
  // Read lazily, once — after that, this module-level cache is the single
  // source of truth so repeated calls return a referentially stable value
  // (required by useSyncExternalStore to avoid re-render loops).
  if (!initialized) {
    currentValue = readFromStorage();
    initialized = true;
  }
  return currentValue;
}

function getServerSnapshot(): StoredOrg | null {
  return null; // sessionStorage doesn't exist during SSR
}

function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

function writeToStorage(id: string, name: string) {
  currentValue = { id, name };
  initialized = true;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(currentValue));
  listeners.forEach((listener) => listener());
}

/**
 * Session-only "which workspace am I in" state, backed by sessionStorage.
 *
 * Uses useSyncExternalStore rather than useEffect+setState: the server
 * always renders with organizationId=null (no sessionStorage exists there),
 * and React reconciles the real client value immediately after hydration
 * without us manually triggering a state update inside an effect — the
 * officially recommended pattern for syncing with browser-only storage,
 * and it avoids both a hydration mismatch and an unnecessary extra render.
 *
 * Never trusted as authorization — the backend re-verifies membership on
 * every request regardless of what's stored here.
 */
export function useOrgState() {
  const stored = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setOrganizationId = useCallback((id: string, name: string) => {
    writeToStorage(id, name);
  }, []);

  return {
    organizationId: stored?.id ?? null,
    organizationName: stored?.name ?? null,
    setOrganizationId,
  };
}
