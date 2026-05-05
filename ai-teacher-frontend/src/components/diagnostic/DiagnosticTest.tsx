/**
 * 诊断测试组件
 * 课前诊断，识别学生的知识起点
 */

import React, { useState, useEffect } from 'react';
import Button from 'antd/es/button';
import Progress from 'antd/es/progress';
import message from 'antd/es/message';
import Result from 'antd/es/result';
import Spin from 'antd/es/spin';
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import './DiagnosticTest.css';

export interface DiagnosticQuestion {
  id: string;
  content: string;
  type: 'point_click' | 'input' | 'choice';
  options?: Array<{ id: string; text: string }>;
  prerequisiteKpId?: string;
}

export interface DiagnosticResult {
  conclusion: 'full_mastery' | 'partial_mastery' | 'need_review' | 'full_learning';
  weakPrerequisites: string[];
  recommendedStartPhase: string;
}

interface DiagnosticTestProps {
  sessionId: string;
  onComplete: (result: DiagnosticResult) => void;
  onSkip?: () => void;
}

/**
 * 诊断测试组件
 */
const DiagnosticTest: React.FC<DiagnosticTestProps> = ({
  sessionId,
  onComplete,
  onSkip,
}) => {
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([]);
  const [targetKpName, setTargetKpName] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<DiagnosticResult | null>(null);

  // 加载诊断题目
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const res = await fetch(`/api/v1/diagnostic/session/${sessionId}/question`);
        if (res.ok) {
          const data = await res.json();
          if (data.success) {
            setQuestions(data.data.questions || []);
            setTargetKpName(data.data.target_kp_name || '知识点');
          }
        }
      } catch (error) {
        console.error('加载诊断题目失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (sessionId) {
      fetchQuestions();
    }
  }, [sessionId]);

  const currentQuestion = questions[currentIndex];
  const progress = questions.length > 0 ? ((currentIndex + 1) / questions.length) * 100 : 0;

  const handleAnswer = async (questionId: string, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
    
    // 提交答案到后端
    try {
      await fetch(`/api/v1/diagnostic/session/${sessionId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, answer }),
      });
    } catch (error) {
      console.error('提交答案失败', error);
    }
    
    // 自动进入下一题
    if (currentIndex < questions.length - 1) {
      setTimeout(() => {
        setCurrentIndex((prev) => prev + 1);
      }, 500);
    }
  };

  const handleComplete = async () => {
    setIsSubmitting(true);
    
    try {
      // 调用后端完成诊断
      const res = await fetch(`/api/v1/diagnostic/session/${sessionId}/complete`, {
        method: 'POST',
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          const diagnosticResult: DiagnosticResult = {
            conclusion: data.data.diagnostic_conclusion || 'full_learning',
            weakPrerequisites: data.data.weak_prerequisites || [],
            recommendedStartPhase: data.data.recommended_start_phase || 'concept_introduction',
          };
          setResult(diagnosticResult);
          setShowResult(true);
        }
      }
    } catch (error) {
      console.error('完成诊断失败', error);
      // 使用默认结果
      const diagnosticResult: DiagnosticResult = {
        conclusion: 'full_learning',
        weakPrerequisites: [],
        recommendedStartPhase: 'concept_introduction',
      };
      setResult(diagnosticResult);
      setShowResult(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleContinue = () => {
    if (result) {
      onComplete(result);
    }
  };

  // 当所有题目都已回答时，自动完成
  useEffect(() => {
    if (questions.length > 0 && Object.keys(answers).length === questions.length && !showResult && !isSubmitting) {
      handleComplete();
    }
  }, [answers, questions.length, showResult, isSubmitting]);

  if (loading) {
    return (
      <div className="diagnostic-test loading">
        <Spin tip="加载诊断题目..." />
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="diagnostic-test empty">
        <p>暂无诊断题目</p>
        <Button type="primary" onClick={() => onComplete({ conclusion: 'full_learning', weakPrerequisites: [], recommendedStartPhase: 'concept_introduction' })}>
          开始学习
        </Button>
      </div>
    );
  }

  if (showResult && result) {
    return (
      <div className="diagnostic-test result">
        <Result
          icon={
            result.conclusion === 'full_mastery' ? (
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
            ) : (
              <CloseCircleOutlined style={{ color: '#1890ff' }} />
            )
          }
          title={
            result.conclusion === 'full_mastery' 
              ? '太棒了！你已经掌握了前置知识' 
              : '让我们开始学习吧'
          }
          subTitle={
            result.conclusion === 'full_mastery'
              ? '可以直接跳过基础部分，进入进阶学习'
              : result.conclusion === 'partial_mastery'
              ? '你有不错的基础，我们来快速复习一下'
              : '让我们从头开始，打好基础'
          }
          extra={[
            <Button type="primary" key="continue" onClick={handleContinue}>
              {result.conclusion === 'full_mastery' ? '跳过基础' : '开始学习'}
            </Button>,
          ]}
        />
      </div>
    );
  }

  return (
    <div className="diagnostic-test">
      <div className="diagnostic-header">
        <h2>课前诊断</h2>
        <p className="diagnostic-subtitle">
          开始学习「{targetKpName}」前，先快速检测一下：
        </p>
        <Progress 
          percent={progress} 
          showInfo={false}
          strokeColor="#1890ff"
        />
        <p className="progress-text">
          {currentIndex + 1} / {questions.length}
        </p>
      </div>

      {currentQuestion && (
        <div className="diagnostic-question">
          <div className="question-content">
            {currentQuestion.content}
          </div>

          {currentQuestion.type === 'choice' && currentQuestion.options && (
            <div className="question-options">
              {currentQuestion.options.map((option) => (
                <button
                  key={option.id}
                  className={`option-btn ${answers[currentQuestion.id] === option.id ? 'selected' : ''}`}
                  onClick={() => handleAnswer(currentQuestion.id, option.id)}
                  disabled={!!answers[currentQuestion.id]}
                >
                  {option.text}
                </button>
              ))}
            </div>
          )}

          {currentQuestion.type === 'input' && (
            <div className="question-input">
              <input
                type="text"
                placeholder="请输入答案..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleAnswer(currentQuestion.id, (e.target as HTMLInputElement).value);
                  }
                }}
                disabled={!!answers[currentQuestion.id]}
              />
            </div>
          )}

          {currentQuestion.type === 'point_click' && (
            <div className="question-click-area">
              <p>请在坐标系中点击正确的位置</p>
              <div className="coordinate-plane">
                <div className="click-placeholder">
                  点击坐标交互区域
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="diagnostic-footer">
        {onSkip && (
          <Button type="link" onClick={onSkip}>
            跳过诊断，从头开始
          </Button>
        )}
      </div>

      {isSubmitting && (
        <div className="diagnostic-loading">
          <LoadingOutlined /> 正在分析结果...
        </div>
      )}
    </div>
  );
};

export default DiagnosticTest;