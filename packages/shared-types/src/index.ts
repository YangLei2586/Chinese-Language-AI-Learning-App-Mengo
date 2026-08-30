export type Level = "beginner" | "elementary" | "intermediate";

export interface LearnerProfile {
  goal: string;
  level: Level;
  minutes_per_day: number;
  onboarding_complete: boolean;
}

export interface VocabularyWord {
  hanzi: string;
  pinyin: string;
  english: string;
}

export interface Scenario {
  id: string;
  title: string;
  title_zh: string;
  category: string;
  level: Level;
  duration_minutes: number;
  prompt: string;
  vocabulary: VocabularyWord[];
}

export interface LessonSession {
  id: string;
  scenario_id: string;
  status: "active" | "completed";
  turn_count: number;
  created_at: string;
}

export interface TutorFeedback {
  grammar: string;
  vocabulary: string;
  tones: string;
  pronunciation_score: number;
}

export interface TutorTurn {
  learner_transcript: string;
  tutor_response: string;
  tutor_pinyin: string;
  feedback: TutorFeedback;
  session_completed: boolean;
}

export interface Progress {
  completed_lessons: number;
  total_minutes: number;
  current_streak: number;
  last_activity_date: string | null;
}
