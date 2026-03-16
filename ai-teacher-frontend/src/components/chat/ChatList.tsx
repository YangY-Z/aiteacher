import React, { useRef, useEffect } from 'react';
import { Spin } from 'antd';
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

  // 自动滚动到底部
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="chat-list" ref={listRef}>
      {messages.length === 0 && !isLoading && (
        <div className="chat-empty">
          <div className="empty-icon">👋</div>
          <div className="empty-title">欢迎来到AI虚拟教师</div>
          <div className="empty-desc">点击"开始学习"开始你的学习之旅</div>
        </div>
      )}

      {messages.map((message) => (
        <ChatMessage 
          key={message.id} 
          message={message} 
          onSelectAnswer={onSelectAnswer}
          selectedAnswer={message.question ? selectedAnswers[message.question.id] : undefined}
        />
      ))}

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
