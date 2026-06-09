const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export type SignUpPayload = {
  email: string;
  password: string;
  full_name: string;
  role: "student" | "faculty";
  enrollment_id?: string;
  semester?: string;
  branch?: string;
};

async function parseError(response: Response): Promise<string> {
  const text = await response.text();
  try {
    const data = JSON.parse(text) as { detail?: string };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* not JSON */
  }
  return text || `Request failed: ${response.status}`;
}

export async function signUpAccount(payload: SignUpPayload): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}
