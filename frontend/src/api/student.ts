import { getSupabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const PREFIX = "/api/v1/student";
const supabase = getSupabase("student");

function authHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function getAccessToken(): Promise<string | undefined> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token;
}

export type UserProfile = {
  id: string;
  email: string;
  role: "student" | "faculty" | "admin";
  full_name: string | null;
  semester: string | null;
  branch: string | null;
  enrollment_id: string | null;
};

export type BatchResponse = {
  id: string;
  name: string;
  code: string;
  semester: string;
  branch: string;
  student_count: number;
  subject_count: number;
};

export type FeedItem = {
  id: string;
  title: string;
  content: string;
  item_type: string;
  subject_code: string | null;
  batch_code: string | null;
  due_date: string | null;
  file_name: string | null;
  created_at: string | null;
};

export async function fetchProfile(token: string): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}${PREFIX}/me`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function fetchFeed(): Promise<FeedItem[]> {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE}${PREFIX}/feed`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function fetchBatches(): Promise<BatchResponse[]> {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE}${PREFIX}/batches`, { headers: authHeaders(token) });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export async function sendQuery(message: string, sessionId?: string) {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE}${PREFIX}/query/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!response.ok) throw new Error(`Query failed: ${response.status}`);
  return response.json();
}

export async function uploadScreenshot(file: File) {
  const token = await getAccessToken();
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}${PREFIX}/jarvis/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
  return response.json();
}
