/** API client: session-cookie auth, CSRF handling, predictable errors. */
import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[2] ?? "") : null;
}

api.interceptors.request.use((config) => {
  const csrf = getCookie("csrftoken");
  if (csrf && config.method && ["post", "put", "patch", "delete"].includes(config.method)) {
    config.headers.set("X-CSRFToken", csrf);
  }
  return config;
});

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]> | string[];
}

export function extractApiError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { error?: ApiError; detail?: string } | undefined;
    if (data?.error) return data.error;
    if (data?.detail) return { code: "error", message: data.detail };
    if (err.response) return { code: "http_error", message: `HTTP ${err.response.status}` };
    return { code: "network", message: "Network error" };
  }
  return { code: "unknown", message: "Unknown error" };
}
