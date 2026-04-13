import type { QuestionPublic, Subject, SubmitResult } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost/api";

export async function fetchQuestions(subject: Subject): Promise<QuestionPublic[]> {
  const response = await fetch(`${API_BASE}/${subject}/v1/questions?limit=10`);
  if (!response.ok) {
    throw new Error(`Failed to load questions for ${subject}: HTTP ${response.status}`);
  }
  return response.json();
}

export async function submitAnswer(
  subject: Subject,
  questionId: string,
  selectedIndex: number,
): Promise<SubmitResult> {
  const response = await fetch(`${API_BASE}/${subject}/v1/questions/${questionId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_index: selectedIndex }),
  });
  if (!response.ok) {
    throw new Error(`Failed to submit answer: HTTP ${response.status}`);
  }
  return response.json();
}
