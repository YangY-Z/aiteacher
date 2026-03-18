/**
 * 微练习组件
 * 2分钟快速复习，2-3道题
 */

import React, { useState } from 'react';
import { Button, Progress, Result, Spin } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import './MicroPractice.css';

export interface MicroPracticeQuestion {
  id: string;
  content: string;
  options: string[];
  correctAnswer: string;
}

export interface MicroPracticeData {
  id: string;
  kpId: string;
  kpName: string;
  questions: MicroPracticeQuestion[];
  estimatedTime: number;
}

interface MicroPracticeProps {
  practice: MicroPracticeData;
  onComplete: (score: number) => void;
  onSkip?: () => void;
}

/**
 * 微练习组件
 */
const MicroPractice: React.FC<MicroPracticeProps> = ({
  practice,
  onComplete,
  onSkip,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQuestion = practice.questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = (answeredCount / practice.questions.length) * 100;

  const handleAnswer = (questionId: string, answer: string) => {
    setAnswers((prev) => {
      const newAnswers = { ...prev, [questionId]: answer };
      
      // 检查是否全部回答完成
      if (Object.keys(newAnswers).length === practice.questions.length) {
        // 自动提交
        setTimeout(() => {
          submitPractice(newAnswers);
        }, 500);
      } else {
        // 进入下一题
        setTimeout(() => {
          setCurrentIndex((prev) => prev + 1);
        }, 300);
      }
      
      return newAnswers;
    });
  };

  const submitPractice = async (finalAnswers: Record<string, string>) => {
    setIsSubmitting(true);
    
    // 计算得分
    let correctCount = 0;
    practice.questions.forEach((q) => {
      if (finalAnswers[q.id] === q.correctAnswer) {
        correctCount++;
      }
    });
    
    const score = correctCount / practice.questions.length;
    
    // 模拟提交延迟
    setTimeout(() => {
      setShowResult(true);
      setIsSubmitting(false);
      onComplete(score);
    }, 500);
  };

  if (showResult) {
    const correctCount = practice.questions.filter(
      (q) => answers[q.id] === q.correctAnswer
    ).length;
    
    return (
      <div className="micro-practice result">
        <Result
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          title="练习完成！"
          subTitle={`答对 ${correctCount}/${practice.questions.length} 题`}
          extra={[
            <Button type="primary" key="done" onClick={() => onComplete(correctCount / practice.questions.length)}>
              完成
            </Button>,
          ]}
        />
      </div>
    );
  }

  if (isSubmitting) {
    return (
      <div className="micro-practice loading">
        <Spin tip="提交中..." />
      </div>
    );
  }

  return (
    <div className="micro-practice">
      <div className="practice-header">
        <div className="kp-info">
          <span className="kp-name">{practice.kpName}</span>
          <span className="time-info">
            <ClockCircleOutlined /> 约{Math.round(practice.estimatedTime / 60)}分钟
          </span>
        </div>
        <Progress 
          percent={progress} 
          showInfo={false}
          strokeColor="#52c41a"
          size="small"
        />
        <p className="progress-text">
          {answeredCount} / {practice.questions.length}
        </p>
      </div>

      <div className="question-section">
        <div className="question-number">第 {currentIndex + 1} 题</div>
        <div className="question-content">{currentQuestion.content}</div>
        
        <div className="options-list">
          {currentQuestion.options.map((option, idx) => (
            <button
              key={idx}
              className={`option-btn ${answers[currentQuestion.id] === option ? 'selected' : ''}`}
              onClick={() => handleAnswer(currentQuestion.id, option)}
              disabled={!!answers[currentQuestion.id]}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {onSkip && (
        <div className="practice-footer">
          <Button type="link" onClick={onSkip}>
            跳过
          </Button>
        </div>
      )}
    </div>
  );
};

export default MicroPractice;
