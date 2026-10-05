import type { ApiErrorBody } from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api"
).replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "cloudpilot.accessToken";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getAccessToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeAccessToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(
      errorBody.detail ?? `Request failed with status ${response.status}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}