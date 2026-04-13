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
  WhiteboardContent,
  StartImprovementRequest,
  ImprovementSession,
  ImprovementQuiz,
  ImprovementQuizResult,
} from '../types';

// SSE事件类型（增量事件）
export type StreamEventType = 
  // 边讲边写模式
  | 'segment'
  // 白板增量事件
  | 'wb_title'
  | 'wb_points'
  | 'wb_formulas'
  | 'wb_examples'
  | 'wb_notes'
  // 消息事件
  | 'msg_intro'
  | 'msg_def'
  | 'msg_example'
  | 'msg_summary'
  | 'msg_question'
  | 'msg_feedback'
  | 'msg_encourage'
  | 'msg_supplement'
  // 工具增强事件（v2新增）
  | 'tool_call'
  | 'tool_result'
  // 控制事件
  | 'whiteboard'
  | 'complete'
  | 'error';

// 白板片段数据
export interface WhiteboardSegment {
  title?: string;
  points?: string[];
  formulas?: string[];
  examples?: string[];
  notes?: string[];
}

// segment事件数据
export interface SegmentData {
  message: string;
  whiteboard: WhiteboardSegment;
  is_question?: boolean;
  // 工具增强字段（v2新增）
  image_id?: string;
  video_id?: string;
  demo_id?: string;
}

// 工具调用数据（v2新增）
export interface ToolCallData {
  tool_name: string;
  action: string;
  params: Record<string, any>;
}

// 工具结果数据（v2新增）
export interface ToolResultData {
  tool_name: string;
  success: boolean;
  message?: string;
  image_id?: string;
  video_id?: string;
  demo_id?: string;
}

// 教学图片数据（v2新增）
export interface TeachingImageData {
  id: string;
  title: string;
  description: string;
  url: string;
  thumbnail_url?: string;
  knowledge_point_id: string;
  image_type: string;
  tags: string[];
}

export interface StreamCallbacks {
  // 边讲边写模式（同时处理消息和白板）
  onSegment?: (data: SegmentData) => void;
  // 白板增量事件
  onWbTitle?: (content: string) => void;
  onWbPoints?: (content: string) => void;
  onWbFormulas?: (content: string) => void;
  onWbExamples?: (content: string) => void;
  onWbNotes?: (content: string) => void;
  // 消息事件
  onMsgIntro?: (content: string) => void;
  onMsgDef?: (content: string) => void;
  onMsgExample?: (content: string) => void;
  onMsgSummary?: (content: string) => void;
  onMsgQuestion?: (content: string) => void;
  onMsgFeedback?: (content: string) => void;
  onMsgEncourage?: (content: string) => void;
  onMsgSupplement?: (content: string) => void;
  // 工具增强事件（v2新增）
  onToolCall?: (data: ToolCallData) => void;
  onToolResult?: (data: ToolResultData) => void;
  // 控制事件
  onWhiteboard?: (whiteboard: WhiteboardContent) => void;
  onComplete?: (nextAction: string) => void;
  onError?: (error: string) => void;
  // 阶段推进事件
  onPhaseAdvance?: (data: { current_phase: number; total_phases: number; next_action: string }) => void;
}

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

  // 流式获取教学内容（增量事件）
  streamTeachingContent: async (sessionId: string, callbacks: StreamCallbacks) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/v1/learning/session/${sessionId}/stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      callbacks.onError?.('无法读取响应流');
      return;
    }

    let currentEvent: string = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim();
            try {
              const data = JSON.parse(dataStr);
              
              // 处理增量事件
              switch (currentEvent) {
                case 'segment':
                  // 边讲边写模式：同时处理消息和白板
                  callbacks.onSegment?.(data);
                  break;
                case 'wb_title':
                  callbacks.onWbTitle?.(data.content);
                  break;
                case 'wb_points':
                  callbacks.onWbPoints?.(data.content);
                  break;
                case 'wb_formulas':
                  callbacks.onWbFormulas?.(data.content);
                  break;
                case 'wb_examples':
                  callbacks.onWbExamples?.(data.content);
                  break;
                case 'wb_notes':
                  callbacks.onWbNotes?.(data.content);
                  break;
                case 'msg_intro':
                  callbacks.onMsgIntro?.(data.content);
                  break;
                case 'msg_def':
                  callbacks.onMsgDef?.(data.content);
                  break;
                case 'msg_example':
                  callbacks.onMsgExample?.(data.content);
                  break;
                case 'msg_summary':
                  callbacks.onMsgSummary?.(data.content);
                  break;
                case 'msg_question':
                  callbacks.onMsgQuestion?.(data.content);
                  break;
                case 'msg_feedback':
                  callbacks.onMsgFeedback?.(data.content);
                  break;
                case 'msg_encourage':
                  callbacks.onMsgEncourage?.(data.content);
                  break;
                case 'msg_supplement':
                  callbacks.onMsgSupplement?.(data.content);
                  break;
                case 'whiteboard':
                  callbacks.onWhiteboard?.(data);
                  break;
                case 'complete':
                  callbacks.onComplete?.(data.next_action || 'wait_for_student');
                  break;
                case 'error':
                  callbacks.onError?.(data.error || '未知错误');
                  break;
              }
            } catch (e) {
              // 解析失败，忽略
            }
          }
        }
      }
    } catch (error) {
      callbacks.onError?.(error instanceof Error ? error.message : '流式读取错误');
    }
  },

  sendMessage: (sessionId: string, data: ChatRequest) =>
    api.post<ApiResponse<ChatResponse>>(`/learning/session/${sessionId}/chat`, data),

  // 流式发送消息（增量事件）
  streamSendMessage: async (sessionId: string, message: string, callbacks: StreamCallbacks) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/v1/learning/session/${sessionId}/stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      callbacks.onError?.('无法读取响应流');
      return;
    }

    let currentEvent: string = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim();
            try {
              const data = JSON.parse(dataStr);
              
              // 处理增量事件
              switch (currentEvent) {
                case 'wb_formulas':
                  callbacks.onWbFormulas?.(data.content);
                  break;
                case 'msg_feedback':
                  callbacks.onMsgFeedback?.(data.content);
                  break;
                case 'msg_encourage':
                  callbacks.onMsgEncourage?.(data.content);
                  break;
                case 'msg_supplement':
                  callbacks.onMsgSupplement?.(data.content);
                  break;
                case 'phase_advance':
                  callbacks.onPhaseAdvance?.(data);
                  break;
                case 'complete':
                  callbacks.onComplete?.(data.next_action || 'wait_for_student');
                  break;
                case 'error':
                  callbacks.onError?.(data.error || '未知错误');
                  break;
              }
            } catch (e) {
              // 解析失败，忽略
            }
          }
        }
      }
    } catch (error) {
      callbacks.onError?.(error instanceof Error ? error.message : '流式读取错误');
    }
  },

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

  // 教学阶段相关
  getPhase: (sessionId: string) =>
    api.get<ApiResponse<{
      teaching_mode: string;
      current_phase: number;
      total_phases: number;
      phase_status: string;
      phase_info: {
        name: string;
        description: string;
        activities: string[];
      } | null;
    }>>(`/learning/session/${sessionId}/phase`),

  advancePhase: (sessionId: string) =>
    api.post<ApiResponse<{
      current_phase: number;
      total_phases: number;
      is_last_phase: boolean;
    }>>(`/learning/session/${sessionId}/phase/next`),
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
};

// 对话推荐API
export interface ChatRecommendRequest {
  message: string;
  session_id?: string;
  student_id?: number;
}

export interface ChatRecommendResponse {
  reply: string;
  is_ready: boolean;
  recommended_kp: string | null;
  recommended_kp_name: string | null;
  session_id: string;
}

export const chatApi = {
  recommend: (data: ChatRecommendRequest) =>
    api.post<ApiResponse<ChatRecommendResponse>>('/chat/recommend', data),
};

// 教学V2 API - 工具增强版（v2新增）
export const teachingV2Api = {
  // 流式获取教学内容（工具增强版）
  streamTeachingContent: async (sessionId: string, useTools: boolean, callbacks: StreamCallbacks) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/v1/teaching-v2/session/${sessionId}/teach-v2?use_tools=${useTools}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      callbacks.onError?.('无法读取响应流');
      return;
    }

    let currentEvent: string = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim();
            try {
              const data = JSON.parse(dataStr);
              
              // 处理增量事件
              switch (currentEvent) {
                case 'segment':
                  callbacks.onSegment?.(data);
                  break;
                case 'wb_title':
                  callbacks.onWbTitle?.(data.content);
                  break;
                case 'wb_points':
                  callbacks.onWbPoints?.(data.content);
                  break;
                case 'wb_formulas':
                  callbacks.onWbFormulas?.(data.content);
                  break;
                case 'wb_examples':
                  callbacks.onWbExamples?.(data.content);
                  break;
                case 'wb_notes':
                  callbacks.onWbNotes?.(data.content);
                  break;
                case 'msg_intro':
                  callbacks.onMsgIntro?.(data.content);
                  break;
                case 'msg_def':
                  callbacks.onMsgDef?.(data.content);
                  break;
                case 'msg_example':
                  callbacks.onMsgExample?.(data.content);
                  break;
                case 'msg_summary':
                  callbacks.onMsgSummary?.(data.content);
                  break;
                case 'msg_question':
                  callbacks.onMsgQuestion?.(data.content);
                  break;
                case 'msg_feedback':
                  callbacks.onMsgFeedback?.(data.content);
                  break;
                case 'msg_encourage':
                  callbacks.onMsgEncourage?.(data.content);
                  break;
                case 'msg_supplement':
                  callbacks.onMsgSupplement?.(data.content);
                  break;
                case 'tool_call':
                  callbacks.onToolCall?.(data);
                  break;
                case 'tool_result':
                  callbacks.onToolResult?.(data);
                  break;
                case 'whiteboard':
                  callbacks.onWhiteboard?.(data);
                  break;
                case 'phase_advance':
                  callbacks.onPhaseAdvance?.(data);
                  break;
                case 'complete':
                  callbacks.onComplete?.(data.next_action || 'wait_for_student');
                  break;
                case 'error':
                  callbacks.onError?.(data.error || '未知错误');
                  break;
              }
            } catch (e) {
              // 解析失败，忽略
            }
          }
        }
      }
    } catch (error) {
      callbacks.onError?.(error instanceof Error ? error.message : '流式读取错误');
    }
  },

  // 查看可用工具
  getAvailableTools: (sessionId: string) =>
    api.get<ApiResponse<{ tools: string[]; session_id: string; knowledge_point: string }>>(`/teaching-v2/session/${sessionId}/tools/available`),

  // 获取图片
  getImage: (imageId: string) =>
    api.get<ApiResponse<TeachingImageData>>(`/teaching-v2/images/${imageId}`),

  // 生成图片
  generateImage: (params: { concept: string; type: string; knowledge_point_id: string }) =>
    api.post<ApiResponse<TeachingImageData & { source: string; cost: number }>>('/teaching-v2/images/generate', params),
};
