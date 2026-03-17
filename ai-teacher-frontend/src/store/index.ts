import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Student, Course, KnowledgePoint, Message, SessionResponse, ProgressResponse, WhiteboardContent } from '../types';

interface AuthState {
  token: string | null;
  user: Student | null;
  setAuth: (token: string, user: Student) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => {
        set({ token: null, user: null });
        localStorage.removeItem('token');
      },
      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'auth-storage',
    }
  )
);

interface CourseState {
  currentCourse: Course | null;
  knowledgePoints: KnowledgePoint[];
  setCurrentCourse: (course: Course) => void;
  setKnowledgePoints: (kps: KnowledgePoint[]) => void;
}

export const useCourseStore = create<CourseState>()((set) => ({
  currentCourse: null,
  knowledgePoints: [],
  setCurrentCourse: (course) => set({ currentCourse: course }),
  setKnowledgePoints: (kps) => set({ knowledgePoints: kps }),
}));

interface LearningState {
  session: SessionResponse | null;
  currentKp: KnowledgePoint | null;
  progress: ProgressResponse | null;
  messages: Message[];
  isLoading: boolean;
  isAssessmentMode: boolean;
  assessmentQuestions: { id: string; content: string; options: string[] }[];
  whiteboardBlocks: WhiteboardContent[];
  
  setSession: (session: SessionResponse | null) => void;
  setCurrentKp: (kp: KnowledgePoint | null) => void;
  setProgress: (progress: ProgressResponse) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setLoading: (loading: boolean) => void;
  setAssessmentMode: (mode: boolean) => void;
  setAssessmentQuestions: (questions: { id: string; content: string; options: string[] }[]) => void;
  addWhiteboardBlock: (block: WhiteboardContent) => void;
  clearWhiteboard: () => void;
  reset: () => void;
}

const initialLearningState = {
  session: null,
  currentKp: null,
  progress: null,
  messages: [],
  isLoading: false,
  isAssessmentMode: false,
  assessmentQuestions: [],
  whiteboardBlocks: [],
};

export const useLearningStore = create<LearningState>()((set) => ({
  ...initialLearningState,
  setSession: (session) => set({ session }),
  setCurrentKp: (kp) => set({ currentKp: kp }),
  setProgress: (progress) => set({ progress }),
  addMessage: (message) => set((state) => {
    // 避免添加重复消息（React StrictMode 双重调用问题）
    if (state.messages.some(m => m.id === message.id)) {
      return state;
    }
    return { messages: [...state.messages, message] };
  }),
  setMessages: (messages) => set({ messages }),
  setLoading: (loading) => set({ isLoading: loading }),
  setAssessmentMode: (mode) => set({ isAssessmentMode: mode }),
  setAssessmentQuestions: (questions) => set({ assessmentQuestions: questions }),
  addWhiteboardBlock: (block) => set((state) => {
    // 检查是否有实际内容需要添加
    const hasContent = block.title || 
      (block.key_points && block.key_points.length > 0) ||
      (block.formulas && block.formulas.length > 0) ||
      (block.examples && block.examples.length > 0) ||
      (block.notes && block.notes.length > 0);
    if (!hasContent) {
      return state;
    }
    return { whiteboardBlocks: [...state.whiteboardBlocks, block] };
  }),
  clearWhiteboard: () => set({ whiteboardBlocks: [] }),
  reset: () => set(initialLearningState),
}));
