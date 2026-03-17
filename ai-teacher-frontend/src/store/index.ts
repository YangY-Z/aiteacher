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

interface WhiteboardState {
  title: string;
  key_points: string[];
  formulas: string[];
  examples: string[];
  notes: string[];
}

interface LearningState {
  session: SessionResponse | null;
  currentKp: KnowledgePoint | null;
  progress: ProgressResponse | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  isAssessmentMode: boolean;
  assessmentQuestions: { id: string; content: string; options: string[] }[];
  whiteboardBlocks: WhiteboardContent[];
  // 新增：当前白板状态（用于增量更新）
  currentWhiteboard: WhiteboardState;
  streamingMessageId: string | null;
  
  setSession: (session: SessionResponse | null) => void;
  setCurrentKp: (kp: KnowledgePoint | null) => void;
  setProgress: (progress: ProgressResponse) => void;
  addMessage: (message: Message) => void;
  updateStreamingMessage: (id: string, content: string) => void;
  finishStreamingMessage: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setAssessmentMode: (mode: boolean) => void;
  setAssessmentQuestions: (questions: { id: string; content: string; options: string[] }[]) => void;
  addWhiteboardBlock: (block: WhiteboardContent) => void;
  updateLastWhiteboardBlock: (block: Partial<WhiteboardContent>) => void;
  clearWhiteboard: () => void;
  // 新增：增量更新方法
  setWhiteboardTitle: (title: string) => void;
  addWhiteboardPoint: (point: string) => void;
  addWhiteboardFormula: (formula: string) => void;
  addWhiteboardExample: (example: string) => void;
  addWhiteboardNote: (note: string) => void;
  commitWhiteboard: () => void;
  reset: () => void;
}

const initialWhiteboardState: WhiteboardState = {
  title: '',
  key_points: [],
  formulas: [],
  examples: [],
  notes: [],
};

const initialLearningState = {
  session: null,
  currentKp: null,
  progress: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  isAssessmentMode: false,
  assessmentQuestions: [],
  whiteboardBlocks: [],
  currentWhiteboard: initialWhiteboardState,
  streamingMessageId: null,
};

export const useLearningStore = create<LearningState>()((set) => ({
  ...initialLearningState,
  setSession: (session) => set({ session }),
  setCurrentKp: (kp) => set({ currentKp: kp }),
  setProgress: (progress) => set({ progress }),
  addMessage: (message) => set((state) => {
    // 避免添加重复消息（React StrictMode 双重调用问题）
    // 检查ID重复
    if (state.messages.some(m => m.id === message.id)) {
      return state;
    }
    // 检查最近一条消息是否内容相同（防止快速连续添加相同内容）
    const lastMessage = state.messages[state.messages.length - 1];
    if (lastMessage && 
        lastMessage.role === message.role && 
        lastMessage.content === message.content &&
        Date.now() - lastMessage.timestamp.getTime() < 1000) {
      return state;
    }
    return { messages: [...state.messages, message] };
  }),
  updateStreamingMessage: (id, content) => set((state) => {
    const messages = state.messages.map(m => 
      m.id === id ? { ...m, content } : m
    );
    return { messages, streamingMessageId: id };
  }),
  finishStreamingMessage: (id) => set((state) => {
    if (state.streamingMessageId === id) {
      return { streamingMessageId: null, isStreaming: false };
    }
    return state;
  }),
  setMessages: (messages) => set({ messages }),
  setLoading: (loading) => set({ isLoading: loading }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
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
  updateLastWhiteboardBlock: (block) => set((state) => {
    if (state.whiteboardBlocks.length === 0) return state;
    const blocks = [...state.whiteboardBlocks];
    const lastBlock = blocks[blocks.length - 1];
    blocks[blocks.length - 1] = { ...lastBlock, ...block };
    return { whiteboardBlocks: blocks };
  }),
  clearWhiteboard: () => set({ 
    whiteboardBlocks: [],
    currentWhiteboard: initialWhiteboardState,
  }),
  // 增量更新方法
  setWhiteboardTitle: (title) => set((state) => ({
    currentWhiteboard: { ...state.currentWhiteboard, title },
  })),
  addWhiteboardPoint: (point) => set((state) => ({
    currentWhiteboard: {
      ...state.currentWhiteboard,
      key_points: [...state.currentWhiteboard.key_points, point],
    },
  })),
  addWhiteboardFormula: (formula) => set((state) => ({
    currentWhiteboard: {
      ...state.currentWhiteboard,
      formulas: [...state.currentWhiteboard.formulas, formula],
    },
  })),
  addWhiteboardExample: (example) => set((state) => ({
    currentWhiteboard: {
      ...state.currentWhiteboard,
      examples: [...state.currentWhiteboard.examples, example],
    },
  })),
  addWhiteboardNote: (note) => set((state) => ({
    currentWhiteboard: {
      ...state.currentWhiteboard,
      notes: [...state.currentWhiteboard.notes, note],
    },
  })),
  // 将当前白板状态提交到 whiteboardBlocks
  commitWhiteboard: () => set((state) => {
    const wb = state.currentWhiteboard;
    const hasContent = wb.title || 
      wb.key_points.length > 0 || 
      wb.formulas.length > 0 || 
      wb.examples.length > 0 || 
      wb.notes.length > 0;
    if (!hasContent) return state;
    
    // 检查是否已存在相同的白板块（避免重复）
    const existingBlock = state.whiteboardBlocks.find(b => b.title === wb.title);
    if (existingBlock) {
      // 更新现有块
      const blocks = state.whiteboardBlocks.map(b => 
        b.title === wb.title 
          ? { 
              ...b, 
              key_points: [...b.key_points, ...wb.key_points],
              formulas: [...b.formulas, ...wb.formulas],
              examples: [...b.examples, ...wb.examples],
              notes: [...b.notes, ...wb.notes],
            } 
          : b
      );
      return { whiteboardBlocks: blocks };
    }
    
    return { 
      whiteboardBlocks: [...state.whiteboardBlocks, {
        title: wb.title,
        key_points: wb.key_points,
        formulas: wb.formulas,
        examples: wb.examples,
        notes: wb.notes,
      }],
    };
  }),
  reset: () => set(initialLearningState),
}));
