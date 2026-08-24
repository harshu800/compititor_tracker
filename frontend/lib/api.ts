"use client";

/**
 * Thin API client. Every request attaches the Clerk session token
 * (Authorization: Bearer <token>) and the active organization id
 * (X-Organization-Id). The backend is the source of truth for whether
 * the user actually belongs to that org — this header is just "which of
 * my orgs am I acting as", never a trust boundary by itself.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
}

export async function apiRequest<T>(
  path: string,
  token: string | null,
  organizationId: string | null,
  options: RequestOptions = {}
): Promise<T> {
  const url = new URL(`${API_URL}${path}`);
  if (options.params) {
    Object.entries(options.params).forEach(([k, v]) => {
      if (v !== undefined) url.searchParams.set(k, String(v));
    });
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (organizationId) headers["X-Organization-Id"] = organizationId;

  const res = await fetch(url.toString(), {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore parse failure */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}
