export interface Edit {
  field: string;
  find?: string | null;
  replace: string;
}

export interface Result {
  reportId: string;
  questionId: string;
  verdict: string;
  repair?: string | null;
  edit?: Edit | null;
  route: string;
  confidence: number;
  evidence: string;
  student_reply: string;
}

export interface Report {
  reportId: string;
  questionId: string;
  studentId: string;
  source: string;
  reportedAt: string;
  comment: string;
}

export interface Question {
  _id: string;
  qid?: string | null;
  questionType: string;
  subject: string;
  chapter: string;
  concept?: string | null;
  subConcept?: string | null;
  level?: string | null;
  error?: number;
  updatedAt?: string;
  scq?: {
    question: string;
    solution: string;
    answer: string;
    quesImages?: string[];
    solutionImages?: string[];
  };
  integerQuestion?: {
    question: string;
    solution: string;
    answer: string;
    quesImages?: string[];
    solutionImages?: string[];
  };
  mcq?: {
    question: string;
    solution: string;
    answer: string | string[];
    quesImages?: string[];
    solutionImages?: string[];
  };
}

export interface QueueGroup {
  questionId: string;
  subject: string;
  chapter: string;
  questionType: string;
  question_preview: string;
  urgency_score: number;
  report_count: number;
  max_confidence: number;
  top_verdict: string;
  top_route: string;
  repairs: string[];
  reports: Report[];
  results: Result[];
}

export interface Metrics {
  total_reports: number;
  total_questions: number;
  defects_count: number;
  auto_apply_count: number;
  faculty_review_count: number;
  no_change_count: number;
  by_verdict: Record<string, number>;
  by_route: Record<string, number>;
  by_repair: Record<string, number>;
  by_subject: Record<string, number>;
}

export interface AuditEntry {
  id: number;
  report_id: string;
  question_id: string;
  action: string;
  faculty_name?: string | null;
  old_edit?: string | null;
  new_edit?: string | null;
  reason?: string | null;
  created_at: string;
}

export interface SingleResultDetail {
  result: Result;
  report: Report;
  question: Question;
  question_content: {
    question?: string;
    solution?: string;
    answer?: any;
    quesImages?: string[];
    solutionImages?: string[];
  };
  sibling_results: Result[];
}

