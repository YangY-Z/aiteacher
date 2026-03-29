import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, message } from 'antd';
import { LogoutOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import FloatingWhiteboard from '../components/whiteboard/FloatingWhiteboard';
import { useAuthStore, useLearningStore } from '../store';
import './MinimalLearning.css';

type LearningPhase = 'explain' | 'question' | 'feedback';

interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  phase?: LearningPhase;
}

interface LearningState {
  currentTopic: string;
  phase: LearningPhase;
  messages: Message[];
  isStreaming: boolean;
  sessionId: string | null;
}

// 渲染带有公式的内容
const renderContentWithFormula = (content: string): React.ReactNode => {
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
    while ((match = pattern.regex.exec(content)) !== null) {
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
  
  // 按位置排序
  allFormulas.sort((a, b) => a.start - b.start);
  
  // 构建渲染结果
  let lastIndex = 0;
  for (const formula of allFormulas) {
    // 添加公式前的文本
    if (formula.start > lastIndex) {
      parts.push(
        <span key={key++}>{content.slice(lastIndex, formula.start)}</span>
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
  if (lastIndex < content.length) {
    parts.push(<span key={key++}>{content.slice(lastIndex)}</span>);
  }
  
  return parts.length > 0 ? parts : content;
};

const MinimalLearning: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, token } = useAuthStore();
  const { setWhiteboardTitle, addWhiteboardPoint } = useLearningStore();
  
  const [state, setState] = useState<LearningState>({
    currentTopic: '一次函数',
    phase: 'explain',
    messages: [],
    isStreaming: false,
    sessionId: null,
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

  // 流式获取讲解内容
  const streamTeaching = async (sessionId: string) => {
    abortControllerRef.current = new AbortController();
    
    try {
      const res = await fetch(`/api/v1/learning/session/${sessionId}/teach/stream`, {
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
              
              if (currentEventType === 'segment' && json.message) {
                queueMessage(json.message, 'explain');
              }
              
              if (json.whiteboard) {
                if (json.whiteboard.title) setWhiteboardTitle(json.whiteboard.title);
                if (json.whiteboard.points) {
                  json.whiteboard.points.forEach((p: string) => addWhiteboardPoint(p));
                }
              }
              
              if (currentEventType === 'complete' || json.next_action === 'question') {
                setState(prev => ({ ...prev, phase: 'question' }));
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

  // 发送消息
  const handleSend = useCallback(async (content: string) => {
    if (state.isStreaming) return;
    
    addMessageNow('student', content, state.phase);
    setState(prev => ({ ...prev, isStreaming: true }));
    
    try {
      if (!state.sessionId) {
        const res = await fetch('/api/v1/learning/start', {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ course_id: 'MATH_JUNIOR_01' }),
        });
        
        if (!res.ok) throw new Error(`创建会话失败: ${res.status}`);
        
        const data = await res.json();
        const sessionId = data.data?.session_id;
        
        if (sessionId) {
          setState(prev => ({ ...prev, sessionId }));
          await streamTeaching(sessionId);
        }
      } else {
        const res = await fetch(`/api/v1/learning/session/${state.sessionId}/chat/stream`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ message: content }),
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
                if (json.content) {
                  queueMessage(json.content, 'feedback');
                }
                if (json.next_action === 'question') {
                  setState(prev => ({ ...prev, phase: 'question' }));
                }
              } catch (e) {}
            }
          }
        }
      }
    } catch (error: any) {
      console.error('发送失败:', error);
      message.error('发送失败，请重试');
    } finally {
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, [state.sessionId, state.isStreaming, state.phase, addMessageNow, getAuthHeaders, queueMessage]);

  // 初始化欢迎消息
  useEffect(() => {
    const timer = setTimeout(() => {
      queueMessage('你好！我是你的AI老师。今天我们来学习"一次函数"。准备好了吗？输入任何内容开始学习。', 'explain');
    }, 300);
    
    return () => clearTimeout(timer);
  }, []);

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
