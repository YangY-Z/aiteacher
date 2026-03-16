import React from 'react';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined, CheckOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import type { Message } from '../../types';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
  onSelectAnswer?: (questionId: string, answer: string) => void;
  selectedAnswer?: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onSelectAnswer,
  selectedAnswer 
}) => {
  const isAi = message.role === 'ai';

  const renderContent = () => {
    // 老师的文本提问（需要学生回复）
    if (message.type === 'teacher_question') {
      return (
        <div className="message-teacher-question">
          <div className="question-icon-pulse">
            <QuestionCircleOutlined />
          </div>
          <div className="question-text">{message.content}</div>
          <div className="question-hint">
            <span className="hint-dot"></span>
            请在下方输入框回答问题
          </div>
        </div>
      );
    }

    // 选择题（评估模式）
    if (message.type === 'question' && message.question) {
      return (
        <div className="message-question">
          <div className="question-content">{message.question.content}</div>
          <div className="question-options">
            {message.question.options.map((option, index) => {
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
          <span>{message.content}</span>
        </div>
      );
    }

    return <div className="message-text">{message.content}</div>;
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
