import React from 'react';
import './MinimalChat.css';

interface Message {
  id: string;
  role: 'ai' | 'student';
  content: string;
  options?: string[];
  selectedOption?: number;
  isCorrect?: boolean;
}

interface MinimalChatProps {
  messages: Message[];
  onOptionSelect?: (index: number) => void;
  isLoading?: boolean;
}

const MinimalChat: React.FC<MinimalChatProps> = ({ 
  messages, 
  onOptionSelect,
  isLoading 
}) => {
  return (
    <div className="minimal-chat">
      {messages.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'ai' ? '🤖' : '👤'}
          </div>
          <div className="message-content">
            <div className="message-text">{msg.content}</div>
            
            {/* 选择题选项 */}
            {msg.options && (
              <div className="message-options">
                {msg.options.map((option, idx) => (
                  <button
                    key={idx}
                    className={`option-btn ${msg.selectedOption === idx ? 'selected' : ''} ${
                      msg.selectedOption !== undefined && idx === msg.options.findIndex(o => o.includes('✅')) ? 'correct' : ''
                    } ${
                      msg.selectedOption === idx && msg.isCorrect === false ? 'incorrect' : ''
                    }`}
                    onClick={() => onOptionSelect?.(idx)}
                    disabled={msg.selectedOption !== undefined}
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
      
      {isLoading && (
        <div className="message ai">
          <div className="message-avatar">🤖</div>
          <div className="message-content">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MinimalChat;
