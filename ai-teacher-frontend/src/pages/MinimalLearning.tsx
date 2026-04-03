import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, message } from 'antd';
import { LogoutOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import FloatingWhiteboard from '../components/whiteboard/FloatingWhiteboard';
import { useAuthStore, useLearningStore } from '../store';
import './MinimalLearning.css';

type LearningPhase = 'explain' | 'question' | 'feedback' | 'assessment';

interface Question {
  id: string;
  type: string;
  content: string;
  options?: string[];
  difficulty?: string;
}

interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  phase?: LearningPhase;
  question?: Question;
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
  });
  
  const chatRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // 消息队列和显示控制
  const messageQueueRef = useRef<Array<{content: string, phase: LearningPhase}>>([]);
  const isDisplayingRef = useRef(false);

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
        
        // 显示评估开始消息（不在消息中显示具体题目，题目在评估面板中显示）
        addMessageNow('ai', `很好！让我们来做 ${questions.length} 道题检验一下学习效果：`, 'assessment');
      } else {
        addMessageNow('ai', '暂无评估题目，本节学习完成！', 'feedback');
        setState(prev => ({ ...prev, isStreaming: false, phase: 'explain' }));
      }
    } catch (error) {
      console.error('获取评估题目失败:', error);
      message.error('获取评估题目失败');
      setState(prev => ({ ...prev, isStreaming: false }));
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
        addMessageNow('ai', `评估完成！正确率：${result.correct_count}/${result.total_count} (${result.score}分)`, 'feedback');
        
        if (result.passed) {
          addMessageNow('ai', '恭喜你通过本次学习！可以进入下一个知识点的学习了。', 'feedback');
        } else {
          addMessageNow('ai', '还需要再努力一下，让我们重新学习这个知识点吧。', 'feedback');
        }
        
        setState(prev => ({
          ...prev,
          phase: 'explain',
          assessmentQuestions: [],
          isStreaming: false,
        }));
      }
    } catch (error) {
      console.error('提交评估失败:', error);
      message.error('提交评估失败');
      setState(prev => ({ ...prev, isStreaming: false }));
    }
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
                    queueMessage(json.message, 'explain');
                  }
                  if (json.whiteboard) {
                    if (json.whiteboard.title) setWhiteboardTitle(json.whiteboard.title);
                    if (json.whiteboard.points) {
                      json.whiteboard.points.forEach((p: string) => addWhiteboardPoint(p));
                    }
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
              case 'msg_feedback':
              case 'msg_supplement':
              case 'msg_encourage':
                if (json.content) {
                  queueMessage(json.content, 'feedback');
                }
                break;
              
              case 'wb_formulas':
                if (json.content) {
                  queueMessage(json.content, 'feedback');
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
          
          // 首次输入发送空消息，让后端开始教学
          const res = await fetch(`/api/v1/learning/session/${sessionId}/stream`, {
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
        const res = await fetch(`/api/v1/learning/session/${state.sessionId}/stream`, {
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
  }, [state.sessionId, state.isStreaming, state.phase, state.isFirstInput, addMessageNow, getAuthHeaders, queueMessage]);

  return (
    <div className="minimal-learning">
      <header className="minimal-header">
        <div className="header-content">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/center')} className="back-btn">
            学习中心
          </Button>
          <div className="header-right">
            <span className="header-topic">{state.currentTopic}</span>
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
              <div className="message-content">{renderContentWithFormula(msg.content)}</div>
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
              {state.assessmentQuestions.map((q, idx) => (
                <div key={q.id} className="assessment-question">
                  <div className="question-header">第 {idx + 1} 题</div>
                  <div className="question-content">{renderContentWithFormula(q.content)}</div>
                  
                  {/* 选择题：显示选项按钮 */}
                  {q.options && q.options.length > 0 ? (
                    <div className="question-options">
                      {q.options.map((opt, optIdx) => (
                        <button
                          key={optIdx}
                          className={`option-btn ${state.selectedAnswers[q.id] === opt ? 'selected' : ''}`}
                          onClick={() => selectAnswer(q.id, opt)}
                        >
                          {String.fromCharCode(65 + optIdx)}. {opt}
                        </button>
                      ))}
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
              ))}
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
