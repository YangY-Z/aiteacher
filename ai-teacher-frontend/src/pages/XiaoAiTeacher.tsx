import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuthStore } from '../store';
import { chatApi } from '../api';
import './XiaoAiTeacher.css';

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface XiaoAiTeacherProps {
  onStartLearning?: (topic: string, kpId?: string) => void;
}

// 轮换展示的预设问题列表
const PRESET_QUESTIONS = [
  '我想学习一次函数',
  '我不太理解函数的概念',
  '帮我复习一下数学',
  '斜率和截距有什么区别？',
  '函数图像怎么画？',
];

const WELCOME_TEXT = '欢迎回来，今天又学习了什么新东西呀，快来和我说说吧！';

const XiaoAiTeacher: React.FC<XiaoAiTeacherProps> = ({ onStartLearning }) => {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [readyToLearn, setReadyToLearn] = useState(false);
  const [recommendedTopic, setRecommendedTopic] = useState<string>('');
  const [recommendedKpId, setRecommendedKpId] = useState<string>('');
  const [sessionId, setSessionId] = useState<string>('');
  
  // 打字机效果状态
  const [displayedText, setDisplayedText] = useState('');
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  
  // 引导语显示状态
  const [showGuide, setShowGuide] = useState(true);
  
  const chatRef = useRef<HTMLDivElement>(null);

  // 引导语5秒后自动消失
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowGuide(false);
    }, 5000);
    
    return () => clearTimeout(timer);
  }, []);

  // 打字机效果（仅用于预设问题）
  useEffect(() => {
    const currentText = PRESET_QUESTIONS[currentTextIndex];
    
    // 暂停后开始删除或下一个
    if (isPaused) {
      const pauseTimer = setTimeout(() => {
        setIsPaused(false);
        setIsDeleting(true);
      }, 2000);
      
      return () => clearTimeout(pauseTimer);
    }
    
    // 删除效果
    if (isDeleting) {
      if (displayedText.length === 0) {
        setIsDeleting(false);
        // 循环到下一个文本
        setCurrentTextIndex((prev) => (prev + 1) % PRESET_QUESTIONS.length);
        return;
      }
      
      const deleteTimer = setTimeout(() => {
        setDisplayedText(prev => prev.slice(0, -1));
      }, 30);
      
      return () => clearTimeout(deleteTimer);
    }
    
    // 打字效果
    if (displayedText.length < currentText.length) {
      const typeTimer = setTimeout(() => {
        setDisplayedText(currentText.slice(0, displayedText.length + 1));
      }, 60);
      
      return () => clearTimeout(typeTimer);
    } else {
      // 打字完成，开始暂停
      setIsPaused(true);
    }
  }, [displayedText, currentTextIndex, isDeleting, isPaused]);

  // 自动滚动到底部
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  // 发送消息
  const handleSend = useCallback(async () => {
    const content = inputValue.trim();
    if (!content || isTyping) return;

    // 添加用户消息
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // 调用真实API
      const response = await chatApi.recommend({
        message: content,
        session_id: sessionId || undefined,
        student_id: user?.id,
      });

      const data = response.data.data;
      
      // 更新session_id
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // 添加AI回复
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: data.reply,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, aiMessage]);

      // 检查是否准备好学习
      if (data.is_ready && data.recommended_kp) {
        setReadyToLearn(true);
        setRecommendedTopic(data.recommended_kp_name || '');
        setRecommendedKpId(data.recommended_kp);
      }
    } catch (error) {
      console.error('API调用失败:', error);
      // 降级处理：显示错误提示
      const errorMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: '抱歉，我遇到了一些问题。请稍后再试，或者直接去陪伴学习页面开始学习吧！',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, [inputValue, isTyping, sessionId, user?.id]);

  // 开始学习
  const handleStartLearning = () => {
    if (onStartLearning && recommendedTopic) {
      onStartLearning(recommendedTopic, recommendedKpId);
    }
  };

  // 键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 点击预设问题
  const handleTextClick = () => {
    setInputValue(displayedText);
  };

  return (
    <div className="xiaoai-teacher">
      {/* 右上角引导语 */}
      {showGuide && (
        <div className="guide-tip">
          <span className="guide-icon">💡</span>
          <span>在下方输入框开始对话，或点击上方的预设问题</span>
        </div>
      )}

      {/* 呼吸圆球区域 */}
      <div className="orb-container">
        <div className="orb-wrapper">
          <div className="orb-glow"></div>
          <div className="orb">
            <div className="orb-inner"></div>
            <div className="orb-pulse"></div>
          </div>
        </div>
        <div 
          className="preset-text"
          onClick={handleTextClick}
        >
          <span className="text-content">
            {displayedText}
            <span className="cursor">|</span>
          </span>
          <span className="click-hint">点击可快速发送</span>
        </div>
      </div>

      {/* 对话区域 */}
      <div className="chat-area" ref={chatRef}>
        {messages.length > 0 && (
          <div className="message-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-item ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'ai' ? '🤖' : '👤'}
                </div>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {isTyping && (
              <div className="message-item ai typing">
                <div className="message-avatar">🤖</div>
                <div className="message-content typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 开始学习按钮 */}
      {readyToLearn && (
        <div className="start-learning-banner">
          <div className="banner-content">
            <span className="banner-icon">🎯</span>
            <span className="banner-text">已为你推荐：<strong>{recommendedTopic}</strong></span>
          </div>
          <button className="start-learning-btn" onClick={handleStartLearning}>
            开始学习
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      )}

      {/* 输入区域 */}
      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            className="chat-input"
            placeholder={WELCOME_TEXT}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isTyping}
            rows={1}
          />
          <button
            className="send-button"
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default XiaoAiTeacher;
