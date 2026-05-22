import React, { useState, useEffect, useRef, useCallback } from 'react';
import Button from 'antd/es/button';
import message from 'antd/es/message';
import Drawer from 'antd/es/drawer';
import Tag from 'antd/es/tag';
import Empty from 'antd/es/empty';
import { LogoutOutlined, ArrowLeftOutlined, ToolOutlined, HistoryOutlined, CloseOutlined, PlusOutlined, AudioOutlined, SoundOutlined, StopOutlined, PauseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import 'katex/dist/katex.min.css';
import Whiteboard from '../components/whiteboard/Whiteboard';
import WhiteboardHTML from '../components/whiteboard/WhiteboardHTML';
import TeachingImage from '../components/teaching/TeachingImage';
import MarkdownContent from '../components/MarkdownContent';
import { InteractiveWhiteboard } from '../components/interactive';
import type { InteractiveTask, AIFeedback } from '../components/interactive/types';
import { useAuthStore, useLearningStore } from '../store';
import { useBrowserVoice } from '../hooks/useBrowserVoice';
import type { SessionListItem, SessionHistoryResponse, WhiteboardContent, WhiteboardImage } from '../types';
import './MinimalLearning.css';

type LearningPhase = 'explain' | 'question' | 'interactive' | 'feedback' | 'assessment';

interface Question {
  id: string;
  type: string;
  content: string;
  options?: string[];
  difficulty?: string;
  correct_answer?: string | string[];
  explanation?: string;
}

interface QuestionResult {
  question_id: string;
  content: string;
  type: string;
  options?: string[];
  student_answer: string;
  correct_answer: string | string[];
  is_correct: boolean;
  explanation?: string;
}

interface MediaResource {
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

interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  phase?: LearningPhase;
  question?: Question;
  questionResults?: QuestionResult[];  // 评估结果
  imageId?: string;  // 工具增强：图片ID（兼容旧版）
  image?: MediaResource;  // 完整图片资源
  video?: MediaResource;  // 完整视频资源
}

interface LearningState {
  currentTopic: string;
  currentKpId: string | null;
  phase: LearningPhase;
  currentPhase: number;
  totalPhases: number;
  messages: Message[];
  isStreaming: boolean;
  sessionId: string | null;
  isFirstInput: boolean;  // 是否是首次输入（欢迎语后的确认）
  // 评估相关
  assessmentQuestions: Question[];
  currentQuestionIndex: number;
  selectedAnswers: Record<string, string>;
  // 工具增强相关
  useTools: boolean;  // 是否启用工具增强
  // 互动白板相关
  interactiveTask: InteractiveTask | null;
  aiDrawingFeedback: AIFeedback | null;
  showInteractivePanel: boolean;
  isSubmittingDrawing: boolean;
}

// 渲染带有公式 + Markdown 格式的内容 — 改用 MarkdownContent 组件

/** 转义 HTML 特殊字符，防止 XSS 和格式错乱 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

const getWhiteboardStorageKey = (sessionId: string) => `learning_whiteboard:${sessionId}`;

interface WhiteboardSnapshot {
  version: 1;
  whiteboardBlocks: WhiteboardContent[];
  currentWhiteboard: {
    title: string;
    key_points: string[];
    formulas: string[];
    examples: string[];
    notes: string[];
    image: WhiteboardImage | null;
    html: string;
  };
  whiteboardMode: 'hidden' | 'mini' | 'expanded';
}

const emptyWhiteboardSnapshot = (): Omit<WhiteboardSnapshot, 'version' | 'whiteboardMode'> => ({
  whiteboardBlocks: [],
  currentWhiteboard: {
    title: '',
    key_points: [],
    formulas: [],
    examples: [],
    notes: [],
    image: null,
    html: '',
  },
});

const loadWhiteboardSnapshot = (sessionId: string): WhiteboardSnapshot | null => {
  try {
    const raw = localStorage.getItem(getWhiteboardStorageKey(sessionId));
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.whiteboardBlocks)) return null;

    return {
      version: 1,
      whiteboardBlocks: parsed.whiteboardBlocks,
      currentWhiteboard: {
        ...emptyWhiteboardSnapshot().currentWhiteboard,
        ...(parsed.currentWhiteboard || {}),
      },
      whiteboardMode: parsed.whiteboardMode || 'hidden',
    };
  } catch (error) {
    console.warn('恢复白板快照失败:', error);
    return null;
  }
};

const MinimalLearning: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlKpId = searchParams.get('kp_id');
  const urlKpName = searchParams.get('kp_name');
  const { user, logout, token } = useAuthStore();
  const { 
    mergeCurrentWhiteboard,
    setWhiteboardTitle, 
    addWhiteboardPoint, 
    addWhiteboardFormula, 
    addWhiteboardExample, 
    addWhiteboardNote,
    setWhiteboardImage,
    commitWhiteboard,
    setWhiteboardSnapshot,
    clearWhiteboard,
    whiteboardBlocks,
    currentWhiteboard,
    whiteboardMode,
  } = useLearningStore();
  
  const [state, setState] = useState<LearningState>({
    currentTopic: urlKpName || '一次函数',
    currentKpId: null,
    phase: 'explain',
    currentPhase: 1,
    totalPhases: 4,
    messages: [{
      id: 'welcome-msg',
      role: 'ai',
      content: '你好！我是你的AI老师。今天我们来学习"一次函数"。准备好了吗？输入任何内容开始学习。',
      timestamp: new Date(),
      phase: 'explain',
    }],
    isStreaming: false,
    sessionId: null,
    isFirstInput: true,  // 首次输入标记
    assessmentQuestions: [],
    currentQuestionIndex: 0,
    selectedAnswers: {},
    useTools: true,  // 默认启用工具增强
    interactiveTask: null,
    aiDrawingFeedback: null,
    showInteractivePanel: false,
    isSubmittingDrawing: false,
  });
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const restoringWhiteboardSessionRef = useRef<string | null>(null);
  const pendingWhiteboardAnswerRef = useRef<string | null>(null);

  // 消息队列和显示控制
  const messageQueueRef = useRef<Array<{content: string, phase: LearningPhase, imageId?: string, image?: MediaResource, video?: MediaResource}>>([]);
  const isDisplayingRef = useRef(false);

  // 防止评估接口重复调用
  const isLoadingAssessmentRef = useRef(false);

  // 右侧交流输入状态
  const [inputText, setInputText] = useState('');
  const [interactivePanelMounted, setInteractivePanelMounted] = useState(false);
  const [interactivePanelVisible, setInteractivePanelVisible] = useState(false);
  const chatPanelRef = useRef<HTMLDivElement>(null);
  const voice = useBrowserVoice();
  const voiceAutoReadRef = useRef(voice.autoRead);
  const voiceSpeakRef = useRef(voice.speak);

  useEffect(() => {
    voiceAutoReadRef.current = voice.autoRead;
    voiceSpeakRef.current = voice.speak;
  }, [voice.autoRead, voice.speak]);

  // 历史会话相关状态
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sessionList, setSessionList] = useState<SessionListItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);

  const getAuthHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token || localStorage.getItem('token')}`,
  }), [token]);

  const handleLogout = () => {
    logout();
    localStorage.removeItem('learning_session_id');
    window.location.href = '/login';
  };

  // 保存 sessionId 到 localStorage
  const saveSessionId = useCallback((sessionId: string) => {
    localStorage.setItem('learning_session_id', sessionId);
  }, []);

  // 当前会话的白板内容按 sessionId 持久化，刷新后能恢复同一块白板
  useEffect(() => {
    if (!state.sessionId) return;
    if (restoringWhiteboardSessionRef.current) {
      if (restoringWhiteboardSessionRef.current !== state.sessionId) return;
      restoringWhiteboardSessionRef.current = null;
    }

    const snapshot: WhiteboardSnapshot = {
      version: 1,
      whiteboardBlocks,
      currentWhiteboard,
      whiteboardMode,
    };

    localStorage.setItem(getWhiteboardStorageKey(state.sessionId), JSON.stringify(snapshot));
  }, [state.sessionId, whiteboardBlocks, currentWhiteboard, whiteboardMode]);

  // 从 localStorage 恢复会话
  const restoreSession = useCallback(async (sessionId: string) => {
    setIsRestoring(true);
    try {
      const res = await fetch(`/api/v1/learning/session/${sessionId}/history`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!res.ok) {
        localStorage.removeItem('learning_session_id');
        return;
      }

      const data = await res.json();

      if (data.success && data.data) {
        const history: SessionHistoryResponse = data.data;
        const whiteboardSnapshot = loadWhiteboardSnapshot(sessionId);
        restoringWhiteboardSessionRef.current = sessionId;

        if (whiteboardSnapshot) {
          setWhiteboardSnapshot(whiteboardSnapshot);
        } else {
          clearWhiteboard();
        }

        // 将后端消息转换为前端消息格式
        const restoredMessages: Message[] = [];
        for (const round of history.rounds) {
          for (const msg of round.messages) {
            const role = msg.role === 'assistant' ? 'ai' : 'student';
            const content = msg.content || '';
            const questionResults = (msg.questionResults || msg.question_results) as QuestionResult[] | undefined;
            if (!content && !msg.imageId && !msg.image_id && !msg.image && !msg.video && !questionResults?.length) continue;
            restoredMessages.push({
              id: `hist-${round.round_number}-${Math.random().toString(36).slice(2, 9)}`,
              role,
              content,
              timestamp: round.start_time ? new Date(round.start_time) : new Date(),
              phase: 'explain',
              imageId: msg.imageId || msg.image_id,
              image: msg.image,
              video: msg.video,
              questionResults,
            });
          }
        }

        // 只在有消息时才恢复，否则保持欢迎语
        if (restoredMessages.length > 0) {
          setState(prev => ({
            ...prev,
            sessionId,
            currentKpId: history.kp_id || prev.currentKpId,
            messages: restoredMessages,
            isFirstInput: false,
            currentTopic: history.kp_name || '一次函数',
            currentPhase: Math.max(1, history.rounds[history.current_round_index || 0]?.current_phase || prev.currentPhase),
            totalPhases: Math.max(1, history.rounds[history.current_round_index || 0]?.total_phases || prev.totalPhases),
          }));
        } else {
          setState(prev => ({
            ...prev,
            sessionId,
          }));
        }
      }
    } catch (error) {
      console.error('恢复会话失败:', error);
      localStorage.removeItem('learning_session_id');
    } finally {
      setIsRestoring(false);
    }
  }, [clearWhiteboard, getAuthHeaders, setWhiteboardSnapshot]);

  // 获取会话历史列表
  const fetchSessionList = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const params = new URLSearchParams({ course_id: 'MATH_JUNIOR_01' });
      if (state.currentKpId) {
        params.set('kp_id', state.currentKpId);
      }
      const res = await fetch(`/api/v1/learning/sessions?${params}`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setSessionList(data.data || []);
        }
      }
    } catch (error) {
      console.error('获取会话列表失败:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [getAuthHeaders, state.currentKpId]);

  // 加载某个历史会话的对话
  const loadSessionHistory = useCallback(async (sessionId: string) => {
    setHistoryOpen(false);
    await restoreSession(sessionId);
  }, [restoreSession]);

  // 页面加载时恢复会话
  useEffect(() => {
    const savedSessionId = localStorage.getItem('learning_session_id');
    if (savedSessionId) {
      restoreSession(savedSessionId);
    }
  }, [restoreSession]);

  // 打开历史面板时获取列表
  useEffect(() => {
    if (historyOpen && sessionList.length === 0) {
      fetchSessionList();
    }
  }, [historyOpen, sessionList.length, fetchSessionList]);

  // 直接添加消息到状态
  const addMessageNow = useCallback((role: 'ai' | 'student', content: string, phase: LearningPhase, imageId?: string, image?: MediaResource, video?: MediaResource) => {
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, {
        id: msgId,
        role,
        content,
        timestamp: new Date(),
        phase,
        imageId: imageId || undefined,
        image: image || undefined,
        video: video || undefined,
      }],
    }));
    if (role === 'ai' && voiceAutoReadRef.current) {
      voiceSpeakRef.current(content);
    }
  }, []);

  // 将消息加入队列，逐个显示
  const queueMessage = useCallback((content: string, phase: LearningPhase, extra?: {imageId?: string, image?: MediaResource, video?: MediaResource}) => {
    messageQueueRef.current.push({ content, phase, ...extra });
    processQueue();
  }, []);

  // 处理消息队列，每条消息间隔 1500ms
  const processQueue = () => {
    if (isDisplayingRef.current) return;
    if (messageQueueRef.current.length === 0) return;

    isDisplayingRef.current = true;
    const item = messageQueueRef.current.shift()!;

    addMessageNow('ai', item.content, item.phase, item.imageId, item.image, item.video);

    // 延迟后处理下一条
    setTimeout(() => {
      isDisplayingRef.current = false;
      processQueue();
    }, 1500);
  };

  // 等待消息队列清空
  const waitForQueueDrain = useCallback(async () => {
    // 最多等待 30 秒
    const maxWait = 30000;
    const start = Date.now();
    while (isDisplayingRef.current || messageQueueRef.current.length > 0) {
      if (Date.now() - start > maxWait) break;
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }, []);

  // 开始评估
  const startAssessment = async () => {
    if (!state.sessionId) return;

    // 使用 ref 防止重复调用
    if (isLoadingAssessmentRef.current) return;
    isLoadingAssessmentRef.current = true;

    try {
      setState(prev => ({ ...prev, isStreaming: true }));

      const res = await fetch(`/api/v1/learning/session/${state.sessionId}/assessment`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!res.ok) throw new Error(`获取评估题目失败: ${res.status}`);

      const data = await res.json();

      if (data.success && data.data?.questions?.length > 0) {
        const questions = data.data.questions;

        setState(prev => ({
          ...prev,
          assessmentQuestions: questions,
          currentQuestionIndex: 0,
          selectedAnswers: {},
          isStreaming: false,
        }));

        // 显示评估开始消息
        addMessageNow('ai', `很好！让我们来做 ${questions.length} 道题检验一下学习效果：`, 'assessment');
      } else {
        addMessageNow('ai', '暂无评估题目，本节学习完成！', 'feedback');
        setState(prev => ({ ...prev, isStreaming: false, phase: 'explain' }));
      }
    } catch (error) {
      console.error('获取评估题目失败:', error);
      message.error('获取评估题目失败');
      setState(prev => ({ ...prev, isStreaming: false }));
    } finally {
      isLoadingAssessmentRef.current = false;
    }
  };

  // 选择答案（选择题）
  const selectAnswer = (questionId: string, answer: string) => {
    setState(prev => ({
      ...prev,
      selectedAnswers: { ...prev.selectedAnswers, [questionId]: answer },
    }));
  };

  // 输入答案（填空题）
  const inputAnswer = (questionId: string, answer: string) => {
    setState(prev => ({
      ...prev,
      selectedAnswers: { ...prev.selectedAnswers, [questionId]: answer },
    }));
  };

  // 提交评估答案
  const submitAssessment = async () => {
    if (!state.sessionId || state.assessmentQuestions.length === 0) return;

    try {
      setState(prev => ({ ...prev, isStreaming: true }));

      const answers = Object.entries(state.selectedAnswers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer,
      }));

      const res = await fetch(`/api/v1/learning/session/${state.sessionId}/assessment`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ answers }),
      });

      if (!res.ok) throw new Error(`提交评估失败: ${res.status}`);

      const data = await res.json();

      if (data.success) {
        const result = data.data;
        const questionResults = result.question_results || [];

        // 构建评估结果消息
        const resultMsgId = `result-${Date.now()}`;
        let resultContent = `📊 **评估结果**\n\n正确率：${result.correct_count}/${result.total_questions}（${Math.round(result.score * 100)}分）\n\n`;
        resultContent += result.passed ? '🎉 恭喜你通过本次学习！' : '💪 还需要再努力一下，让我们继续加油！';

        // 添加评估结果消息（包含题目详情）
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, {
            id: resultMsgId,
            role: 'ai',
            content: resultContent,
            timestamp: new Date(),
            phase: 'feedback',
            questionResults: questionResults,
          }],
          assessmentQuestions: [],
          selectedAnswers: {},
          isStreaming: false,
        }));

        // 根据评估结果决定下一步
        if (result.passed && result.next_kp_name) {
          // 通过且有下一个知识点，自动开始新知识点学习
          setTimeout(() => {
            startNewKnowledgePoint(result.next_kp_name!);
          }, 1500);
        } else if (!result.passed) {
          // 未通过，继续当前知识点讲解
          setState(prev => ({ ...prev, phase: 'explain' }));
          setTimeout(() => {
            continueLearning();
          }, 1500);
        }
      }
    } catch (error) {
      console.error('提交评估失败:', error);
      message.error('提交评估失败');
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  };

  // 开始新知识点学习
  const startNewKnowledgePoint = async (kpName: string) => {
    if (!state.sessionId) return;

    // 更新当前主题
    setState(prev => ({ ...prev, currentTopic: kpName, phase: 'explain', currentPhase: 1, totalPhases: 4 }));

    // 添加新知识点开始消息
    addMessageNow('ai', `🎉 现在我们开始学习新的知识点：「${kpName}」`, 'explain');

    // 直接开始新知识点的教学
    setTimeout(async () => {
      setState(prev => ({ ...prev, isStreaming: true }));

      try {
        const res = await fetch(`/api/v1/learning/session/${state.sessionId}/stream?start_new=true`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ message: '', is_first_input: true }),
        });

        if (!res.ok) throw new Error(`请求失败: ${res.status}`);

        await processStreamResponse(res);
      } catch (error) {
        console.error('开始新知识点失败:', error);
        message.error('开始新知识点失败');
      } finally {
        setState(prev => ({ ...prev, isStreaming: false }));
      }
    }, 500);
  };

  // 继续当前知识点学习
  const continueLearning = async () => {
    if (!state.sessionId) return;

    // 添加继续学习消息
    addMessageNow('ai', '💪 让我们再复习一下这个知识点吧', 'explain');

    // 直接开始复习教学
    setTimeout(async () => {
      setState(prev => ({ ...prev, isStreaming: true, isFirstInput: true }));

      try {
        const res = await fetch(`/api/v1/learning/session/${state.sessionId}/stream?start_new=true`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ message: '', is_first_input: true }),
        });

        if (!res.ok) throw new Error(`请求失败: ${res.status}`);

        await processStreamResponse(res);
      } catch (error) {
        console.error('继续学习失败:', error);
        message.error('继续学习失败');
      } finally {
        setState(prev => ({ ...prev, isStreaming: false }));
      }
    }, 500);
  };

  // 流式获取讲解内容
  const streamTeaching = async (sessionId: string) => {
    abortControllerRef.current = new AbortController();
    
    try {
      const res = await fetch(`/api/v1/learning/session/${sessionId}/stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token || localStorage.getItem('token')}`,
        },
        signal: abortControllerRef.current.signal,
      });
      
      if (!res.ok) throw new Error(`请求失败: ${res.status}`);
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) return;
      
      let buffer = '';
      let currentEventType = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        buffer = buffer.replace(/\r\n/g, '\n');
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith('event:')) {
            currentEventType = trimmedLine.slice(6).trim();
            continue;
          }
          
          if (trimmedLine.startsWith('data:')) {
            const data = trimmedLine.slice(5).trim();
            if (!data || data === '[DONE]') continue;

            try {
              const json = JSON.parse(data);

              const eventType = json.type || currentEventType;
              
              // 根据事件类型处理
              switch (eventType) {
                case 'segment':
                  if (json.message) {
                    let imageResource: MediaResource | undefined = json.image && json.image.type === 'image' ? json.image : undefined;
                    let videoResource: MediaResource | undefined = json.image && json.image.type === 'video' ? json.image : undefined;
                    if (json.video) videoResource = json.video;
                    queueMessage(json.message, 'explain', { imageId: json.image_id, image: imageResource, video: videoResource });
                  }
                  if (json.whiteboard_html) {
                    mergeCurrentWhiteboard({
                      html: json.whiteboard_html,
                    });
                  }

                  if (json.image && json.image.type === 'image') {
                    setWhiteboardImage({
                      id: json.image.id,
                      url: json.image.url,
                      svg_code: json.image.svg_code,
                      title: json.image.title,
                      description: json.image.description,
                      type: json.image.type,
                    });
                  }
                  break;

                case 'whiteboard_page_delta':
                  if (json.whiteboard_html) {
                    mergeCurrentWhiteboard({ html: json.whiteboard_html });
                  }
                  break;
                
                // 工具增强事件（v2新增）
                case 'tool_call':
                  // 可选：显示工具调用提示
                  break;
                
                case 'tool_result':
                  // 如果工具结果包含图片，添加到消息中
                  if (json.success && json.image_id) {
                    const toolMsgId = `tool-${Date.now()}`;
                    setState(prev => ({
                      ...prev,
                      messages: [...prev.messages, {
                        id: toolMsgId,
                        role: 'ai',
                        content: json.message || '',
                        timestamp: new Date(),
                        phase: 'explain',
                        imageId: json.image_id,
                      }],
                    }));
                  }
                  break;
                
                // 教学模式事件
                case 'msg_intro':
                case 'msg_def':
                case 'msg_example':
                case 'msg_summary':
                case 'msg_question':
                  if (json.content) {
                    queueMessage(json.content, 'explain');
                  }
                  break;
                
                // 对话模式事件
                case 'msg_feedback':
                case 'msg_supplement':
                case 'msg_encourage':
                  if (json.content) {
                    queueMessage(json.content, 'feedback');
                  }
                  break;
                
                case 'wb_title':
                  if (json.content) setWhiteboardTitle(json.content);
                  break;
                
                case 'wb_points':
                  if (json.content) addWhiteboardPoint(json.content);
                  break;
                
                case 'wb_formulas':
                  if (json.content) addWhiteboardFormula(json.content);
                  break;
                
                case 'wb_examples':
                  if (json.content) addWhiteboardExample(json.content);
                  break;
                
                case 'wb_notes':
                  if (json.content) addWhiteboardNote(json.content);
                  break;
                
                case 'complete':
                  commitWhiteboard();
                  if (json.next_action === 'start_assessment') {
                    setState(prev => ({ ...prev, phase: 'assessment' }));
                    waitForQueueDrain().then(() => {
                      setTimeout(() => startAssessment(), 500);
                    });
                  } else if (json.next_action === 'question') {
                    setState(prev => ({ ...prev, phase: 'question' }));
                  }
                  break;

                case 'phase_advance':
                  setState(prev => ({
                    ...prev,
                    currentPhase: Math.max(1, Number(json.current_phase) || prev.currentPhase),
                    totalPhases: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                  }));
                  if (json.next_action === 'start_assessment') {
                    setState(prev => ({
                      ...prev,
                      phase: 'assessment',
                      currentPhase: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                      totalPhases: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                    }));
                    waitForQueueDrain().then(() => {
                      setTimeout(() => startAssessment(), 500);
                    });
                  }
                  break;
              }
            } catch (e) {}
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('流式获取失败:', error);
      }
    } finally {
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  };

  // 处理流式响应
  const processStreamResponse = async (res: Response) => {
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    
    if (!reader) return;
    
    let buffer = '';
    let currentEventType = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, '\n');
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('event:')) {
          currentEventType = trimmedLine.slice(6).trim();
          continue;
        }
        
        if (trimmedLine.startsWith('data:')) {
          const data = trimmedLine.slice(5).trim();
          if (!data || data === '[DONE]') continue;
          
          try {
            const json = JSON.parse(data);

            const eventType = json.type || currentEventType;

            // 根据事件类型处理
            switch (eventType) {
              // 教学模式事件
              case 'segment':
                if (json.message) {
                  // 提取媒体资源
                  let imageResource: MediaResource | undefined = json.image && json.image.type === 'image' ? json.image : undefined;
                  let videoResource: MediaResource | undefined = json.image && json.image.type === 'video' ? json.image : undefined;
                  if (json.video) videoResource = json.video;
                  queueMessage(json.message, 'explain', { imageId: json.image_id, image: imageResource, video: videoResource });
                } else if (json.image) {
                  // 只有媒体资源没有文本消息
                  let imageResource: MediaResource | undefined = json.image.type === 'image' ? json.image : undefined;
                  let videoResource: MediaResource | undefined = json.image.type === 'video' ? json.image : undefined;
                  queueMessage(json.image.title || '', 'explain', { image: imageResource, video: videoResource });
                }
                if (json.whiteboard_html) {
                  mergeCurrentWhiteboard({
                    html: json.whiteboard_html,
                  });
                }
                if (json.image && json.image.type === 'image') {
                  setWhiteboardImage({
                    id: json.image.id,
                    url: json.image.url,
                    svg_code: json.image.svg_code,
                    title: json.image.title,
                    description: json.image.description,
                    type: json.image.type,
                  });
                }
                break;

              case 'whiteboard_page_delta':
                if (json.whiteboard_html) {
                  mergeCurrentWhiteboard({ html: json.whiteboard_html });
                }
                break;
              
              // 工具增强事件（v2新增）
              case 'tool_call':
                break;
              
              case 'tool_result':
                if (json.success && json.image_id) {
                  const toolMsgId = `tool-${Date.now()}`;
                  setState(prev => ({
                    ...prev,
                    messages: [...prev.messages, {
                      id: toolMsgId,
                      role: 'ai',
                      content: json.message || '',
                      timestamp: new Date(),
                      phase: 'explain',
                      imageId: json.image_id,
                    }],
                  }));
                }
                break;
              
              case 'msg_intro':
              case 'msg_def':
              case 'msg_example':
              case 'msg_summary':
              case 'msg_question':
                if (json.content) {
                  queueMessage(json.content, 'explain');
                }
                break;
              
              // 对话模式事件
              case 'msg_feedback':
              case 'msg_supplement':
              case 'msg_encourage':
                if (json.content) {
                  queueMessage(json.content, 'feedback');
                }
                break;
              
              case 'wb_formulas':
                // 白板公式事件：显示在白板上而不是消息列表
                if (json.content) {
                  addWhiteboardFormula(json.content);
                }
                break;
              
              case 'phase_advance':
                setState(prev => ({
                  ...prev,
                  currentPhase: Math.max(1, Number(json.current_phase) || prev.currentPhase),
                  totalPhases: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                }));
                if (json.next_action === 'start_assessment') {
                  setState(prev => ({
                    ...prev,
                    phase: 'assessment',
                    currentPhase: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                    totalPhases: Math.max(1, Number(json.total_phases) || prev.totalPhases),
                  }));
                  waitForQueueDrain().then(() => {
                    setTimeout(() => startAssessment(), 500);
                  });
                }
                break;
              
              case 'complete':
                commitWhiteboard();
                if (json.next_action === 'start_assessment') {
                  setState(prev => ({ ...prev, phase: 'assessment' }));
                  // 等待消息队列全部展示完毕后再开始评估
                  waitForQueueDrain().then(() => {
                    setTimeout(() => startAssessment(), 500);
                  });
                } else if (json.next_action === 'question') {
                  setState(prev => ({ ...prev, phase: 'question' }));
                }
                break;
            }
          } catch (e) {}
        }
      }
    }
  };

  // 发送消息
  const handleSend = useCallback(async (content: string) => {
    console.log('[SEND] handleSend, content=' + content.substring(0, 40) + ', isStreaming=' + state.isStreaming + ', isFirstInput=' + state.isFirstInput + ', sessionId=' + state.sessionId);
    if (state.isStreaming) return;
    
    addMessageNow('student', content, state.phase);
    setState(prev => ({ ...prev, isStreaming: true }));
    
    try {
      // 判断是否是首次输入（欢迎语后的确认）
      const isFirstInput = state.isFirstInput;
      
      if (isFirstInput) {
        // 首次输入只是确认，不发送用户内容
        setState(prev => ({ ...prev, isFirstInput: false }));
      }
      
      if (!state.sessionId) {
        // 创建会话（如果有 URL 传入的 kp_id 则指定知识点）
        const body: Record<string, string> = { course_id: 'MATH_JUNIOR_01' };
        if (urlKpId) {
          body.kp_id = urlKpId;
        }
        const startRes = await fetch('/api/v1/learning/start', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(body),
        });
        
        if (!startRes.ok) throw new Error(`创建会话失败: ${startRes.status}`);
        
        const startData = await startRes.json();
        const sessionId = startData.data?.session_id;
        
        if (sessionId) {
          const kpId = startData.data?.kp_id || urlKpId || null;
          const kpName = startData.data?.kp_name || null;
          setState(prev => ({
            ...prev,
            sessionId,
            currentKpId: kpId,
            currentTopic: kpName || prev.currentTopic,
            currentPhase: 1,
            totalPhases: 4,
          }));
          saveSessionId(sessionId);
          clearWhiteboard();
          // 清除 URL 中的 kp_id 参数，避免刷新重复创建
          setSearchParams({}, { replace: true });
          
          // 根据useTools选择不同的API端点
          const apiUrl = state.useTools 
            ? `/api/v1/teaching-v2/session/${sessionId}/teach-v2?use_tools=true`
            : `/api/v1/learning/session/${sessionId}/stream`;
          
          // 首次输入发送空消息，让后端开始教学
          const res = await fetch(apiUrl, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ 
              message: isFirstInput ? '' : content,
              is_first_input: isFirstInput,
            }),
          });
          
          if (!res.ok) throw new Error(`请求失败: ${res.status}`);
          
          await processStreamResponse(res);
        }
      } else {
        // 根据useTools选择不同的API端点
        const apiUrl = state.useTools 
          ? `/api/v1/teaching-v2/session/${state.sessionId}/teach-v2?use_tools=true`
          : `/api/v1/learning/session/${state.sessionId}/stream`;
        
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ 
            message: isFirstInput ? '' : content,
            is_first_input: isFirstInput,
          }),
        });
        
        if (!res.ok) throw new Error(`请求失败: ${res.status}`);
        
        await processStreamResponse(res);
      }
    } catch (error: any) {
      console.error('发送失败:', error);
      message.error('发送失败，请重试');
    } finally {
      // 等待消息队列全部展示完毕后再结束流式状态
      await waitForQueueDrain();
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, [state.sessionId, state.isStreaming, state.phase, state.isFirstInput, state.useTools, addMessageNow, getAuthHeaders, queueMessage, saveSessionId, waitForQueueDrain]);

  const handleVoiceInput = useCallback(() => {
    if (voice.isListening) {
      voice.stopListening();
      return;
    }

    voice.startListening({
      initialText: inputText,
      onTranscript: setInputText,
    });
  }, [inputText, voice]);

  const submitInputText = useCallback(() => {
    const content = inputText.trim();
    if (!content || state.isStreaming) return;
    handleSend(content);
    setInputText('');
  }, [handleSend, inputText, state.isStreaming]);

  const handleWhiteboardQuizAnswer = useCallback((answer: string, source: 'quiz' | 'reveal' = 'quiz') => {
    const content = answer.trim();
    if (!content) return;
    const messageContent = source === 'quiz'
      ? `我选择：${content}`
      : `我看到了白板提问：${content}`;
    if (state.isStreaming) {
      pendingWhiteboardAnswerRef.current = messageContent;
      return;
    }
    setInputText('');
    handleSend(messageContent);
  }, [handleSend, state.isStreaming]);

  useEffect(() => {
    if (state.isStreaming || !pendingWhiteboardAnswerRef.current) return;
    const answer = pendingWhiteboardAnswerRef.current;
    pendingWhiteboardAnswerRef.current = null;
    setInputText('');
    handleSend(answer);
  }, [handleSend, state.isStreaming]);

  const handleSubmitDrawing = useCallback(async (imageData: string) => {
    if (!state.sessionId || !state.interactiveTask) return;

    setState(prev => ({ ...prev, isSubmittingDrawing: true }));

    try {
      const res = await fetch(`/api/v1/interactive/session/${state.sessionId}/submit-drawing`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          task_id: state.interactiveTask.id,
          image_data: imageData,
        }),
      });

      if (!res.ok) throw new Error(`提交失败: ${res.status}`);

      const data = await res.json();

      if (data.success) {
        const feedback: AIFeedback = data.data;
        setState(prev => ({
          ...prev,
          aiDrawingFeedback: feedback,
          whiteboardMode: 'display',
          interactiveTask: null,
        }));

        addMessageNow('ai', feedback.feedback, 'feedback');
      }
    } catch (error) {
      console.error('提交绘图失败:', error);
      message.error('提交失败，请重试');
    } finally {
      setState(prev => ({ ...prev, isSubmittingDrawing: false }));
    }
  }, [state.sessionId, state.interactiveTask, getAuthHeaders, addMessageNow]);

  const openInteractivePanel = useCallback(() => {
    setInteractivePanelMounted(true);
    setState(prev => ({ ...prev, showInteractivePanel: true }));
    window.requestAnimationFrame(() => {
      setInteractivePanelVisible(true);
    });
  }, []);

  const handleCloseInteractivePanel = useCallback(() => {
    setInteractivePanelVisible(false);
    setState(prev => ({ ...prev, showInteractivePanel: false }));
  }, []);

  const handleToggleInteractivePanel = useCallback(() => {
    if (state.showInteractivePanel) {
      handleCloseInteractivePanel();
      return;
    }

    openInteractivePanel();
  }, [handleCloseInteractivePanel, openInteractivePanel, state.showInteractivePanel]);

  const isInteractivePanelOpen = state.showInteractivePanel;
  const interactivePanelButtonLabel = isInteractivePanelOpen ? '关闭互动白板' : '打开互动白板';
  const interactivePanelClassName = [
    'side-card',
    'interactive-side-card',
    interactivePanelVisible ? 'is-open' : 'is-closed',
  ].join(' ');

  const sidePanelClassName = [
    'learning-side-panel',
    isInteractivePanelOpen ? 'interactive-active' : '',
  ].filter(Boolean).join(' ');

  const latestStudentMessage = [...state.messages].reverse().find((msg) => msg.role === 'student' && msg.content.trim());
  const phaseLabelMap: Record<LearningPhase, string> = {
    explain: '概念讲解',
    question: '随堂练习',
    interactive: '互动探究',
    feedback: '即时反馈',
    assessment: '阶段测评',
  };
  const safeTotalPhases = Math.max(1, state.totalPhases || 4);
  const safeCurrentPhase = Math.min(safeTotalPhases, Math.max(1, state.currentPhase || 1));
  const lessonProgressPercent = state.phase === 'assessment'
    ? 100
    : Math.round((safeCurrentPhase / safeTotalPhases) * 100);
  const answeredCount = Object.keys(state.selectedAnswers).length;
  const assessmentTotal = state.assessmentQuestions.length;
  const boardItemCount = whiteboardBlocks.length
    + currentWhiteboard.key_points.length
    + currentWhiteboard.formulas.length
    + currentWhiteboard.examples.length
    + currentWhiteboard.notes.length
    + (currentWhiteboard.title ? 1 : 0)
    + (currentWhiteboard.html ? 1 : 0)
    + (currentWhiteboard.image ? 1 : 0);
  const sideHint = state.phase === 'assessment'
    ? '先完成当前小测，再看解析。'
    : state.phase === 'question'
      ? '先说出你的思路，再看老师反馈。'
      : state.phase === 'interactive'
        ? '可以打开互动白板，把想法画出来。'
        : '跟着左侧当前内容，抓住一个核心点。';

  const renderRecordMedia = (msg: Message) => {
    if (msg.image) {
      return (
        <div className="side-record-media">
          <img
            src={msg.image.url}
            alt={msg.image.title || '教学图片'}
            title={msg.image.description || msg.image.title || '教学图片'}
          />
          {msg.image.title && <div className="side-record-media-caption">{msg.image.title}</div>}
        </div>
      );
    }

    if (msg.video) {
      return (
        <div className="side-record-media">
          <video
            src={msg.video.url}
            controls
            poster={msg.video.thumbnail_url}
            title={msg.video.description || msg.video.title || '教学视频'}
          />
          {msg.video.title && <div className="side-record-media-caption">{msg.video.title}</div>}
        </div>
      );
    }

    if (msg.imageId) {
      return (
        <TeachingImage
          imageId={msg.imageId}
          className="side-record-teaching-image"
          showDescription
        />
      );
    }

    return null;
  };

  const renderQuestionResults = (results?: QuestionResult[]) => {
    if (!results || results.length === 0) return null;

    return (
      <div className="assessment-results side-assessment-results">
        {results.map((result, index) => (
          <div key={result.question_id || index} className={`result-item ${result.is_correct ? 'correct' : 'incorrect'}`}>
            <div className="result-header">
              <span className="result-index">第 {index + 1} 题</span>
              <span className={`result-status ${result.is_correct ? 'correct' : 'incorrect'}`}>
                {result.is_correct ? '正确' : '需订正'}
              </span>
            </div>
            <div className="result-question"><MarkdownContent content={result.content} /></div>
            <div className="result-answer">
              <div className="answer-row">
                <span className="answer-label">你的答案：</span>
                <span className={result.is_correct ? 'answer-correct' : 'answer-wrong'}>{result.student_answer || '未作答'}</span>
              </div>
              <div className="answer-row">
                <span className="answer-label">正确答案：</span>
                <span className="answer-correct">
                  {Array.isArray(result.correct_answer) ? result.correct_answer.join('、') : result.correct_answer}
                </span>
              </div>
            </div>
            {result.explanation && (
              <div className="result-explanation">
                <span className="explanation-label">解析</span>
                <div className="explanation-content"><MarkdownContent content={result.explanation} /></div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="minimal-learning">
      {/* Overlay header */}
      <header className="minimal-header">
        <div className="header-content">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} className="back-btn" aria-label="返回上一页">
            返回
          </Button>
          <div className="header-right">
            <span className="header-topic">{state.currentTopic}</span>
            <Button
              type="text"
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => { fetchSessionList(); setHistoryOpen(true); }}
              title="历史会话"
              aria-label="打开历史会话"
            />
            <Button
              type="text"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => {
                localStorage.removeItem('learning_session_id');
                setSearchParams({}, { replace: true });
                setState(prev => ({
                  ...prev,
                  sessionId: null,
                  currentKpId: null,
                  currentPhase: 1,
                  totalPhases: 4,
                  messages: [{
                    id: 'welcome-msg',
                    role: 'ai' as const,
                    content: '你好！我是你的AI老师。今天我们来学习"一次函数"。准备好了吗？输入任何内容开始学习。',
                    timestamp: new Date(),
                    phase: 'explain' as LearningPhase,
                  }],
                  isFirstInput: true,
                  phase: 'explain' as LearningPhase,
                  assessmentQuestions: [],
                  currentQuestionIndex: 0,
                  selectedAnswers: {},
                  currentTopic: '一次函数',
                }));
              }}
              title="新开会话"
              aria-label="新开会话"
            />
            <Button
              type={state.useTools ? 'primary' : 'default'}
              size="small"
              icon={<ToolOutlined />}
              onClick={() => setState(prev => ({ ...prev, useTools: !prev.useTools }))}
              title={state.useTools ? '工具增强已启用' : '工具增强已禁用'}
              aria-label={state.useTools ? '关闭工具增强' : '开启工具增强'}
            >
              {state.useTools ? '工具增强' : '标准模式'}
            </Button>
            <Button
              type={isInteractivePanelOpen ? 'primary' : 'default'}
              size="small"
              icon={<ToolOutlined />}
              onClick={handleToggleInteractivePanel}
              title={interactivePanelButtonLabel}
              aria-label={interactivePanelButtonLabel}
            >
              {interactivePanelButtonLabel}
            </Button>
            <Button
              type={voice.autoRead ? 'primary' : 'default'}
              size="small"
              icon={voice.isPaused ? <PlayCircleOutlined /> : voice.isSpeaking ? <PauseCircleOutlined /> : <SoundOutlined />}
              onClick={() => {
                if (voice.isSpeaking) {
                  if (voice.isPaused) {
                    voice.resumeSpeaking();
                  } else {
                    voice.pauseSpeaking();
                  }
                  return;
                }
                const nextAutoRead = !voice.autoRead;
                voice.setAutoRead(nextAutoRead);
                if (nextAutoRead) {
                  const lastAiMessage = [...state.messages].reverse().find((msg) => msg.role === 'ai' && msg.content.trim());
                  if (lastAiMessage) {
                    voice.speak(lastAiMessage.content, { interrupt: true });
                  }
                }
              }}
              title={voice.isPaused ? '继续播放语音' : voice.isSpeaking ? '暂停语音播放' : voice.autoRead ? '自动朗读已开启' : '自动朗读已关闭'}
              aria-label={voice.isPaused ? '继续播放语音' : voice.isSpeaking ? '暂停语音播放' : voice.autoRead ? '关闭自动朗读' : '开启自动朗读'}
            >
              {voice.isPaused ? '继续播放' : voice.isSpeaking ? '暂停语音' : voice.autoRead ? '自动朗读' : '手动朗读'}
            </Button>
            <div className="user-info">
              <span className="user-name">{user?.name || '学生'}</span>
              <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout} className="logout-btn" title="退出登录" aria-label="退出登录" />
            </div>
          </div>
        </div>
      </header>

      <main className="learning-workspace">
        <section className="lesson-stage" aria-label="课堂画布">
          <div className="lesson-stage-header">
            <div>
              <div className="stage-eyebrow">课堂画布</div>
              <h1>{state.currentTopic}</h1>
            </div>
            <Tag color={state.isStreaming ? 'processing' : 'default'}>
              {state.isStreaming ? '老师讲解中' : phaseLabelMap[state.phase]}
            </Tag>
          </div>
          <div className="whiteboard-main">
            <Whiteboard loading={state.isStreaming} onQuizAnswer={handleWhiteboardQuizAnswer} />
          </div>
        </section>

        <aside className={sidePanelClassName} aria-label="学习辅助区">
          <div className={`side-content-base ${isInteractivePanelOpen ? 'is-covered' : ''}`} aria-hidden={isInteractivePanelOpen}>
              <section className="side-card side-overview-card">
                <div className="side-card-title">学习状态</div>
                <div className="goal-topic">{phaseLabelMap[state.phase]}</div>
                <p>{sideHint}</p>
                <div className="compact-step-row">
                  {Array.from({ length: safeTotalPhases }, (_, index) => (
                    <span
                      key={`phase-${index + 1}`}
                      className={`compact-step-dot ${index + 1 < safeCurrentPhase || state.phase === 'assessment' ? 'done' : index + 1 === safeCurrentPhase ? 'active' : ''}`}
                      title={`第 ${index + 1} 阶段`}
                    />
                  ))}
                </div>
                <div className="phase-progress-meta">
                  <span>{state.phase === 'assessment' ? '教学完成' : `第 ${safeCurrentPhase} / ${safeTotalPhases} 阶段`}</span>
                  <strong>{lessonProgressPercent}%</strong>
                </div>
                <div className="side-stats">
                  <div>
                    <strong>{boardItemCount}</strong>
                    <span>板书点</span>
                  </div>
                  <div>
                    <strong>{state.messages.length}</strong>
                    <span>互动轮次</span>
                  </div>
                  <div>
                    <strong>{assessmentTotal ? `${answeredCount}/${assessmentTotal}` : '-'}</strong>
                    <span>测评进度</span>
                  </div>
                </div>
              </section>

              {state.phase === 'assessment' && state.assessmentQuestions.length > 0 && (
                <section className="side-card side-assessment-card">
                  <div className="side-card-title">随堂小测</div>
                  <div className="assessment-panel side-assessment-panel">
                {state.assessmentQuestions.map((q, idx) => {
                  const displayOptions = q.type === '判断题' && (!q.options || q.options.length === 0)
                    ? ['正确', '错误']
                    : q.options;

                  return (
                    <div key={q.id} className="assessment-question">
                      <div className="question-header">第 {idx + 1} 题</div>
                      <div className="question-content"><MarkdownContent content={q.content} /></div>

                      {displayOptions && displayOptions.length > 0 ? (
                        <div className="question-options">
                          {displayOptions.map((opt, optIdx) => {
                            const hasPrefix = /^[A-D][\.、\s]/.test(opt);
                            const displayText = hasPrefix ? opt : `${String.fromCharCode(65 + optIdx)}. ${opt}`;

                            return (
                              <button
                                key={optIdx}
                                className={`option-btn ${state.selectedAnswers[q.id] === opt ? 'selected' : ''}`}
                                onClick={() => selectAnswer(q.id, opt)}
                              >
                                {displayText}
                              </button>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="question-input">
                          <input
                            type="text"
                            className="answer-input"
                            placeholder="请输入答案"
                            value={state.selectedAnswers[q.id] || ''}
                            onChange={(e) => inputAnswer(q.id, e.target.value)}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
                <button
                  className="submit-assessment-btn"
                  onClick={submitAssessment}
                  disabled={Object.keys(state.selectedAnswers).length < state.assessmentQuestions.length}
                >
                  提交答案
                </button>
                  </div>
                </section>
              )}

              <section className="side-card side-record-card">
                <div className="side-card-title">学习记录</div>
                {latestStudentMessage && (
                  <div className="side-latest-answer">
                    <span>你刚才：</span>
                    <MarkdownContent content={latestStudentMessage.content} />
                  </div>
                )}
                <div className="side-full-record-list fixed">
                  {state.messages.map((msg) => (
                    <div key={msg.id} className={`side-full-record ${msg.role}`}>
                      <div className="side-full-record-avatar">{msg.role === 'ai' ? '师' : '我'}</div>
                      <div className="side-full-record-content">
                        {msg.role === 'ai' && (
                          <button
                            type="button"
                            className="side-speak-btn"
                            onClick={() => voice.speak(msg.content, { interrupt: true })}
                            disabled={!voice.speechSynthesisSupported}
                            title={voice.speechSynthesisSupported ? '朗读这条记录' : '当前浏览器不支持朗读'}
                            aria-label="朗读这条学习记录"
                          >
                            <SoundOutlined />
                          </button>
                        )}
                        <MarkdownContent content={msg.content} />
                        {renderRecordMedia(msg)}
                        {renderQuestionResults(msg.questionResults)}
                      </div>
                    </div>
                  ))}
                  {(state.isStreaming || isRestoring) && (
                    <div className="side-full-record ai">
                      <div className="side-full-record-avatar">师</div>
                      <div className="side-full-record-content">老师正在讲解...</div>
                    </div>
                  )}
                </div>
                <div
                  ref={chatPanelRef}
                  className="side-record-composer"
                >
                  <div className="classroom-controls">
                    <button
                      type="button"
                      className={`voice-input-btn ${voice.isListening ? 'recording' : ''}`}
                      disabled={state.isStreaming}
                      onClick={handleVoiceInput}
                      title={voice.speechRecognitionSupported ? (voice.isListening ? '停止语音输入' : '语音输入') : '当前浏览器不支持语音输入'}
                      aria-label={voice.isListening ? '停止语音输入' : '开始语音输入'}
                    >
                      {voice.isListening ? <StopOutlined /> : <AudioOutlined />}
                    </button>
                    <textarea
                      className="input-field"
                      placeholder={state.phase === 'explain' ? '输入问题...' : '输入回答...'}
                      disabled={state.isStreaming}
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          submitInputText();
                        }
                      }}
                    />
                    <button
                      className="send-btn"
                      disabled={state.isStreaming || !inputText.trim()}
                      onClick={submitInputText}
                      aria-label="发送消息"
                    >
                      发送
                    </button>
                  </div>
                  {voice.error && <div className="voice-status">{voice.error}</div>}
                </div>
              </section>
          </div>

          {interactivePanelMounted && (
            <section className={interactivePanelClassName} aria-label="互动白板">
              <div className="interactive-side-header">
                <div>
                  <div className="side-card-title">互动白板</div>
                  <p>在这里画图、标注或解题，不会遮住左侧课堂画布。</p>
                </div>
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={handleCloseInteractivePanel}
                  title="收起互动白板"
                  aria-label="关闭互动白板面板"
                />
              </div>
              <div className="interactive-side-body">
                <InteractiveWhiteboard
                  mode="interactive"
                  interactiveTask={state.interactiveTask}
                  aiFeedback={state.aiDrawingFeedback}
                  onSubmit={handleSubmitDrawing}
                  isSubmitting={state.isSubmittingDrawing}
                  width={300}
                  height={280}
                  compact
                />
              </div>
            </section>
          )}
        </aside>
      </main>

      {/* 历史会话抽屉 */}
      <Drawer
        title="历史会话"
        placement="left"
        width={360}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        closeIcon={<CloseOutlined />}
        aria-label="历史会话抽屉"
      >
        {isLoadingHistory ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : sessionList.length === 0 ? (
          <Empty description="暂无历史会话" />
        ) : (
          <div>
            {sessionList.map((item) => (
              <div
                key={item.session_id}
                style={{
                  cursor: 'pointer',
                  padding: '12px 8px',
                  borderRadius: 8,
                  marginBottom: 4,
                  backgroundColor: item.session_id === state.sessionId ? '#e6f4ff' : undefined,
                  border: item.session_id === state.sessionId ? '1px solid #91caff' : '1px solid transparent',
                }}
                onClick={() => loadSessionHistory(item.session_id)}
              >
                <div style={{ fontSize: 14, fontWeight: 500 }}>
                  {item.kp_name || '未开始'}
                  {item.session_id === state.sessionId && (
                    <Tag color="blue" style={{ marginLeft: 8, fontSize: 11 }}>当前</Tag>
                  )}
                </div>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  <div>第 {item.current_round} 轮 · {item.total_messages} 条消息</div>
                  <div>{item.created_at ? new Date(item.created_at).toLocaleString('zh-CN') : ''}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default MinimalLearning;
