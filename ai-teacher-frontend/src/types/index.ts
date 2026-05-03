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
  level_descriptions?: Record<number, string>; // 层级描述，key 为层级编号
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

// 会话历史相关类型
export interface SessionListItem {
  session_id: string;
  course_id: string;
  kp_id: string | null;
  kp_name: string | null;
  status: string;
  current_round: number;
  rounds_count: number;
  total_messages: number;
  created_at: string | null;
}

export interface RoundMessage {
  role: string;
  content: string;
}

export interface SessionHistoryRound {
  round_number: number;
  status: string;
  start_time: string | null;
  end_time: string | null;
  messages: RoundMessage[];
  teaching_mode: string | null;
  assessment_result: Record<string, unknown> | null;
  summary: Record<string, unknown> | null;
}

export interface SessionHistoryResponse {
  session_id: string;
  course_id: string;
  kp_id: string | null;
  kp_name: string | null;
  status: string;
  created_at: string | null;
  current_round_index: number;
  rounds: SessionHistoryRound[];
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
  knowledge_points: KnowledgePointProgress[];  // 新增：详细知识点进度
}

// 知识点进度详情
export interface KnowledgePointProgress {
  id: string;
  name: string;
  type: string;
  level: number;
  status: 'locked' | 'in_progress' | 'current' | 'completed' | 'skipped';
  progress: number;  // 0-100
  dependencies: string[];
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

// 媒体资源信息
export interface MediaResource {
  id?: string;
  type: 'image' | 'video';
  url: string;
  thumbnail_url?: string;
  title?: string;
  description?: string;
  source?: string;
  duration?: number;
  cached?: boolean;
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
  image?: MediaResource;
  video?: MediaResource;
}

export interface QuestionContent {
  id: string;
  content: string;
  options: string[];
  selected?: string;
}

// ============ 专项突破相关类型 ============

// 成绩上传请求
export interface ScoreUploadRequest {
  exam_name: string;
  score: number;
  total_score: number;
  error_description?: string;
  available_time: number;
  difficulty: 'basic' | 'normal' | 'challenge';
  foundation: 'weak' | 'average' | 'good';
  max_clarification_rounds: number;
}

// 开始专项突破请求
export interface StartImprovementRequest {
  course_id: string;
  score_input: ScoreUploadRequest;
}

// 澄清轮次
export interface ClarificationRound {
  round_number: number;
  system_question: string;
  student_answer?: string | null;
  created_at: string;
  answered_at?: string | null;
}

// 诊断结果
export interface DiagnosisResponse {
  target_knowledge_point_id: string;
  target_kp_name: string;
  confidence: number;
  reason: string;
  prerequisite_gaps: string[];
}

// 学习方案步骤
export interface ImprovementPlanStep {
  step_order: number;
  knowledge_point_id: string;
  kp_name: string;
  goal: string;
  estimated_minutes: number;
  is_completed: boolean;
}

// 学习方案
export interface ImprovementPlan {
  plan_id: string;
  target_kp_id: string;
  target_kp_name: string;
  steps: ImprovementPlanStep[];
  total_estimated_minutes: number;
}

// 专项突破会话
export interface ImprovementSession {
  session_id: string;
  student_id: string;
  course_id: string;
  status: string;
  max_clarification_rounds: number;
  score_input?: Record<string, unknown> | null;
  clarification_rounds: ClarificationRound[];
  diagnosis?: DiagnosisResponse | null;
  plan?: ImprovementPlan | null;
  current_step_order: number;
  created_at: string;
  updated_at: string;
}

// 小测问题
export interface QuizQuestion {
  id: string;
  type: string;
  content: string;
  options?: string[] | null;
  difficulty: string;
}

// 小测
export interface ImprovementQuiz {
  quiz_id: string;
  target_kp_id: string;
  questions: QuizQuestion[];
}

// 小测结果
export interface ImprovementQuizResult {
  quiz_id: string;
  score: number;
  passed: boolean;
  feedback: string;
}
