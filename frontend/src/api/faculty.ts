import { getSupabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const PREFIX = "/api/v1/faculty";
const supabase = getSupabase("faculty");

function authHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function getAccessToken(): Promise<string | undefined> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token;
}

async function authFetch(url: string, init: RequestInit = {}) {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers: { ...authHeaders(token), ...init.headers },
  });
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`);
  return response;
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

export type SubjectResponse = {
  id: string;
  name: string;
  code: string;
  batch_id: string;
};

export type BatchDetail = BatchResponse & {
  subjects: SubjectResponse[];
  student_enrollment_ids: string[];
};

export type PostSummary = {
  id: string;
  content: string;
  post_type: string;
  subject_name: string | null;
  subject_code: string | null;
  batch_code: string | null;
  batch_name: string | null;
  due_date: string | null;
  file_name: string | null;
  created_at: string | null;
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
  const response = await authFetch(`${PREFIX}/feed`);
  return response.json();
}

export async function fetchBatches(): Promise<BatchResponse[]> {
  const response = await authFetch(`${PREFIX}/batches`);
  return response.json();
}

export async function createBatch(data: {
  name: string;
  code: string;
  semester: string;
  branch: string;
}): Promise<BatchResponse> {
  const response = await authFetch(`${PREFIX}/batches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function fetchBatchDetail(batchId: string): Promise<BatchDetail> {
  const response = await authFetch(`${PREFIX}/batches/${batchId}`);
  return response.json();
}

export async function addSubjectToBatch(batchId: string, data: { name: string; code: string }) {
  const response = await authFetch(`${PREFIX}/batches/${batchId}/subjects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function addStudentToBatch(batchId: string, enrollmentId: string) {
  const response = await authFetch(`${PREFIX}/batches/${batchId}/students`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enrollment_id: enrollmentId }),
  });
  return response.json();
}

export async function removeStudentFromBatch(batchId: string, enrollmentId: string) {
  const response = await authFetch(`${PREFIX}/batches/${batchId}/students/${enrollmentId}`, {
    method: "DELETE",
  });
  return response.json();
}

export async function fetchBatchPosts(batchId: string): Promise<PostSummary[]> {
  const response = await authFetch(`${PREFIX}/batches/${batchId}/posts`);
  return response.json();
}

export async function createPost(
  batchId: string,
  subjectId: string,
  content: string,
  file: File | null,
) {
  const token = await getAccessToken();
  const formData = new FormData();
  formData.append("batch_id", batchId);
  formData.append("subject_id", subjectId);
  formData.append("content", content);
  if (file) formData.append("file", file);

  const response = await fetch(`${API_BASE}${PREFIX}/posts`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
