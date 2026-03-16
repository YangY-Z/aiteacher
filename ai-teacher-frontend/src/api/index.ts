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
