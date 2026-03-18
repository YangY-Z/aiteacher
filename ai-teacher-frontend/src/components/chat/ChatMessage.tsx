import React, { useState, useEffect, useRef } from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined, CheckOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import type { Message } from '../../types';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
  onSelectAnswer?: (questionId: string, answer: string) => void;
  selectedAnswer?: string;
  // 打字机速度（毫秒/字符），默认 50ms，模拟语音速度
  typewriterSpeed?: number;
  // 打字完成回调（学生消息也会触发，用于显示下一条）
  onTypingComplete?: (messageId: string) => void;
}

// 打字机 Hook
const useTypewriter = (text: string, speed: number = 50, enabled: boolean = true) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(!enabled);
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!enabled) {
      // 不启用打字机时，直接显示全部内容并标记完成
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    // 重置状态
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;

    const typeNextChar = () => {
      if (indexRef.current < text.length) {
        // 每次添加 1-2 个字符，模拟更自然的打字效果
        const charsToAdd = Math.min(
          Math.random() > 0.7 ? 2 : 1,
          text.length - indexRef.current
        );
        indexRef.current += charsToAdd;
        setDisplayedText(text.slice(0, indexRef.current));
        
        // 随机延迟，模拟真实语音节奏
        const delay = speed + Math.random() * 20 - 10;
        timerRef.current = setTimeout(typeNextChar, delay);
      } else {
        setIsComplete(true);
      }
    };

    // 开始打字
    timerRef.current = setTimeout(typeNextChar, speed);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [text, speed, enabled]);

  return { displayedText, isComplete };
};

// 简单的 Markdown 渲染器
const renderMarkdown = (text: string) => {
  // 处理 **粗体**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      // 粗体文本
      const boldText = part.slice(2, -2);
      return <strong key={index}>{boldText}</strong>;
    }
    return part;
  });
};

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onSelectAnswer,
  selectedAnswer,
  typewriterSpeed = 100,
  onTypingComplete
}) => {
  const isAi = message.role === 'ai';
  const hasTriggeredRef = useRef(false);
  
  // 对 AI 消息启用打字机效果（排除反馈消息）
  const enableTypewriter = isAi && message.type !== 'feedback';
  
  const { displayedText, isComplete } = useTypewriter(
    message.content,
    typewriterSpeed,
    enableTypewriter
  );

  // 消息完成时触发回调（AI打字完成 或 学生消息立即完成）
  useEffect(() => {
    // 防止重复触发
    if (isComplete && onTypingComplete && !hasTriggeredRef.current) {
      hasTriggeredRef.current = true;
      // 延迟一点触发，让学生消息有显示时间
      const delay = enableTypewriter ? 0 : 300;
      setTimeout(() => {
        onTypingComplete(message.id);
      }, delay);
    }
  }, [isComplete, enableTypewriter, message.id, onTypingComplete]);

  // 重置触发标记（当消息变化时）
  useEffect(() => {
    hasTriggeredRef.current = false;
  }, [message.id]);

  // 实际显示的内容
  const contentToShow = enableTypewriter ? displayedText : message.content;

  const renderContent = () => {
    // 老师的文本提问（需要学生回复）
    if (message.type === 'teacher_question') {
      return (
        <div className="message-teacher-question">
          <div className="question-icon-pulse">
            <QuestionCircleOutlined />
          </div>
          <div className="question-text">{renderMarkdown(contentToShow)}</div>
          {isComplete && (
            <div className="question-hint">
              <span className="hint-dot"></span>
              请在下方输入框回答问题
            </div>
          )}
        </div>
      );
    }

    // 选择题（评估模式）
    if (message.type === 'question' && message.question) {
      const options = message.question.options || [];
      const hasOptions = options.length > 0;
      
      return (
        <div className="message-question">
          <div className="question-content">{renderMarkdown(message.question.content || '')}</div>
          {hasOptions ? (
            <div className="question-options">
              {options.map((option, index) => {
                const optionKey = option.charAt(0);
                const isSelected = selectedAnswer === optionKey;
                
                return (
                  <div
                    key={index}
                    className={`question-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectAnswer?.(message.question!.id, optionKey)}
                  >
                    {option}
                    {isSelected && <CheckOutlined className="option-check" />}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="question-hint">
              <span className="hint-dot"></span>
              请在下方输入框填写答案
            </div>
          )}
        </div>
      );
    }

    if (message.type === 'feedback') {
      const isCorrect = message.content.includes('正确') || message.content.includes('✅');
      return (
        <div className={`message-feedback ${isCorrect ? 'correct' : 'incorrect'}`}>
          <span className="feedback-icon">
            {isCorrect ? '✅' : '❌'}
          </span>
          <span>{renderMarkdown(message.content)}</span>
        </div>
      );
    }

    return (
      <div className="message-text">
        {renderMarkdown(contentToShow)}
        {enableTypewriter && !isComplete && <span className="typing-cursor">|</span>}
      </div>
    );
  };

  return (
    <div className={`chat-message ${isAi ? 'ai-message' : 'student-message'} fade-in`}>
      {isAi && (
        <Avatar 
          className="message-avatar"
          icon={<RobotOutlined />}
          style={{ backgroundColor: '#4A90D9' }}
        />
      )}
      
      <div className="message-body">
        <div className="message-sender">
          {isAi ? 'AI老师' : '我'}
        </div>
        <div className="message-content">
          {renderContent()}
        </div>
        <div className="message-time">
          {message.timestamp.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>

      {!isAi && (
        <Avatar 
          className="message-avatar"
          icon={<UserOutlined />}
          style={{ backgroundColor: '#67C23A' }}
        />
      )}
    </div>
  );
};

export default ChatMessage;