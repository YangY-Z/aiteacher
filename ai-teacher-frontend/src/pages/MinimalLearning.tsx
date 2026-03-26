import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, message, Spin } from 'antd';
import MinimalChat from '../components/chat/MinimalChat';
import MinimalProgress from '../components/progress/MinimalProgress';
import './MinimalLearning.css';

/**
 * 极简版学习页面
 * 
 * 核心设计：
 * 1. 单列居中布局
 * 2. 三步循环：讲解 → 提问 → 反馈
 * 3. 流式对话，打字机效果
 */

// 学习阶段
type LearningPhase = 'explain' | 'question' | 'feedback';

// 消息类型
interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  timestamp: Date;
  phase?: LearningPhase;
}

// 简化的状态
interface LearningState {
  currentTopic: string;
  phase: LearningPhase;
  messages: Message[];
  isStreaming: boolean;
  sessionId: string | null;
}

// 知识点数据（10 个核心模块）
const KNOWLEDGE_MODULES = [
  { id: '1', name: '函数概念', status: 'completed' as const },
  { id: '2', name: '一次函数', status: 'current' as const },
  { id: '3', name: '斜率计算', status: 'locked' as const },
  { id: '4', name: '截距理解', status: 'locked' as const },
  { id: '5', name: '图像绘制', status: 'locked' as const },
  { id: '6', name: '性质应用', status: 'locked' as const },
  { id: '7', name: '实际问题', status: 'locked' as const },
  { id: '8', name: '综合练习', status: 'locked' as const },
  { id: '9', name: '单元测试', status: 'locked' as const },
  { id: '10', name: '拓展提升', status: 'locked' as const },
];

const MinimalLearning: React.FC = () => {
  // 核心状态
  const [currentModule, setCurrentModule] = useState(2);
  const [state, setState] = useState<LearningState>({
    currentTopic: '一次函数',
    phase: 'explain',
    messages: [],
    isStreaming: false,
    sessionId: null,
  });
  
  const chatRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [state.messages]);

  // 添加消息
  const addMessage = useCallback((msg: Omit<Message, 'id' | 'timestamp'>) => {
    const newMsg: Message = {
      ...msg,
      id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      timestamp: new Date(),
    };
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, newMsg],
    }));
    return newMsg.id;
  }, []);

  // 更新最后一条消息（用于流式）
  const updateLastMessage = useCallback((content: string) => {
    setState(prev => {
      const messages = [...prev.messages];
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        };
      }
      return { ...prev, messages };
    });
  }, []);

  // 开始学习会话
  const startSession = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isStreaming: true }));
      
      // 创建会话
      const res = await fetch('/api/v1/learning/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_id: 'linear-function' }),
      });
      
      if (!res.ok) {
        throw new Error('启动失败');
      }
      
      const data = await res.json();
      const sessionId = data.data?.session_id;
      
      if (sessionId) {
        setState(prev => ({ ...prev, sessionId }));
        // 开始讲解
        await fetchExplain(sessionId);
      }
    } catch (error) {
      console.error('启动失败:', error);
      message.error('启动失败，请刷新重试');
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, []);

  // 流式获取讲解内容
  const fetchExplain = async (sessionId: string) => {
    abortControllerRef.current = new AbortController();
    
    // 添加AI消息占位
    const msgId = addMessage({ role: 'ai', content: '', phase: 'explain' });
    let fullContent = '';
    
    try {
      const res = await fetch(`/api/v1/learning/${sessionId}/explain`, {
        signal: abortControllerRef.current.signal,
      });
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) return;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            
            try {
              const json = JSON.parse(data);
              if (json.content) {
                fullContent += json.content;
                updateLastMessage(fullContent);
              }
              if (json.next_action === 'question') {
                setState(prev => ({ ...prev, phase: 'question' }));
              }
            } catch {
              // 非JSON，作为纯文本处理
              fullContent += data;
              updateLastMessage(fullContent);
            }
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

  // 发送学生回答
  const handleSend = useCallback(async (content: string) => {
    if (!state.sessionId || state.isStreaming) return;
    
    // 添加学生消息
    addMessage({ role: 'student', content, phase: state.phase });
    
    // 获取AI反馈
    setState(prev => ({ ...prev, isStreaming: true }));
    abortControllerRef.current = new AbortController();
    
    const msgId = addMessage({ role: 'ai', content: '', phase: 'feedback' });
    let fullContent = '';
    
    try {
      const res = await fetch(`/api/v1/learning/${state.sessionId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
        signal: abortControllerRef.current.signal,
      });
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) return;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            
            try {
              const json = JSON.parse(data);
              if (json.content) {
                fullContent += json.content;
                updateLastMessage(fullContent);
              }
              if (json.next_action === 'question') {
                setState(prev => ({ ...prev, phase: 'question' }));
              } else if (json.next_action === 'explain') {
                setState(prev => ({ ...prev, phase: 'explain' }));
              }
            } catch {
              fullContent += data;
              updateLastMessage(fullContent);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('发送失败:', error);
        message.error('发送失败，请重试');
      }
    } finally {
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, [state.sessionId, state.isStreaming, state.phase, addMessage, updateLastMessage]);

  // 初始启动
  useEffect(() => {
    // 显示欢迎消息
    addMessage({
      role: 'ai',
      content: '你好！我是你的AI老师。今天我们来学习"一次函数"。准备好了吗？输入任何内容开始学习。',
      phase: 'explain',
    });
  }, []);

  return (
    <div className="minimal-learning">
      {/* 顶部标题栏 */}
      <header className="minimal-header">
        <div className="header-content">
          <h1 className="header-title">AI教师</h1>
          <span className="header-topic">当前学习：{state.currentTopic}</span>
        </div>
      </header>

      {/* 主聊天区域 */}
      <main className="minimal-main">
        <div className="chat-container" ref={chatRef}>
          {state.messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'ai' ? '👨‍🏫' : '👨‍🎓'}
              </div>
              <div className="message-content">
                {msg.content || <Spin size="small" />}
              </div>
            </div>
          ))}
          
          {state.isStreaming && state.messages.length > 0 && 
           state.messages[state.messages.length - 1].role === 'ai' && 
           !state.messages[state.messages.length - 1].content && (
            <div className="message ai">
              <div className="message-avatar">👨‍🏫</div>
              <div className="message-content">
                <Spin size="small" />
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 底部输入区 */}
      <footer className="minimal-footer">
        <div className="input-container">
          <textarea
            className="input-field"
            placeholder={
              state.phase === 'explain' ? '请输入你的问题...' :
              state.phase === 'question' ? '请输入你的回答...' :
              '请输入你的想法...'
            }
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
    </div>
  );
};

export default MinimalLearning;
