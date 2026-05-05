import React, { useRef, useEffect, useState, useCallback } from 'react';
import Spin from 'antd/es/spin';
import ChatMessage from './ChatMessage';
import { useLearningStore } from '../../store';
import './ChatList.css';

interface ChatListProps {
  onSelectAnswer?: (questionId: string, answer: string) => void;
  selectedAnswers?: Record<string, string>;
}

const ChatList: React.FC<ChatListProps> = ({ onSelectAnswer, selectedAnswers = {} }) => {
  const { messages, isLoading } = useLearningStore();
  const listRef = useRef<HTMLDivElement>(null);
  
  // 当前可见的消息数量
  const [visibleCount, setVisibleCount] = useState(0);

  // 自动滚动到底部
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [visibleCount]);

  // 重置状态
  useEffect(() => {
    if (messages.length === 0) {
      setVisibleCount(0);
    }
  }, [messages.length]);

  // 初始化：显示第一条消息
  useEffect(() => {
    if (messages.length > 0 && visibleCount === 0) {
      setVisibleCount(1);
    }
  }, [messages.length, visibleCount]);

  // 显示下一条消息
  const showNextMessage = useCallback(() => {
    setVisibleCount(prev => Math.min(prev + 1, messages.length));
  }, [messages.length]);

  // 处理消息完成（打字完成或学生消息直接完成）
  const handleMessageComplete = useCallback((messageId: string) => {
    // 延迟显示下一条
    setTimeout(() => {
      showNextMessage();
    }, 300);
  }, [showNextMessage]);

  // 获取当前应该显示的消息
  const visibleMessages = messages.slice(0, visibleCount);

  return (
    <div className="chat-list" ref={listRef}>
      {messages.length === 0 && !isLoading && (
        <div className="chat-empty">
          <div className="empty-icon">👋</div>
          <div className="empty-title">欢迎来到AI虚拟教师</div>
          <div className="empty-desc">点击"开始学习"开始你的学习之旅</div>
        </div>
      )}

      {visibleMessages.map((message, index) => {
        const isLastVisible = index === visibleMessages.length - 1;
        
        // 最后一条消息需要触发完成回调来显示下一条
        const needCompleteCallback = isLastVisible && visibleCount < messages.length;
        
        return (
          <ChatMessage 
            key={message.id} 
            message={message} 
            onSelectAnswer={onSelectAnswer}
            selectedAnswer={message.question ? selectedAnswers[message.question.id] : undefined}
            typewriterSpeed={100}
            onTypingComplete={needCompleteCallback ? handleMessageComplete : undefined}
          />
        );
      })}

      {isLoading && (
        <div className="chat-loading">
          <div className="loading-content">
            <Spin />
            <span className="loading-text">AI老师正在思考中...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatList;
