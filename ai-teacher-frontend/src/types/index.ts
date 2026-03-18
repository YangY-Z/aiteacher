// API响应类型
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string | null;
  meta?: unknown;
}

// 用户相关
export interface Student {
  id: number;
  name: string;
  grade: string;
  phone: string;
  avatar_url: string | null;
  status: string;
  created_at: string;
}

export interface LoginRequest {
  phone: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  grade: string;
  phone: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  student_id: number;
  student_name: string;
}

// 课程相关
export interface KnowledgePoint {
  id: string;
  course_id: string;
  name: string;
  type: string;
  description: string | null;
  level: number;
  sort_order: number;
  key_points: string[];
  mastery_criteria: MasteryCriteria | null;
  teaching_config: TeachingConfig | null;
  dependencies: string[];
  created_at: string;
}

export interface MasteryCriteria {
  type: string;
  method: string;
  question_count: number;
  pass_threshold: number;
}

export interface TeachingConfig {
  use_examples: boolean;
  ask_questions: boolean;
  question_positions: string[];
}

export interface Course {
  id: string;
  name: string;
  grade: string;
  subject: string;
  description: string | null;
  total_knowledge_points: number;
  estimated_hours: number | null;
  status: string;
  knowledge_points: KnowledgePoint[];
  created_at: string;
}

// 学习会话
export interface StartSessionRequest {
  course_id: string;
  kp_id?: string;
}

export interface SessionResponse {
  session_id: string;
  course_id: string;
  kp_id: string | null;
  status: string;
}

// 聊天
export interface ChatRequest {
  message: string;
  input_type?: string;
}

export interface ChatResponse {
  response_type: string;
  content: Record<string, unknown>;
  whiteboard: WhiteboardContent;
  next_action: string;
}

export interface WhiteboardContent {
  title?: string;
  key_points?: string[];
  formulas?: string[];
  examples?: string[];
  notes?: string[];
  // 兼容旧格式
  diagrams?: string[];
}

// 评估
export interface AssessmentQuestion {
  id: string;
  type: string;
  content: string;
  options: string[];
  difficulty: string;
}

export interface AssessmentRequest {
  answers: Answer[];
}

export interface Answer {
  question_id: string;
  answer: string;
}

export interface AssessmentResponse {
  result: string;
  score: number;
  correct_count: number;
  total_questions: number;
  passed: boolean;
  next_kp_id: string | null;
  next_kp_name: string | null;
  backtrack_required: boolean;
}

// 学习进度
export interface ProgressResponse {
  student_id: number;
  course_id: string;
  current_kp_id: string | null;
  current_kp_name: string | null;
  completed_count: number;
  mastered_count: number;
  skipped_count: number;
  total_count: number;
  mastery_rate: number;
  total_time: number;
  session_count: number;
  last_session_at: string | null;
}

// 回溯
export interface BacktrackDecision {
  decision: 'backtrack' | 'continue';
  reason: string;
  backtrack_target?: {
    knowledge_point_id: string;
    knowledge_point_name: string;
  };
  error_root_cause?: string;
  teaching_adjustment?: string;
  remedial_content?: RemedialContent;
}

export interface RemedialContent {
  introduction: string;
  review_content: string;
  examples: string[];
  practice_questions: string[];
}

// 聊天消息
export interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  type?: 'text' | 'question' | 'teacher_question' | 'feedback';
  question?: QuestionContent;
  isTyping?: boolean; // 是否正在打字中
}

export interface QuestionContent {
  id: string;
  content: string;
  options: string[];
  selected?: string;
}
