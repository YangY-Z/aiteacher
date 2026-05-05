import React, { useEffect, useState, useCallback, useRef } from 'react';
import Modal from 'antd/es/modal';
import Select from 'antd/es/select';
import message from 'antd/es/message';
import Button from 'antd/es/button';
import Drawer from 'antd/es/drawer';
import { useNavigate } from 'react-router-dom';
import SingleStreamLayout from '../components/layout/SingleStreamLayout';
import LearningMap from '../components/layout/LearningMap';
import Whiteboard from '../components/whiteboard/Whiteboard';
import ChatList from '../components/chat/ChatList';
import ChatInput from '../components/chat/ChatInput';
import DiagnosticTest from '../components/diagnostic/DiagnosticTest';
import { useAuthStore, useCourseStore, useLearningStore } from '../store';
import { courseApi, learningApi } from '../api';
import './Learning.css';

/**
 * 学习页面 - V2两列布局
 * 
 * 布局：白板(左侧) | AI对话(右侧，默认1/4，可拖拽调整)
 * 
 * 流程：
 * 1. 课前诊断 → 2. 核心学习 → 3. 即时检测 → 4. 课后保持
 */

type LearningPhase = 'diagnostic' | 'teaching' | 'assessment' | 'completed';

const LearningPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { setCurrentCourse, currentCourse } = useCourseStore();
  const {
    session,
    setSession,
    currentKp,
    setCurrentKp,
    progress,
    setProgress,
    addMessage,
    setMessages,
    isLoading,
    setLoading,
    isStreaming,
    setStreaming,
    isAssessmentMode,
    setAssessmentMode,
    assessmentQuestions,
    setAssessmentQuestions,
    clearWhiteboard,
    setWhiteboardTitle,
    addWhiteboardPoint,
    addWhiteboardFormula,
    addWhiteboardExample,
    addWhiteboardNote,
    commitWhiteboard,
    reset,
  } = useLearningStore();

  // 学习阶段
  const [phase, setPhase] = useState<LearningPhase>('diagnostic');
  
  // 诊断相关
  const [diagnosticSessionId, setDiagnosticSessionId] = useState<string | null>(null);
  const [diagnosticResult, setDiagnosticResult] = useState<any>(null);
  
  // 两列布局 - 右侧聊天区域宽度百分比（默认25%）
  const [rightPanelWidth, setRightPanelWidth] = useState(25);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // UI状态
  const [mapVisible, setMapVisible] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [skipModalVisible, setSkipModalVisible] = useState(false);

  // 防止重复调用
  const isStartingRef = useRef(false);
  const hasStartedRef = useRef(false);
  const phaseAdvanceHandledRef = useRef(false);  // 防止 phase_advance 和 complete 重复处理

  // 检查登录状态
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }
  }, [isAuthenticated, navigate]);

  // 加载课程
  useEffect(() => {
    const loadCourse = async () => {
      try {
        const res = await courseApi.getAll();
        if (res.data.success && res.data.data.length > 0) {
          setCurrentCourse(res.data.data[0]);
        }
      } catch (error) {
        console.error('Failed to load course:', error);
      }
    };
    loadCourse();
  }, [setCurrentCourse]);

  // 拖拽分隔条处理
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = ((containerRect.right - e.clientX) / containerRect.width) * 100;
      
      // 限制范围：15% - 50%
      const clampedWidth = Math.max(15, Math.min(50, newWidth));
      setRightPanelWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // 开始学习会话（含课前诊断）
  const startLearning = useCallback(async () => {
    if (!currentCourse) return;
    
    if (isStartingRef.current || hasStartedRef.current) return;
    
    const currentSession = useLearningStore.getState().session;
    if (currentSession) return;
    
    isStartingRef.current = true;
    
    try {
      setLoading(true);
      
      // 1. 先进行课前诊断
      setPhase('diagnostic');
      
      // 创建诊断会话
      const diagRes = await fetch('/api/v1/diagnostic/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: currentCourse.id,
          kp_id: null, // 使用当前知识点
        }),
      });
      
      if (diagRes.ok) {
        const diagData = await diagRes.json();
        if (diagData.success) {
          setDiagnosticSessionId(diagData.data.session_id);
          setLoading(false);
          return; // 等待诊断完成
        }
      }
      
      // 如果诊断创建失败，直接开始学习
      await startTeachingSession();
      
    } catch (error) {
      console.error('诊断启动失败，直接开始学习', error);
      await startTeachingSession();
    } finally {
      setLoading(false);
    }
  }, [currentCourse]);

  // 诊断完成回调
  const handleDiagnosticComplete = useCallback(async (result: any) => {
    setDiagnosticResult(result);
    
    // 根据诊断结果决定学习起点
    if (result.conclusion === 'full_mastery') {
      // 已掌握，跳过
      message.success('你已掌握这个知识点！');
      // TODO: 进入下一个知识点
    } else {
      // 开始学习
      await startTeachingSession();
    }
  }, []);

  // 跳过诊断
  const handleSkipDiagnostic = useCallback(async () => {
    await startTeachingSession();
  }, []);

  // 开始教学会话
  const startTeachingSession = useCallback(async () => {
    if (!currentCourse) return;
    
    try {
      setLoading(true);
      
      const res = await learningApi.startSession({ course_id: currentCourse.id });
      
      if (res.data.success) {
        const sessionData = res.data.data;
        setSession(sessionData);
        hasStartedRef.current = true;
        setPhase('teaching');
        
        // 获取知识点详情
        if (sessionData.kp_id) {
          const kpRes = await courseApi.getKnowledgePoint(
            currentCourse.id,
            sessionData.kp_id
          );
          if (kpRes.data.success) {
            setCurrentKp(kpRes.data.data);
          }
        }
        
        // 获取进度
        const progressRes = await learningApi.getProgress(currentCourse.id);
        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        }

        // 清空消息和白板
        setMessages([]);
        clearWhiteboard();
        
        // 流式获取教学内容
        await fetchTeachingContentStream(sessionData.session_id);
      }
    } catch (error) {
      message.error('启动学习失败，请重试');
      isStartingRef.current = false;
    } finally {
      setLoading(false);
    }
  }, [currentCourse, setSession, setCurrentKp, setProgress, setLoading, setMessages, clearWhiteboard]);

  // 自动开始学习
  useEffect(() => {
    if (currentCourse && !session) {
      startLearning();
    }
  }, [currentCourse, session]);

  // 流式获取教学内容
  const fetchTeachingContentStream = async (sessionId: string) => {
    setStreaming(true);
    
    await learningApi.streamTeachingContent(sessionId, {
      // 边讲边写模式：同时处理消息和白板
      onSegment: (data) => {
        // DEBUG: 检查收到的 segment 数据
        console.log('[DEBUG onSegment] data:', JSON.stringify(data));
        console.log('[DEBUG onSegment] data.image:', data.image);
        console.log('[DEBUG onSegment] data.video:', data.video);
        
        // 1. 提取媒体资源（根据 type 字段正确分配到 image 或 video）
        let imageResource = data.image || undefined;
        let videoResource = data.video || undefined;
        
        // 后端 ImageProcessStrategy 将所有资源挂在 image 字段，需按 type 分配
        if (data.image && data.image.type === 'video') {
          videoResource = data.image;
          imageResource = undefined;
        } else if (data.image && data.image.type === 'image') {
          imageResource = data.image;
          videoResource = undefined;
        }
        
        // 2. 添加消息
        if (data.message) {
          // 检测是否是提问消息
          const isQuestion = data.is_question === true || 
            data.message.includes('?') || 
            data.message.includes('？');
          
          addMessage({
            id: `msg-segment-${Date.now()}`,
            role: 'ai',
            content: data.message,
            timestamp: new Date(),
            type: isQuestion ? 'teacher_question' : undefined,
            image: imageResource,
            video: videoResource,
          });
        } else if (imageResource || videoResource) {
          // 只有媒体资源没有文本消息时，单独添加一条媒体消息
          addMessage({
            id: `msg-media-${Date.now()}`,
            role: 'ai',
            content: imageResource?.title || videoResource?.title || '',
            timestamp: new Date(),
            image: imageResource,
            video: videoResource,
          });
        }
        
        // 2. 更新白板（同步）
        const wb = data.whiteboard;
        if (wb) {
          if (wb.title) {
            setWhiteboardTitle(wb.title);
          }
          if (wb.points && wb.points.length > 0) {
            wb.points.forEach((point: string) => addWhiteboardPoint(point));
          }
          if (wb.formulas && wb.formulas.length > 0) {
            wb.formulas.forEach((formula: string) => addWhiteboardFormula(formula));
          }
          if (wb.examples && wb.examples.length > 0) {
            wb.examples.forEach((example: string) => addWhiteboardExample(example));
          }
          if (wb.notes && wb.notes.length > 0) {
            wb.notes.forEach((note: string) => addWhiteboardNote(note));
          }
        }
      },
      // 兼容旧格式
      onWbTitle: (content) => setWhiteboardTitle(content),
      onWbPoints: (content) => addWhiteboardPoint(content),
      onWbFormulas: (content) => addWhiteboardFormula(content),
      onWbExamples: (content) => addWhiteboardExample(content),
      onWbNotes: (content) => addWhiteboardNote(content),
      onMsgIntro: (content) => {
        addMessage({
          id: `msg-intro-${Date.now()}`,
          role: 'ai',
          content: `📚 ${content}`,
          timestamp: new Date(),
        });
      },
      onMsgDef: (content) => {
        addMessage({
          id: `msg-def-${Date.now()}`,
          role: 'ai',
          content: `💡 **定义**：${content}`,
          timestamp: new Date(),
        });
      },
      onMsgExample: (content) => {
        addMessage({
          id: `msg-example-${Date.now()}`,
          role: 'ai',
          content: `📝 **示例**：${content}`,
          timestamp: new Date(),
        });
      },
      onMsgSummary: (content) => {
        addMessage({
          id: `msg-summary-${Date.now()}`,
          role: 'ai',
          content: `✨ **总结**：${content}`,
          timestamp: new Date(),
        });
      },
      onMsgQuestion: (content) => {
        addMessage({
          id: `msg-question-${Date.now()}`,
          role: 'ai',
          content: `❓ **提问**：${content}`,
          timestamp: new Date(),
          type: 'teacher_question',
        });
      },
      onComplete: (nextAction) => {
        setStreaming(false);
        commitWhiteboard();
        
        if (nextAction === 'start_assessment') {
          setTimeout(() => startAssessment(), 1500);
        } else if (nextAction === 'next_knowledge_point') {
          setTimeout(() => moveToNextKnowledgePoint(), 1500);
        } else if (nextAction === 'next_phase') {
          // 进入下一教学阶段
          setTimeout(() => advanceToNextPhase(), 1500);
        }
      },
      onError: (error) => {
        message.error(error);
        setStreaming(false);
      },
    });
  };

  // 进入下一个知识点
  const moveToNextKnowledgePoint = async () => {
    const currentSession = useLearningStore.getState().session;
    const currentCourse = useCourseStore.getState().currentCourse;
    if (!currentSession || !currentCourse) return;
    
    try {
      setLoading(true);
      clearWhiteboard();
      
      const completeRes = await learningApi.completeKnowledgePoint(currentSession.session_id);
      
      if (completeRes.data.success && completeRes.data.data.next_kp_id) {
        const progressRes = await learningApi.getProgress(currentCourse.id);
        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        }
        
        const kpRes = await courseApi.getKnowledgePoint(currentCourse.id, completeRes.data.data.next_kp_id);
        if (kpRes.data.success) {
          setCurrentKp(kpRes.data.data);
          
          addMessage({
            id: `msg-${Date.now()}`,
            role: 'ai',
            content: `很好！让我们继续学习下一个知识点：${kpRes.data.data.name}`,
            timestamp: new Date(),
          });
          
          setTimeout(async () => {
            await fetchTeachingContentStream(currentSession.session_id);
          }, 1000);
        }
      } else if (completeRes.data.success && !completeRes.data.data.next_kp_id) {
        const progressRes = await learningApi.getProgress(currentCourse.id);
        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        }
        
        setPhase('completed');
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: '🎉 恭喜你！所有知识点都学完了！',
          timestamp: new Date(),
        });
      }
    } catch (error) {
      message.error('进入下一个知识点失败');
    } finally {
      setLoading(false);
    }
  };

  // 进入下一教学阶段
  const advanceToNextPhase = async () => {
    const currentSession = useLearningStore.getState().session;
    if (!currentSession) return;
    
    try {
      setLoading(true);
      
      // 调用后端推进阶段
      const phaseRes = await learningApi.advancePhase(currentSession.session_id);
      
      if (phaseRes.data.success) {
        const { current_phase, total_phases, is_last_phase } = phaseRes.data.data;
        
        // 清空白板，准备新阶段
        clearWhiteboard();
        
        // 添加过渡消息
        addMessage({
          id: `msg-phase-${Date.now()}`,
          role: 'ai',
          content: `📍 进入第${current_phase}/${total_phases}阶段`,
          timestamp: new Date(),
        });
        
        // 重新获取教学内容
        setTimeout(async () => {
          await fetchTeachingContentStream(currentSession.session_id);
        }, 500);
      }
    } catch (error) {
      message.error('进入下一阶段失败');
    } finally {
      setLoading(false);
    }
  };

  // 发送消息
  const handleSendMessage = async (msg: string) => {
    if (!session) return;

    addMessage({
      id: `msg-student-${Date.now()}`,
      role: 'student',
      content: msg,
      timestamp: new Date(),
    });

    if (msg.includes('开始') || msg.includes('测试') || msg.includes('评估')) {
      await startAssessment();
      return;
    }

    // 重置阶段推进标志
    phaseAdvanceHandledRef.current = false;
    
    setStreaming(true);
    
    await learningApi.streamSendMessage(session.session_id, msg, {
      onWbFormulas: (content) => addWhiteboardFormula(content),
      onMsgFeedback: (content) => {
        addMessage({
          id: `msg-feedback-${Date.now()}`,
          role: 'ai',
          content: `💬 ${content}`,
          timestamp: new Date(),
        });
      },
      onMsgEncourage: (content) => {
        addMessage({
          id: `msg-encourage-${Date.now()}`,
          role: 'ai',
          content: `💪 ${content}`,
          timestamp: new Date(),
        });
      },
      onMsgSupplement: (content) => {
        addMessage({
          id: `msg-supplement-${Date.now()}`,
          role: 'ai',
          content: `📝 ${content}`,
          timestamp: new Date(),
        });
      },
      onComplete: (nextAction) => {
        setStreaming(false);
        commitWhiteboard();
        
        // 如果已经通过 phase_advance 处理，跳过
        if (phaseAdvanceHandledRef.current) {
          return;
        }
        
        if (nextAction === 'start_assessment') {
          setTimeout(() => startAssessment(), 1500);
        } else if (nextAction === 'next_knowledge_point') {
          setTimeout(() => moveToNextKnowledgePoint(), 1500);
        } else if (nextAction === 'next_phase') {
          // 进入下一教学阶段
          setTimeout(() => advanceToNextPhase(), 1500);
        }
      },
      onError: (error) => {
        message.error(error);
        setStreaming(false);
      },
      onPhaseAdvance: (data) => {
        console.log('Phase advance event:', data);
        
        // 防御性检查
        if (!data || !data.next_action) {
          console.error('Invalid phase_advance data:', data);
          return;
        }
        
        // 标记已处理，防止 complete 事件重复处理
        phaseAdvanceHandledRef.current = true;
        
        if (data.next_action === 'next_phase') {
          // 后端已经推进了阶段，前端只需获取新阶段的教学内容
          const { current_phase, total_phases } = data;
          
          // 清空白板，准备新阶段
          clearWhiteboard();
          
          // 添加过渡消息
          addMessage({
            id: `msg-phase-${Date.now()}`,
            role: 'ai',
            content: `📍 进入第${current_phase}/${total_phases}阶段`,
            timestamp: new Date(),
          });
          
          // 重新获取教学内容
          setTimeout(async () => {
            const currentSession = useLearningStore.getState().session;
            if (currentSession) {
              await fetchTeachingContentStream(currentSession.session_id);
            }
          }, 500);
        } else if (data.next_action === 'start_assessment') {
          // 所有阶段完成，开始评估
          setTimeout(() => startAssessment(), 1500);
        }
      },
    });
  };

  // 开始评估
  const startAssessment = async () => {
    if (!session) {
      console.error('startAssessment: no session');
      return;
    }
    
    try {
      setLoading(true);
      console.log('Fetching assessment for session:', session.session_id, 'kp_id:', session.kp_id);
      const res = await learningApi.getAssessment(session.session_id);
      console.log('Assessment response:', res.data);
      
      if (res.data.success && res.data.data?.questions?.length > 0) {
        const questions = res.data.data.questions;
        console.log('Questions loaded:', questions.length, questions);
        
        setAssessmentQuestions(questions);
        setAssessmentMode(true);
        setPhase('assessment');
        setSelectedAnswers({});
        
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: `现在让我们来做 ${questions.length} 道题，检验一下学习效果：`,
          timestamp: new Date(),
        });
        
        setTimeout(() => {
          const firstQuestion = questions[0];
          if (firstQuestion) {
            addMessage({
              id: `msg-question-${firstQuestion.id}`,
              role: 'ai',
              content: `**第 1 题**`,
              timestamp: new Date(),
              type: 'question',
              question: {
                id: firstQuestion.id,
                content: firstQuestion.content,
                options: firstQuestion.options || [],
              },
            });
          }
        }, 500);
      } else {
        console.warn('No questions available:', res.data);
        message.warning('暂无题目，跳过评估');
        // 没有题目时，直接进入下一个知识点
        setTimeout(() => moveToNextKnowledgePoint(), 1500);
      }
    } catch (error) {
      console.error('获取题目失败:', error);
      message.error('获取题目失败');
    } finally {
      setLoading(false);
    }
  };

  // 选择答案
  const handleSelectAnswer = useCallback((questionId: string, answer: string) => {
    const questions = useLearningStore.getState().assessmentQuestions;
    
    setSelectedAnswers((prev) => {
      const newAnswers = { ...prev, [questionId]: answer };
      
      addMessage({
        id: `msg-${Date.now()}`,
        role: 'student',
        content: `选择：${answer}`,
        timestamp: new Date(),
      });
      
      if (questions.length > 0 && Object.keys(newAnswers).length === questions.length) {
        setTimeout(() => submitAssessmentWithAnswers(newAnswers), 500);
      } else {
        setTimeout(() => {
          const nextIndex = Object.keys(newAnswers).length;
          if (nextIndex < questions.length) {
            const nextQuestion = questions[nextIndex];
            addMessage({
              id: `msg-question-${nextQuestion.id}`,
              role: 'ai',
              content: `**第 ${nextIndex + 1} 题**`,
              timestamp: new Date(),
              type: 'question',
              question: {
                id: nextQuestion.id,
                content: nextQuestion.content,
                options: nextQuestion.options,
              },
            });
          }
        }, 800);
      }
      
      return newAnswers;
    });
  }, [addMessage]);

  // 提交评估
  const submitAssessmentWithAnswers = async (answers: Record<string, string>) => {
    const currentSession = useLearningStore.getState().session;
    if (!currentSession) return;
    
    try {
      setLoading(true);
      const answersList = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer,
      }));
      
      const res = await learningApi.submitAssessment(currentSession.session_id, { answers: answersList });
      
      if (res.data.success) {
        const result = res.data.data;
        
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: result.passed
            ? `🎉 太棒了！你答对了 ${result.correct_count}/${result.total_questions} 题，成功通过！`
            : `❌ 很遗憾，你只答对了 ${result.correct_count}/${result.total_questions} 题，需要重新学习。`,
          timestamp: new Date(),
          type: 'feedback',
        });
        
        const course = useCourseStore.getState().currentCourse;
        if (course) {
          const progressRes = await learningApi.getProgress(course.id);
          if (progressRes.data.success) {
            setProgress(progressRes.data.data);
          }
        }
        
        setAssessmentMode(false);
        setSelectedAnswers({});
        
        if (result.passed && result.next_kp_id) {
          setTimeout(() => {
            addMessage({
              id: `msg-${Date.now() + 1}`,
              role: 'ai',
              content: `下一个知识点：${result.next_kp_name}。准备好了吗？输入"开始"继续学习。`,
              timestamp: new Date(),
            });
            setPhase('teaching');
          }, 1500);
        } else if (!result.passed) {
          // 未通过，回到学习阶段
          setPhase('teaching');
        }
      }
    } catch (error) {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  };

  // 跳过知识点
  const handleSkip = async () => {
    if (!session) return;
    
    try {
      await learningApi.skipKnowledgePoint(session.session_id, '学生主动跳过');
      message.success('已跳过当前知识点');
      setSkipModalVisible(false);
      reset();
      hasStartedRef.current = false;
      isStartingRef.current = false;
      await startLearning();
    } catch (error) {
      message.error('跳过失败');
    }
  };

  // 暂停学习
  const handlePause = () => {
    Modal.confirm({
      title: '确认暂停学习？',
      content: '暂停后，你可以稍后继续学习。',
      onOk: () => {
        reset();
        navigate('/');
      },
    });
  };

  // 当前任务显示
  const currentTask = currentKp ? `掌握 ${currentKp.name}` : '加载中...';

  return (
    <div className="learning-page-v2">
      <SingleStreamLayout
        currentTask={currentTask}
        onOpenLearningMap={() => setMapVisible(true)}
        onPause={handlePause}
        onSkip={() => setSkipModalVisible(true)}
      >
        {/* 诊断阶段 */}
        {phase === 'diagnostic' && diagnosticSessionId && (
          <DiagnosticTest
            sessionId={diagnosticSessionId}
            onComplete={handleDiagnosticComplete}
            onSkip={handleSkipDiagnostic}
          />
        )}

        {/* 教学/评估阶段 */}
        {(phase === 'teaching' || phase === 'assessment') && (
          <div className="main-content-area" ref={containerRef}>
            {/* 白板区域 - 左侧 */}
            <div 
              className="whiteboard-area" 
              style={{ width: `${100 - rightPanelWidth}%` }}
            >
              <Whiteboard loading={isLoading} />
            </div>
            
            {/* 可拖拽分隔条 */}
            <div 
              className={`resize-divider ${isDragging ? 'dragging' : ''}`}
              onMouseDown={handleMouseDown}
            />
            
            {/* 聊天区域 - 右侧 */}
            <div 
              className="chat-area"
              style={{ width: `${rightPanelWidth}%` }}
            >
              <ChatList 
                onSelectAnswer={handleSelectAnswer}
                selectedAnswers={selectedAnswers}
              />
              <ChatInput
                onSend={handleSendMessage}
                disabled={isLoading || isStreaming}
                placeholder={
                  isAssessmentMode
                    ? '请点击上方选项选择答案'
                    : '请输入你的回答或问题...'
                }
              />
            </div>
          </div>
        )}

        {/* 完成阶段 */}
        {phase === 'completed' && (
          <div className="completed-area">
            <h2>🎉 恭喜完成所有学习！</h2>
            <p>你已经掌握了本课程的所有知识点。</p>
            <Button type="primary" onClick={() => setMapVisible(true)}>
              查看学习地图
            </Button>
          </div>
        )}
      </SingleStreamLayout>

      {/* 学习地图抽屉 */}
      <Drawer
        title="学习地图"
        placement="right"
        width={360}
        open={mapVisible}
        onClose={() => setMapVisible(false)}
      >
        <LearningMap
          progress={progress}
          currentKpId={currentKp?.id}
          onSelectKp={(kpId) => {
            // TODO: 切换到指定知识点
            setMapVisible(false);
          }}
        />
      </Drawer>

      {/* 跳过确认弹窗 */}
      <Modal
        title="确认跳过"
        open={skipModalVisible}
        onCancel={() => setSkipModalVisible(false)}
        onOk={handleSkip}
        okText="确认跳过"
        cancelText="取消"
      >
        <p>确定要跳过这个知识点吗？</p>
        <p style={{ color: '#999' }}>跳过后，你可能需要在后续学习中补充这个知识点。</p>
      </Modal>
    </div>
  );
};

export default LearningPage;