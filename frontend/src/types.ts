export type Subject = "history" | "physics" | "math" | "geography";

export type QuestionPublic = {
  id: string;
  external_id: string;
  topic: string;
  difficulty: "easy" | "medium" | "hard" | string;
  prompt: string;
  options: string[];
};

export type SubmitResult = {
  question_id: string;
  correct: boolean;
  correct_index: number;
  explanation: string;
};
