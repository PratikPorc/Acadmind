const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export type HealthResponse = {
  status: "ok" | "degraded" | "error";
  app: string;
  environment: string;
  services: Array<{ name: string; status: string; detail?: string }>;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/api/v1/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}
