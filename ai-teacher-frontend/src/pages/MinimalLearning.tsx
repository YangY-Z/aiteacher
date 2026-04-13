import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, message } from 'antd';
import { LogoutOutlined, ArrowLeftOutlined, ToolOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import FloatingWhiteboard from '../components/whiteboard/FloatingWhiteboard';
import TeachingImage from '../components/teaching/TeachingImage';
import { useAuthStore, useLearningStore } from '../store';
import './MinimalLearning.css';

type LearningPhase = 'explain' | 'question' | 'feedback' | 'assessment';

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

interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  phase?: LearningPhase;
  question?: Question;
  questionResults?: QuestionResult[];  // 评估结果
  imageId?: string;  // 工具增强：图片ID
}

interface LearningState {
  currentTopic: string;
  phase: LearningPhase;
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
}

// 渲染带有公式的内容
const renderContentWithFormula = (content: string): React.ReactNode => {
  // 清理内容：移除开头结尾的空白，将连续换行符合并为一个
  let cleanContent = content.trim().replace(/\n{3,}/g, '\n\n');
  
  const parts: React.ReactNode[] = [];
  let key = 0;
  
  // 匹配模式：$$...$$（块级）、$...$（行内）、\[...\]（块级）、\(...\)（行内）
  const formulaPatterns = [
    { regex: /\$\$([\s\S]*?)\$\$/g, isBlock: true },
    { regex: /\\\[([\s\S]*?)\\\]/g, isBlock: true },
    { regex: /\$([^$\n]+?)\$/g, isBlock: false },
    { regex: /\\\(([^)]+?)\\\)/g, isBlock: false },
  ];
  
  // 收集所有公式位置
  const allFormulas: { start: number; end: number; formula: string; isBlock: boolean }[] = [];
  
  for (const pattern of formulaPatterns) {
    pattern.regex.lastIndex = 0; // 重置 regex 状态
    let match;
    while ((match = pattern.regex.exec(cleanContent)) !== null) {
      // 检查是否已被其他公式包含
      const isOverlapping = allFormulas.some(
        f => match!.index >= f.start && match!.index < f.end
      );
      if (!isOverlapping) {
        allFormulas.push({
          start: match.index,
          end: match.index + match[0].length,
          formula: match[1].trim(),
          isBlock: pattern.isBlock,
        });
      }
    }
  }
  
  // 如果没有匹配到公式，检查是否整个内容就是公式（包含 LaTeX 命令）
  if (allFormulas.length === 0 && /\\[a-zA-Z]+\{/.test(cleanContent)) {
    // 整个内容可能是公式，尝试渲染
    try {
      const html = katex.renderToString(cleanContent, {
        throwOnError: false,
        displayMode: false,
      });
      return (
        <span
          className="formula-inline"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    } catch {
      // 渲染失败，返回原始内容
      return cleanContent;
    }
  }
  
  // 按位置排序
  allFormulas.sort((a, b) => a.start - b.start);
  
  // 构建渲染结果
  let lastIndex = 0;
  for (const formula of allFormulas) {
    // 添加公式前的文本
    if (formula.start > lastIndex) {
      parts.push(
        <span key={key++}>{cleanContent.slice(lastIndex, formula.start)}</span>
      );
    }
    
    // 渲染公式
    try {
      const html = katex.renderToString(formula.formula, {
        throwOnError: false,
        displayMode: formula.isBlock,
      });
      parts.push(
        <span
          key={key++}
          className={formula.isBlock ? 'formula-block' : 'formula-inline'}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      );
    } catch {
      parts.push(<span key={key++}>{formula.formula}</span>);
    }
    
    lastIndex = formula.end;
  }
  
  // 添加剩余文本
  if (lastIndex < cleanContent.length) {
    parts.push(<span key={key++}>{cleanContent.slice(lastIndex)}</span>);
  }
  
  return parts.length > 0 ? parts : cleanContent;
};

const MinimalLearning: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, token } = useAuthStore();
  const { setWhiteboardTitle, addWhiteboardPoint } = useLearningStore();
  
  const [state, setState] = useState<LearningState>({
    currentTopic: '一次函数',
    phase: 'explain',
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
  });
  
  const chatRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 消息队列和显示控制
  const messageQueueRef = useRef<Array<{content: string, phase: LearningPhase}>>([]);
  const isDisplayingRef = useRef(false);

  // 防止评估接口重复调用
  const isLoadingAssessmentRef = useRef(false);

  const getAuthHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token || localStorage.getItem('token')}`,
  }), [token]);

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [state.messages]);

  // 直接添加消息到状态
  const addMessageNow = useCallback((role: 'ai' | 'student', content: string, phase: LearningPhase) => {
    const msgId = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, {
        id: msgId,
        role,
        content,
        timestamp: new Date(),
        phase,
      }],
    }));
  }, []);

  // 将消息加入队列，逐个显示
  const queueMessage = useCallback((content: string, phase: LearningPhase) => {
    messageQueueRef.current.push({ content, phase });
    processQueue();
  }, []);

  // 处理消息队列，每条消息间隔 800ms
  const processQueue = () => {
    if (isDisplayingRef.current) return;
    if (messageQueueRef.current.length === 0) return;
    
    isDisplayingRef.current = true;
    const item = messageQueueRef.current.shift()!;
    
    addMessageNow('ai', item.content, item.phase);
    
    // 延迟后处理下一条
    setTimeout(() => {
      isDisplayingRef.current = false;
      processQueue();
    }, 800);
  };

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
    setState(prev => ({ ...prev, currentTopic: kpName, phase: 'explain' }));

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
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEventType = line.slice(6).trim();
            continue;
          }
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (!data || data === '[DONE]') continue;
            
            try {
              const json = JSON.parse(data);
              
              // 根据事件类型处理
              switch (currentEventType) {
                case 'segment':
                  if (json.message) {
                    // 工具增强：支持image_id
                    const msgId = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
                    setState(prev => ({
                      ...prev,
                      messages: [...prev.messages, {
                        id: msgId,
                        role: 'ai',
                        content: json.message,
                        timestamp: new Date(),
                        phase: 'explain',
                        imageId: json.image_id,  // 添加图片ID
                      }],
                    }));
                  }
                  if (json.whiteboard) {
                    if (json.whiteboard.title) setWhiteboardTitle(json.whiteboard.title);
                    if (json.whiteboard.points) {
                      json.whiteboard.points.forEach((p: string) => addWhiteboardPoint(p));
                    }
                  }
                  break;
                
                // 工具增强事件（v2新增）
                case 'tool_call':
                  console.log('[Tool Call]', json.tool_name, json.action);
                  // 可选：显示工具调用提示
                  break;
                
                case 'tool_result':
                  console.log('[Tool Result]', json.tool_name, json.success);
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
                case 'wb_formulas':
                case 'wb_examples':
                case 'wb_notes':
                  if (json.content) addWhiteboardPoint(json.content);
                  break;
                
                case 'complete':
                  if (json.next_action === 'start_assessment') {
                    setState(prev => ({ ...prev, phase: 'assessment' }));
                    setTimeout(() => startAssessment(), 1000);
                  } else if (json.next_action === 'question') {
                    setState(prev => ({ ...prev, phase: 'question' }));
                  }
                  break;
                
                case 'phase_advance':
                  if (json.next_action === 'start_assessment') {
                    setState(prev => ({ ...prev, phase: 'assessment' }));
                    setTimeout(() => startAssessment(), 1000);
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
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEventType = line.slice(6).trim();
          continue;
        }
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          
          try {
            const json = JSON.parse(data);
            
            // 根据事件类型处理
            switch (currentEventType) {
              // 教学模式事件
              case 'segment':
                if (json.message) {
                  // 工具增强：支持image_id
                  const msgId = `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
                  setState(prev => ({
                    ...prev,
                    messages: [...prev.messages, {
                      id: msgId,
                      role: 'ai',
                      content: json.message,
                      timestamp: new Date(),
                      phase: 'explain',
                      imageId: json.image_id,  // 添加图片ID
                    }],
                  }));
                }
                if (json.whiteboard) {
                  if (json.whiteboard.title) setWhiteboardTitle(json.whiteboard.title);
                  if (json.whiteboard.points) {
                    json.whiteboard.points.forEach((p: string) => addWhiteboardPoint(p));
                  }
                }
                break;
              
              // 工具增强事件（v2新增）
              case 'tool_call':
                console.log('[Tool Call]', json.tool_name, json.action);
                break;
              
              case 'tool_result':
                console.log('[Tool Result]', json.tool_name, json.success);
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
                  addWhiteboardPoint(json.content);
                }
                break;
              
              case 'phase_advance':
                if (json.next_action === 'start_assessment') {
                  setState(prev => ({ ...prev, phase: 'assessment' }));
                  setTimeout(() => startAssessment(), 1000);
                }
                break;
              
              case 'complete':
                if (json.next_action === 'start_assessment') {
                  setState(prev => ({ ...prev, phase: 'assessment' }));
                  setTimeout(() => startAssessment(), 1000);
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
        // 创建会话
        const startRes = await fetch('/api/v1/learning/start', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ course_id: 'MATH_JUNIOR_01' }),
        });
        
        if (!startRes.ok) throw new Error(`创建会话失败: ${startRes.status}`);
        
        const startData = await startRes.json();
        const sessionId = startData.data?.session_id;
        
        if (sessionId) {
          setState(prev => ({ ...prev, sessionId }));
          
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
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, [state.sessionId, state.isStreaming, state.phase, state.isFirstInput, state.useTools, addMessageNow, getAuthHeaders, queueMessage]);

  return (
    <div className="minimal-learning">
      <header className="minimal-header">
        <div className="header-content">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/center')} className="back-btn">
            学习中心
          </Button>
          <div className="header-right">
            <span className="header-topic">{state.currentTopic}</span>
            {/* 工具增强开关 */}
            <Button 
              type={state.useTools ? 'primary' : 'default'}
              size="small"
              icon={<ToolOutlined />}
              onClick={() => setState(prev => ({ ...prev, useTools: !prev.useTools }))}
              title={state.useTools ? '工具增强已启用' : '工具增强已禁用'}
              style={{ marginRight: 12 }}
            >
              {state.useTools ? '工具增强' : '标准模式'}
            </Button>
            <div className="user-info">
              <span className="user-name">{user?.name || '学生'}</span>
              <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout} className="logout-btn" title="退出登录" />
            </div>
          </div>
        </div>
      </header>

      <main className="minimal-main">
        <div className="chat-container" ref={chatRef}>
          {state.messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'ai' ? '👨‍🏫' : '👨‍🎓'}
              </div>
              <div className="message-content">
                {renderContentWithFormula(msg.content)}
                {/* 工具增强：显示教学图片 */}
                {msg.imageId && (
                  <TeachingImage 
                    imageId={msg.imageId}
                    alt="教学图片"
                    showDescription={true}
                  />
                )}
                {/* 展示评估结果详情 */}
                {msg.questionResults && msg.questionResults.length > 0 && (
                  <div className="assessment-results">
                    {msg.questionResults.map((qr, idx) => (
                      <div key={qr.question_id} className={`result-item ${qr.is_correct ? 'correct' : 'incorrect'}`}>
                        <div className="result-header">
                          <span className="result-index">第 {idx + 1} 题</span>
                          <span className={`result-status ${qr.is_correct ? 'correct' : 'incorrect'}`}>
                            {qr.is_correct ? '✓ 正确' : '✗ 错误'}
                          </span>
                        </div>
                        <div className="result-question">{renderContentWithFormula(qr.content)}</div>
                        <div className="result-answer">
                          <div className="answer-row">
                            <span className="answer-label">你的答案：</span>
                            <span className={qr.is_correct ? 'answer-correct' : 'answer-wrong'}>
                              {qr.student_answer}
                            </span>
                          </div>
                          {!qr.is_correct && (
                            <div className="answer-row">
                              <span className="answer-label">正确答案：</span>
                              <span className="answer-correct">
                                {Array.isArray(qr.correct_answer) ? qr.correct_answer.join('、') : qr.correct_answer}
                              </span>
                            </div>
                          )}
                        </div>
                        {qr.explanation && (
                          <div className="result-explanation">
                            <span className="explanation-label">💡 解题思路：</span>
                            <div className="explanation-content">{renderContentWithFormula(qr.explanation)}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {/* AI正在输入的加载指示器 */}
          {state.isStreaming && (
            <div className="message ai">
              <div className="message-avatar">👨‍🏫</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          
          {/* 评估题目显示 */}
          {state.phase === 'assessment' && state.assessmentQuestions.length > 0 && (
            <div className="assessment-panel">
              {state.assessmentQuestions.map((q, idx) => {
                // 判断题处理：如果没有选项，自动生成"正确"和"错误"两个选项
                const displayOptions = q.type === '判断题' && (!q.options || q.options.length === 0)
                  ? ['正确', '错误']
                  : q.options;
                
                return (
                  <div key={q.id} className="assessment-question">
                    <div className="question-header">第 {idx + 1} 题</div>
                    <div className="question-content">{renderContentWithFormula(q.content)}</div>
                    
                    {/* 选择题/判断题：显示选项按钮 */}
                    {displayOptions && displayOptions.length > 0 ? (
                      <div className="question-options">
                        {displayOptions.map((opt, optIdx) => {
                          // 检查选项是否已经包含字母前缀（如 "A. xxx" 或 "A、xxx"）
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
                      /* 填空题：显示输入框 */
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
          )}
        </div>
      </main>

      <footer className="minimal-footer">
        <div className="input-container">
          <textarea
            className="input-field"
            placeholder={state.phase === 'explain' ? '请输入你的问题...' : '请输入你的回答...'}
            disabled={state.isStreaming}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const target = e.target as HTMLTextAreaElement;
                if (target.value.trim()) {
                  handleSend(target.value.trim());
                  target.value = '';
                }
              }
            }}
          />
          <button
            className="send-btn"
            disabled={state.isStreaming}
            onClick={() => {
              const textarea = document.querySelector('.input-field') as HTMLTextAreaElement;
              if (textarea?.value.trim()) {
                handleSend(textarea.value.trim());
                textarea.value = '';
              }
            }}
          >
            发送
          </button>
        </div>
      </footer>
      
      <FloatingWhiteboard loading={state.isStreaming} />
    </div>
  );
};

export default MinimalLearning;
