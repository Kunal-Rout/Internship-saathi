import type {
  OptionsResponse,
  Internship,
  CandidateProfile,
  RecommendationResponse,
} from "../types";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
  : "/api/v1";

export async function fetchHealth(): Promise<{ status: string; sample_data_count: number }> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchOptions(): Promise<OptionsResponse> {
  const res = await fetch(`${API_BASE_URL}/options`);
  if (!res.ok) {
    throw new Error(`Failed to fetch options: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchInternshipDetail(id: string): Promise<Internship> {
  const res = await fetch(`${API_BASE_URL}/internships/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to load internship: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRecommendations(
  profile: CandidateProfile,
  limit: number = 5
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE_URL}/recommendations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ profile, limit }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData.detail || `Server returned error (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
