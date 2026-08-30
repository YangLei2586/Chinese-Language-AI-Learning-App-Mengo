import type { LearnerProfile, Progress, Scenario, TutorTurn, VocabularyWord } from "@mengo/shared-types";

const baseUrl = process.env.EXPO_PUBLIC_API_URL ?? "http://10.0.2.2:8000/v1";
const demoUser = process.env.EXPO_PUBLIC_DEMO_USER ?? "demo-learner";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Demo-User": demoUser, ...options.headers }
  });
  if (!response.ok) throw new Error((await response.json().catch(() => ({ detail: "Request failed" }))).detail);
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}

export const api = {
  profile: () => request<LearnerProfile>("/me/profile"),
  saveProfile: (profile: Omit<LearnerProfile, "onboarding_complete">) => request<LearnerProfile>("/me/profile", { method: "PUT", body: JSON.stringify(profile) }),
  scenarios: () => request<Scenario[]>("/scenarios"),
  progress: () => request<Progress>("/progress"),
  review: () => request<Array<{ id: number; word: VocabularyWord }>>("/review"),
  entitlement: () => request<{ plan: string; active: boolean; purchase_enabled: boolean }>("/entitlement"),
  createSession: (scenario_id: string) => request<{ id: string }>("/sessions", { method: "POST", body: JSON.stringify({ scenario_id }) }),
  sendTurn: (sessionId: string, transcript: string) => request<TutorTurn>(`/sessions/${sessionId}/turns`, { method: "POST", body: JSON.stringify({ transcript, audio_duration_seconds: 0 }) }),
  saveWord: (word: VocabularyWord) => request<{ id: number; created: boolean }>("/words", { method: "POST", body: JSON.stringify(word) }),
  gradeReview: (id: number, rating: number) => request(`/review/${id}`, { method: "POST", body: JSON.stringify({ rating }) })
};
