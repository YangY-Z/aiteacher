import api from './client';
import type {
  ApiResponse,
  Student,
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  Course,
  KnowledgePoint,
  SessionResponse,
  StartSessionRequest,
  ChatRequest,
  ChatResponse,
  AssessmentQuestion,
  AssessmentRequest,
  AssessmentResponse,
  ProgressResponse,
  BacktrackDecision,
  StartImprovementRequest,
  ImprovementSession,
  ImprovementQuiz,
  ImprovementQuizResult,
} from '../types';

// 认证API
export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<ApiResponse<Student>>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<ApiResponse<AuthResponse>>('/auth/login', data),

  getProfile: () =>
    api.get<ApiResponse<Student>>('/students/me'),
};

// 课程API
export const courseApi = {
  getAll: () =>
    api.get<ApiResponse<Course[]>>('/courses'),

  getById: (courseId: string) =>
    api.get<ApiResponse<Course>>(`/courses/${courseId}`),

  getKnowledgePoints: (courseId: string) =>
    api.get<ApiResponse<KnowledgePoint[]>>(`/courses/${courseId}/knowledge-points`),

  getKnowledgePoint: (courseId: string, kpId: string) =>
    api.get<ApiResponse<KnowledgePoint>>(`/courses/${courseId}/knowledge-points/${kpId}`),
};

// 学习API
export const learningApi = {
  startSession: (data: StartSessionRequest) =>
    api.post<ApiResponse<SessionResponse>>('/learning/start', data),

  getSession: (sessionId: string) =>
    api.get<ApiResponse<SessionResponse>>(`/learning/session/${sessionId}`),

  getTeachingContent: (sessionId: string) =>
    api.post<ApiResponse<ChatResponse>>(`/learning/session/${sessionId}/teach`),

  sendMessage: (sessionId: string, data: ChatRequest) =>
    api.post<ApiResponse<ChatResponse>>(`/learning/session/${sessionId}/chat`, data),

  getAssessment: (sessionId: string) =>
    api.get<ApiResponse<{ kp_id: string; questions: AssessmentQuestion[] }>>(`/learning/session/${sessionId}/assessment`),

  submitAssessment: (sessionId: string, data: AssessmentRequest) =>
    api.post<ApiResponse<AssessmentResponse>>(`/learning/session/${sessionId}/assessment`, data),

  skipKnowledgePoint: (sessionId: string, reason?: string) =>
    api.post<ApiResponse<{ skipped_kp_id: string; next_kp_id: string | null }>>(`/learning/session/${sessionId}/skip`, { reason }),

  completeKnowledgePoint: (sessionId: string) =>
    api.post<ApiResponse<{ completed_kp_id: string; next_kp_id: string | null; next_kp_name: string | null }>>(`/learning/session/${sessionId}/complete`),

  backtrack: (sessionId: string) =>
    api.post<ApiResponse<BacktrackDecision>>(`/learning/session/${sessionId}/backtrack`),

  getProgress: (courseId: string) =>
    api.get<ApiResponse<ProgressResponse>>(`/learning/progress/${courseId}`),
};

// 专项提升API
export const improvementApi = {
  startSession: (data: StartImprovementRequest) =>
    api.post<ApiResponse<ImprovementSession>>('/improvement/start', data),

  getSession: (sessionId: string) =>
    api.get<ApiResponse<ImprovementSession>>(`/improvement/session/${sessionId}`),

  submitClarification: (sessionId: string, answer: string) =>
    api.post<ApiResponse<ImprovementSession>>(`/improvement/session/${sessionId}/clarify`, { answer }),

  generatePlan: (sessionId: string) =>
    api.post<ApiResponse<ImprovementSession>>(`/improvement/session/${sessionId}/plan`, { confirm_diagnosis: true }),

  startStep: (sessionId: string, stepOrder: number) =>
    api.post<ApiResponse<Record<string, unknown>>>(`/improvement/session/${sessionId}/step/${stepOrder}/start`),

  completeStep: (sessionId: string, stepOrder: number, notes?: string) =>
    api.post<ApiResponse<ImprovementSession>>(`/improvement/session/${sessionId}/step/${stepOrder}/complete`, { notes }),

  getQuiz: (sessionId: string) =>
    api.get<ApiResponse<ImprovementQuiz>>(`/improvement/session/${sessionId}/quiz`),

  submitQuiz: (sessionId: string, answers: { question_id: string; answer: string }[]) =>
    api.post<ApiResponse<ImprovementQuizResult>>(`/improvement/session/${sessionId}/quiz`, { answers }),

  // Agent 模式
  runAgent: (data: StartImprovementRequest) =>
    api.post<ApiResponse<ImprovementSession>>('/improvement/agent/run', data),
};
