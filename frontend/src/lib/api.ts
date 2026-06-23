import { auth } from "@/lib/auth";
import type { TokenPair } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Send the active org slug as the tenant header (default: true). */
  withTenant?: boolean;
  /** Attach the JWT access token (default: true). */
  auth?: boolean;
  /** Internal: prevent infinite refresh recursion. */
  _retried?: boolean;
}

/** Flatten a DRF error payload into a single human-readable message. */
function extractDetail(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const obj = payload as Record<string, unknown>;
  const detail = (obj.error as Record<string, unknown>)?.detail ?? obj.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const first = Object.entries(detail as Record<string, unknown>)[0];
    if (first) {
      const [field, msgs] = first;
      const msg = Array.isArray(msgs) ? msgs[0] : msgs;
      return field === "non_field_errors" ? String(msg) : `${field}: ${msg}`;
    }
  }
  return fallback;
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = auth.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { access: string; refresh?: string };
    auth.setTokens({ access: data.access, refresh: data.refresh ?? refresh });
    return true;
  } catch {
    return false;
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, withTenant = true, auth: useAuth = true, _retried, headers, ...rest } = options;

  const finalHeaders = new Headers(headers);
  finalHeaders.set("Content-Type", "application/json");

  if (useAuth) {
    const token = auth.getAccess();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }
  if (withTenant) {
    const slug = auth.getOrgSlug();
    if (slug) finalHeaders.set("X-Org-Slug", slug);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Transparently refresh once on a 401.
  if (response.status === 401 && useAuth && !_retried) {
    if (await refreshAccessToken()) {
      return request<T>(path, { ...options, _retried: true });
    }
  }

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, extractDetail(payload, response.statusText), payload);
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

// --- Auth helpers -----------------------------------------------------------

export async function login(email: string, password: string): Promise<TokenPair> {
  const tokens = await api.post<TokenPair>(
    "/api/auth/token/",
    { email, password },
    { auth: false, withTenant: false },
  );
  auth.setTokens(tokens);
  return tokens;
}

export function logout() {
  auth.clear();
}
