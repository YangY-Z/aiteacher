/**
 * 结构化对话组件
 * 用选择题替代开放式问题，引导学生表达
 */

import React, { useState } from 'react';
import { Button, Input } from 'antd';
import './StructuredChat.css';

const { TextArea } = Input;

export interface ChatOption {
  id: string;
  text: string;
  type?: 'reason' | 'answer' | 'feedback' | 'skip';
  isCorrect?: boolean;
}

export interface SelectionResult {
  selectedOption: string;
  customInput?: string;
}

interface StructuredChatProps {
  options: ChatOption[];
  onSelection: (result: SelectionResult) => void;
  question?: string;
  allowCustomInput?: boolean;
  allowSkip?: boolean;
  disabled?: boolean;
}

/**
 * 结构化对话组件
 * 用选择题替代开放式问题，引导学生表达
 */
const StructuredChat: React.FC<StructuredChatProps> = ({
  options,
  onSelection,
  question,
  allowCustomInput = true,
  allowSkip = true,
  disabled = false,
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  const handleOptionClick = (optionId: string) => {
    if (disabled) return;
    
    setSelectedOption(optionId);
    
    if (optionId === 'custom') {
      setShowCustomInput(true);
    } else {
      onSelection({
        selectedOption: optionId,
      });
    }
  };

  const handleCustomSubmit = () => {
    if (!customInput.trim()) return;
    
    onSelection({
      selectedOption: 'custom',
      customInput: customInput.trim(),
    });
    
    setCustomInput('');
    setShowCustomInput(false);
  };

  // 合并选项和自定义选项
  const allOptions = [...options];
  if (allowCustomInput) {
    allOptions.push({
      id: 'custom',
      text: '其他（请简短说明）',
      type: 'reason' as const,
    });
  }
  if (allowSkip) {
    allOptions.push({
      id: 'skip',
      text: '直接告诉我答案',
      type: 'skip' as const,
    });
  }

  return (
    <div className="structured-chat">
      {question && (
        <div className="structured-question">
          {question}
        </div>
      )}
      
      <div className="options-container">
        {allOptions.map((option) => (
          <button
            key={option.id}
            className={`option-btn ${selectedOption === option.id ? 'selected' : ''} ${option.type || ''}`}
            onClick={() => handleOptionClick(option.id)}
            disabled={disabled}
          >
            <span className="option-icon">
              {option.type === 'skip' ? '⏭️' : 
               option.type === 'reason' ? '💭' : 
               option.type === 'feedback' ? '👍' : '📌'}
            </span>
            <span className="option-text">{option.text}</span>
          </button>
        ))}
      </div>

      {showCustomInput && (
        <div className="custom-input-area">
          <TextArea
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder="请简短说明..."
            rows={2}
            disabled={disabled}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleCustomSubmit();
              }
            }}
          />
          <Button 
            type="primary" 
            onClick={handleCustomSubmit}
            disabled={disabled || !customInput.trim()}
          >
            提交
          </Button>
        </div>
      )}
    </div>
  );
};

export default StructuredChat;
