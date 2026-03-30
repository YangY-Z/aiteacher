import React, { useEffect, useMemo, useState } from 'react';
import { useAuthStore, useCourseStore, useImprovementStore } from '../store';
import { courseApi, improvementApi } from '../api';
import type { ImprovementPlanStep, QuizQuestion } from '../types';
import './Improvement.css';

const stageMap: Record<string, number> = {
  uploading: 0,
  analyzing: 1,
  clarifying: 1,
  diagnosed: 2,
  planning: 2,
  learning: 3,
  quiz: 4,
  completed: 5,
};

const stageLabels = [
  { title: '录入成绩', icon: '📝' },
  { title: '诊断分析', icon: '🔍' },
  { title: '生成方案', icon: '📋' },
  { title: '分步学习', icon: '📚' },
  { title: '最终小测', icon: '✍️' },
  { title: '完成', icon: '🎉' },
];

const Improvement: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const { currentCourse, setCurrentCourse } = useCourseStore();
  const { session, setSession, quiz, setQuiz, stepContent, setStepContent, isLoading, setLoading, reset } = useImprovementStore();

  const [formData, setFormData] = useState({
    exam_name: '',
    score: 0,
    total_score: 100,
    error_description: '',
    available_time: 30,
    difficulty: 'normal' as 'basic' | 'normal' | 'challenge',
    foundation: 'average' as 'weak' | 'average' | 'good',
    max_clarification_rounds: 3,
  });
  const [clarifyAnswer, setClarifyAnswer] = useState('');
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      window.location.href = '/login';
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const loadCourse = async () => {
      if (currentCourse) return;
      try {
        const res = await courseApi.getAll();
        if (res.data.success && res.data.data.length > 0) {
          setCurrentCourse(res.data.data[0]);
        }
      } catch {
        console.error('加载课程失败');
      }
    };
    loadCourse();
  }, [currentCourse, setCurrentCourse]);

  useEffect(() => {
    return () => {
      reset();
    };
  }, [reset]);

  const currentStage = useMemo(() => {
    if (!session) return 0;
    return stageMap[session.status] ?? 0;
  }, [session]);

  const startImprovement = async () => {
    if (!currentCourse) {
      setError('请先选择课程');
      return;
    }
    if (!formData.exam_name.trim()) {
      setError('请输入试卷/作业名称');
      return;
    }
    if (formData.score <= 0 || formData.total_score <= 0) {
      setError('请输入有效的分数');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      const res = await improvementApi.startSession({
        course_id: currentCourse.id,
        score_input: {
          exam_name: formData.exam_name,
          score: formData.score,
          total_score: formData.total_score,
          error_description: formData.error_description || undefined,
          available_time: formData.available_time,
          difficulty: formData.difficulty,
          foundation: formData.foundation,
          max_clarification_rounds: formData.max_clarification_rounds,
        },
      });
      setSession(res.data.data);
    } catch {
      setError('创建专项提升会话失败');
    } finally {
      setLoading(false);
    }
  };

  const submitClarification = async () => {
    if (!session || !clarifyAnswer.trim()) return;
    try {
      setLoading(true);
      const res = await improvementApi.submitClarification(session.session_id, clarifyAnswer.trim());
      setSession(res.data.data);
      setClarifyAnswer('');
    } catch {
      setError('提交澄清回答失败');
    } finally {
      setLoading(false);
    }
  };

  const generatePlan = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const res = await improvementApi.generatePlan(session.session_id);
      setSession(res.data.data);
    } catch {
      setError('生成学习方案失败');
    } finally {
      setLoading(false);
    }
  };

  const startStep = async (step: ImprovementPlanStep) => {
    if (!session) return;
    try {
      setLoading(true);
      const res = await improvementApi.startStep(session.session_id, step.step_order);
      setStepContent(res.data.data);
    } catch {
      setError('加载学习步骤失败');
    } finally {
      setLoading(false);
    }
  };

  const completeStep = async (step: ImprovementPlanStep) => {
    if (!session) return;
    try {
      setLoading(true);
      const res = await improvementApi.completeStep(session.session_id, step.step_order);
      setSession(res.data.data);
      setStepContent(null);
    } catch {
      setError('完成学习步骤失败');
    } finally {
      setLoading(false);
    }
  };

  const loadQuiz = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const res = await improvementApi.getQuiz(session.session_id);
      setQuiz(res.data.data);
    } catch {
      setError('获取小测失败');
    } finally {
      setLoading(false);
    }
  };

  const submitQuiz = async () => {
    if (!session || !quiz) return;
    try {
      setLoading(true);
      const answers = Object.entries(quizAnswers).map(([question_id, answer]) => ({ question_id, answer }));
      await improvementApi.submitQuiz(session.session_id, answers);
      const refreshed = await improvementApi.getSession(session.session_id);
      setSession(refreshed.data.data);
      setQuiz(null);
    } catch {
      setError('提交小测失败');
    } finally {
      setLoading(false);
    }
  };

  const renderUpload = () => (
    <div className="improvement-card">
      <div className="card-header">
        <h3>📝 录入成绩并开始专项提升</h3>
      </div>
      <div className="card-body">
        <div className="form-grid">
          <div className="form-item">
            <label>试卷/作业名称</label>
            <input
              type="text"
              placeholder="如：一次函数单元测验"
              value={formData.exam_name}
              onChange={(e) => setFormData({ ...formData, exam_name: e.target.value })}
            />
          </div>
          <div className="form-item small">
            <label>得分</label>
            <input
              type="number"
              min={0}
              value={formData.score}
              onChange={(e) => setFormData({ ...formData, score: Number(e.target.value) })}
            />
          </div>
          <div className="form-item small">
            <label>满分</label>
            <input
              type="number"
              min={1}
              value={formData.total_score}
              onChange={(e) => setFormData({ ...formData, total_score: Number(e.target.value) })}
            />
          </div>
        </div>
        
        <div className="form-item full">
          <label>错题描述 / 老师评语</label>
          <textarea
            rows={4}
            placeholder="可填写主要丢分点、老师评语、自己觉得不会的题型"
            value={formData.error_description}
            onChange={(e) => setFormData({ ...formData, error_description: e.target.value })}
          />
        </div>
        
        <div className="form-grid">
          <div className="form-item small">
            <label>可投入时间（分钟）</label>
            <input
              type="number"
              min={10}
              max={180}
              value={formData.available_time}
              onChange={(e) => setFormData({ ...formData, available_time: Number(e.target.value) })}
            />
          </div>
          <div className="form-item small">
            <label>最多追问次数</label>
            <input
              type="number"
              min={1}
              max={5}
              value={formData.max_clarification_rounds}
              onChange={(e) => setFormData({ ...formData, max_clarification_rounds: Number(e.target.value) })}
            />
          </div>
          <div className="form-item small">
            <label>期望难度</label>
            <select
              value={formData.difficulty}
              onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as 'basic' | 'normal' | 'challenge' })}
            >
              <option value="basic">基础巩固</option>
              <option value="normal">常规提升</option>
              <option value="challenge">挑战提高</option>
            </select>
          </div>
          <div className="form-item small">
            <label>自评基础</label>
            <select
              value={formData.foundation}
              onChange={(e) => setFormData({ ...formData, foundation: e.target.value as 'weak' | 'average' | 'good' })}
            >
              <option value="weak">薄弱</option>
              <option value="average">一般</option>
              <option value="good">较好</option>
            </select>
          </div>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <button className="btn btn-primary" onClick={startImprovement} disabled={isLoading}>
          {isLoading ? '处理中...' : '开始诊断'}
        </button>
      </div>
    </div>
  );

  const renderClarifying = () => {
    const latest = session?.clarification_rounds?.[session.clarification_rounds.length - 1];
    return (
      <div className="improvement-card">
        <div className="card-header">
          <h3>🔍 进一步澄清薄弱点</h3>
          {session && (
            <span className="round-badge">
              {session.clarification_rounds.length}/{session.max_clarification_rounds}
            </span>
          )}
        </div>
        <div className="card-body">
          {session?.clarification_rounds.map((item, index) => (
            <div key={item.round_number} className="clarify-item">
              <div className="clarify-question">
                <span className="label">系统追问：</span>
                <span>{item.system_question}</span>
              </div>
              {item.student_answer && (
                <div className="clarify-answer">
                  <span className="label">你的回答：</span>
                  <span>{item.student_answer}</span>
                </div>
              )}
            </div>
          ))}
          {latest && !latest.student_answer && (
            <div className="clarify-input">
              <input
                type="text"
                value={clarifyAnswer}
                onChange={(e) => setClarifyAnswer(e.target.value)}
                placeholder="请回答系统问题"
                onKeyPress={(e) => e.key === 'Enter' && submitClarification()}
              />
              <button className="btn btn-primary" onClick={submitClarification} disabled={isLoading || !clarifyAnswer.trim()}>
                提交
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDiagnosis = () => (
    <div className="improvement-card">
      <div className="card-header">
        <h3>🎯 诊断结果</h3>
      </div>
      <div className="card-body">
        <div className="diagnosis-result">
          <h4>{session?.diagnosis?.target_kp_name}</h4>
          <p className="diagnosis-reason">{session?.diagnosis?.reason}</p>
          <div className="confidence-bar">
            <span className="confidence-label">置信度</span>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${Math.round((session?.diagnosis?.confidence || 0) * 100)}%` }}
              />
            </div>
            <span className="confidence-value">{Math.round((session?.diagnosis?.confidence || 0) * 100)}%</span>
          </div>
          {session?.diagnosis?.prerequisite_gaps && session.diagnosis.prerequisite_gaps.length > 0 && (
            <div className="gaps-section">
              <span className="gaps-label">前置知识缺口：</span>
              <div className="gaps-tags">
                {session.diagnosis.prerequisite_gaps.map((item) => (
                  <span key={item} className="gap-tag">{item}</span>
                ))}
              </div>
            </div>
          )}
        </div>
        <button className="btn btn-primary" onClick={generatePlan} disabled={isLoading}>
          生成学习方案
        </button>
      </div>
    </div>
  );

  const renderPlan = () => {
    const content = (stepContent?.content as Record<string, unknown> | undefined) ?? {};
    const whiteboard = (stepContent?.whiteboard as Record<string, unknown> | undefined) ?? {};
    const knowledgePoint = (stepContent?.knowledge_point as Record<string, unknown> | undefined) ?? {};
    const formulas = Array.isArray(whiteboard.formulas) ? (whiteboard.formulas as string[]) : [];
    const diagrams = Array.isArray(whiteboard.diagrams) ? (whiteboard.diagrams as string[]) : [];
    
    // 提取并转换内容为字符串
    const intro = content.introduction ? String(content.introduction) : '';
    const def = content.definition ? String(content.definition) : '';
    const example = content.example ? String(content.example) : '';
    const question = content.question ? String(content.question) : '';
    const summary = content.summary ? String(content.summary) : '';

    return (
      <div className="improvement-card">
        <div className="card-header">
          <h3>📋 个性化学习方案</h3>
        </div>
        <div className="card-body">
          <div className="plan-overview">
            <span className="plan-time">⏱️ 预计总时长：{session?.plan?.total_estimated_minutes} 分钟</span>
          </div>
          
          <div className="steps-list">
            {session?.plan?.steps.map((step) => (
              <div key={step.step_order} className={`step-item ${step.is_completed ? 'completed' : ''}`}>
                <div className="step-header">
                  <span className="step-order">Step {step.step_order}</span>
                  <span className="step-name">{step.kp_name}</span>
                  {step.is_completed && <span className="step-check">✓</span>}
                </div>
                <p className="step-goal">{step.goal}</p>
                <span className="step-time">预计 {step.estimated_minutes} 分钟</span>
                <div className="step-actions">
                  <button 
                    className="btn btn-secondary" 
                    onClick={() => startStep(step)}
                    disabled={step.is_completed || isLoading}
                  >
                    开始本步
                  </button>
                  <button 
                    className="btn btn-primary" 
                    onClick={() => completeStep(step)}
                    disabled={step.is_completed || isLoading}
                  >
                    标记完成
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {stepContent && (
            <div className="step-content">
              <h4>{String(content.title || knowledgePoint.name || '学习内容')}</h4>
              {intro && <p>{intro}</p>}
              {def && (
                <div className="content-section">
                  <span className="section-label">定义/要点：</span>
                  <p>{def}</p>
                </div>
              )}
              {example && (
                <div className="content-section">
                  <span className="section-label">示例：</span>
                  <p>{example}</p>
                </div>
              )}
              {question && (
                <div className="content-section">
                  <span className="section-label">思考题：</span>
                  <p>{question}</p>
                </div>
              )}
              {summary && (
                <div className="content-section">
                  <span className="section-label">总结：</span>
                  <p>{summary}</p>
                </div>
              )}
              {formulas.length > 0 && (
                <div className="content-section">
                  <span className="section-label">板书公式：</span>
                  <div className="tag-list">
                    {formulas.map((item) => (
                      <span key={item} className="content-tag">{item}</span>
                    ))}
                  </div>
                </div>
              )}
              {diagrams.length > 0 && (
                <div className="content-section">
                  <span className="section-label">建议图示：</span>
                  <div className="tag-list">
                    {diagrams.map((item) => (
                      <span key={item} className="content-tag">{item}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {session?.status === 'quiz' && (
            <button className="btn btn-primary" onClick={loadQuiz} disabled={isLoading}>
              进入最终小测
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderQuiz = () => (
    <div className="improvement-card">
      <div className="card-header">
        <h3>✍️ 最终小测</h3>
      </div>
      <div className="card-body">
        {quiz?.questions.map((question: QuizQuestion, index: number) => (
          <div key={question.id} className="quiz-item">
            <div className="quiz-question">
              <span className="quiz-number">第 {index + 1} 题</span>
              <p>{question.content}</p>
            </div>
            {question.options && question.options.length > 0 ? (
              <div className="quiz-options">
                {question.options.map((option) => (
                  <label key={option} className={`quiz-option ${quizAnswers[question.id] === option ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name={question.id}
                      value={option}
                      checked={quizAnswers[question.id] === option}
                      onChange={(e) => setQuizAnswers((prev) => ({ ...prev, [question.id]: e.target.value }))}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            ) : (
              <input
                type="text"
                className="quiz-input"
                placeholder="请输入答案"
                value={quizAnswers[question.id] || ''}
                onChange={(e) => setQuizAnswers((prev) => ({ ...prev, [question.id]: e.target.value }))}
              />
            )}
          </div>
        ))}
        {quiz && (
          <button className="btn btn-primary" onClick={submitQuiz} disabled={isLoading}>
            提交小测
          </button>
        )}
      </div>
    </div>
  );

  const renderCompleted = () => (
    <div className="improvement-card completed-card">
      <div className="card-body">
        <div className="completed-icon">🎉</div>
        <h3>专项提升完成</h3>
        <p className="completed-kp">{session?.diagnosis?.target_kp_name}</p>
        <p>你已经完成诊断、方案学习和最终小测。</p>
        <button className="btn btn-secondary" onClick={() => window.location.href = '/center'}>
          返回学习模块
        </button>
      </div>
    </div>
  );

  return (
    <div className="improvement-page">
      <div className="improvement-container">
        {/* 头部 */}
        <div className="improvement-header">
          <h1>专项突破</h1>
          <p>根据成绩、错因和时间预算，定位最需要补强的知识点并生成个性化提升方案</p>
        </div>

        {/* 步骤指示器 */}
        <div className="steps-indicator">
          {stageLabels.map((stage, index) => (
            <div 
              key={index} 
              className={`step-indicator ${index === currentStage ? 'active' : ''} ${index < currentStage ? 'completed' : ''}`}
            >
              <div className="step-icon">{stage.icon}</div>
              <span className="step-title">{stage.title}</span>
            </div>
          ))}
        </div>

        {/* 内容区域 */}
        <div className="improvement-content">
          {error && <div className="error-banner">{error}</div>}
          
          {!session && renderUpload()}
          {session && (session.status === 'clarifying' || session.status === 'analyzing') && renderClarifying()}
          {session && (session.status === 'diagnosed' || session.status === 'planning') && renderDiagnosis()}
          {session && (session.status === 'learning' || session.status === 'quiz') && renderPlan()}
          {session && (session.status === 'quiz' || quiz) && renderQuiz()}
          {session && session.status === 'completed' && renderCompleted()}
        </div>
      </div>
    </div>
  );
};

export default Improvement;
