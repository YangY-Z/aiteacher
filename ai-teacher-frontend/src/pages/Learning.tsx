import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Layout, Modal, Select, message, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../components/layout/Header';
import Whiteboard from '../components/whiteboard/Whiteboard';
import ChatList from '../components/chat/ChatList';
import ChatInput from '../components/chat/ChatInput';
import ProgressPanel from '../components/progress/ProgressPanel';
import { useAuthStore, useCourseStore, useLearningStore } from '../store';
import { courseApi, learningApi } from '../api';
import './Learning.css';

const { Content, Sider } = Layout;

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
    isAssessmentMode,
    setAssessmentMode,
    assessmentQuestions,
    setAssessmentQuestions,
    addWhiteboardBlock,
    clearWhiteboard,
    reset,
  } = useLearningStore();

  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [skipModalVisible, setSkipModalVisible] = useState(false);
  
  // 防止 StrictMode 重复调用
  const isStartingRef = useRef(false);
  const hasStartedRef = useRef(false);

  // 带参数的提交评估
  const submitAssessmentWithAnswers = useCallback(async (answers: Record<string, string>) => {
    const currentSession = useLearningStore.getState().session;
    if (!currentSession || Object.keys(answers).length === 0) return;
    
    try {
      setLoading(true);
      const answersList = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer,
      }));
      
      const res = await learningApi.submitAssessment(currentSession.session_id, { answers: answersList });
      
      if (res.data.success) {
        const result = res.data.data;
        
        // 添加结果消息
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: result.passed
            ? `🎉 太棒了！你答对了 ${result.correct_count}/${result.total_questions} 题，成功通过！`
            : `❌ 很遗憾，你只答对了 ${result.correct_count}/${result.total_questions} 题，需要重新学习。`,
          timestamp: new Date(),
          type: 'feedback',
        });
        
        // 更新进度
        const course = useCourseStore.getState().currentCourse;
        if (course) {
          const progressRes = await learningApi.getProgress(course.id);
          if (progressRes.data.success) {
            setProgress(progressRes.data.data);
          }
        }
        
        setAssessmentMode(false);
        setSelectedAnswers({});
        setCurrentQuestionIndex(0);
        
        // 如果通过，准备下一个知识点
        if (result.passed && result.next_kp_id) {
          setTimeout(() => {
            addMessage({
              id: `msg-${Date.now() + 1}`,
              role: 'ai',
              content: `下一个知识点：${result.next_kp_name}。准备好了吗？输入"开始"继续学习。`,
              timestamp: new Date(),
            });
          }, 1500);
        }
      }
    } catch (error) {
      message.error('提交失败');
    } finally {
      setLoading(false);
    }
  }, [addMessage, setProgress, setAssessmentMode, setLoading]);

  // 选择答案后进入下一题
  const handleSelectAnswer = useCallback((questionId: string, answer: string) => {
    const questions = useLearningStore.getState().assessmentQuestions;
    
    setSelectedAnswers((prev) => {
      const newAnswers = { ...prev, [questionId]: answer };
      
      // 添加用户选择的消息
      addMessage({
        id: `msg-${Date.now()}`,
        role: 'student',
        content: `选择：${answer}`,
        timestamp: new Date(),
      });
      
      // 检查是否所有题目都已回答
      if (questions.length > 0 && Object.keys(newAnswers).length === questions.length) {
        // 所有题目答完，提交评估
        setTimeout(() => {
          submitAssessmentWithAnswers(newAnswers);
        }, 500);
      } else {
        // 显示下一题
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
  }, [addMessage, submitAssessmentWithAnswers]);

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

  // 开始学习会话
  const startLearning = useCallback(async () => {
    if (!currentCourse) return;
    
    // 防止重复调用（使用 ref）
    if (isStartingRef.current || hasStartedRef.current) {
      console.log('startLearning: already starting or started, skipping');
      return;
    }
    
    // 防止重复调用（检查 store）
    const currentSession = useLearningStore.getState().session;
    if (currentSession) return;
    
    isStartingRef.current = true;
    console.log('startLearning: starting...');
    
    try {
      setLoading(true);
      const res = await learningApi.startSession({ course_id: currentCourse.id });
      
      if (res.data.success) {
        const sessionData = res.data.data;
        setSession(sessionData);
        hasStartedRef.current = true;
        
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
        
        // 获取教学内容
        try {
          const teachRes = await learningApi.getTeachingContent(sessionData.session_id);
          if (teachRes.data.success) {
            const content = teachRes.data.data;
            
            // 调试日志
            console.log('Teach API response:', content);
            
            // 更新白板
            addWhiteboardBlock(content.whiteboard);
            
            // 添加AI消息
            const textContent = content.content as Record<string, any>;
            
            // 逐条展示教学内容
            let delay = 0;
            
            if (textContent.introduction) {
              setTimeout(() => {
                addMessage({
                  id: `msg-intro-${Date.now()}`,
                  role: 'ai',
                  content: textContent.introduction,
                  timestamp: new Date(),
                });
              }, delay);
              delay += 800;
            }
            
            if (textContent.definition) {
              setTimeout(() => {
                addMessage({
                  id: `msg-def-${Date.now()}`,
                  role: 'ai',
                  content: textContent.definition,
                  timestamp: new Date(),
                });
              }, delay);
              delay += 800;
            }
            
            if (textContent.example) {
              setTimeout(() => {
                addMessage({
                  id: `msg-example-${Date.now()}`,
                  role: 'ai',
                  content: textContent.example,
                  timestamp: new Date(),
                });
              }, delay);
              delay += 800;
            }
            
            if (textContent.summary) {
              setTimeout(() => {
                addMessage({
                  id: `msg-summary-${Date.now()}`,
                  role: 'ai',
                  content: textContent.summary,
                  timestamp: new Date(),
                });
              }, delay);
              delay += 800;
            }
            
            // 处理提问
            if (textContent.question) {
              setTimeout(() => {
                addMessage({
                  id: `msg-question-${Date.now()}`,
                  role: 'ai',
                  content: textContent.question,
                  timestamp: new Date(),
                  type: 'teacher_question',
                });
              }, delay);
            } else {
              // 没有提问时，引导开始测试
              setTimeout(() => {
                addMessage({
                  id: `msg-guide-${Date.now()}`,
                  role: 'ai',
                  content: '这部分内容讲解完毕，输入"开始测试"检验学习效果吧！',
                  timestamp: new Date(),
                });
              }, delay);
            }
          }
        } catch (teachError) {
          console.error('Failed to get teaching content:', teachError);
          // 添加欢迎消息作为后备
          addMessage({
            id: `msg-welcome-${Date.now()}`,
            role: 'ai',
            content: '你好！让我们开始学习吧！输入"开始测试"可以进行知识点评估。',
            timestamp: new Date(),
          });
        }
      }
    } catch (error) {
      message.error('启动学习失败，请重试');
      isStartingRef.current = false;
    } finally {
      setLoading(false);
    }
  }, [currentCourse, setSession, setCurrentKp, setProgress, setLoading, setMessages, addMessage, addWhiteboardBlock]);

  // 自动开始学习（移除 startLearning 依赖，避免重复调用）
  useEffect(() => {
    if (currentCourse && !session) {
      startLearning();
    }
  }, [currentCourse, session]);

  // 获取教学内容
  const fetchTeachingContent = async (sessionId: string) => {
    try {
      setLoading(true);
      const res = await learningApi.getTeachingContent(sessionId);
      
      if (res.data.success) {
        const content = res.data.data;
        
        // 调试日志
        console.log('Teach API response:', content);
        console.log('Content field:', content.content);
        console.log('Question field:', content.content?.question);
        
        // 更新白板
        addWhiteboardBlock(content.whiteboard);
        
        // 添加AI消息
        const textContent = content.content as Record<string, any>;
        
        // 逐条展示教学内容
        let delay = 0;
        
        if (textContent.introduction) {
          setTimeout(() => {
            addMessage({
              id: `msg-intro-${Date.now()}`,
              role: 'ai',
              content: textContent.introduction,
              timestamp: new Date(),
            });
          }, delay);
          delay += 800;
        }
        
        if (textContent.definition) {
          setTimeout(() => {
            addMessage({
              id: `msg-def-${Date.now()}`,
              role: 'ai',
              content: textContent.definition,
              timestamp: new Date(),
            });
          }, delay);
          delay += 800;
        }
        
        if (textContent.example) {
          setTimeout(() => {
            addMessage({
              id: `msg-example-${Date.now()}`,
              role: 'ai',
              content: textContent.example,
              timestamp: new Date(),
            });
          }, delay);
          delay += 800;
        }
        
        if (textContent.summary) {
          setTimeout(() => {
            addMessage({
              id: `msg-summary-${Date.now()}`,
              role: 'ai',
              content: textContent.summary,
              timestamp: new Date(),
            });
          }, delay);
          delay += 800;
        }
        
        // 根据 next_action 决定后续动作
        const nextAction = content.next_action;
        console.log('nextAction:', nextAction, 'hasQuestion:', !!textContent.question);
        
        if (textContent.question) {
          // 有提问，显示问题等待学生回复
          setTimeout(() => {
            addMessage({
              id: `msg-question-${Date.now()}`,
              role: 'ai',
              content: textContent.question,
              timestamp: new Date(),
              type: 'teacher_question',
            });
          }, delay);
        } else {
          // 没有提问，引导开始测试
          setTimeout(() => {
            addMessage({
              id: `msg-guide-${Date.now()}`,
              role: 'ai',
              content: '这部分内容讲解完毕，输入"开始测试"检验学习效果吧！',
              timestamp: new Date(),
            });
          }, delay);
        }
      }
    } catch (error) {
      console.error('Failed to get teaching content:', error);
    } finally {
      setLoading(false);
    }
  };

  // 进入下一个知识点（概念类知识点完成后调用）
  const moveToNextKnowledgePoint = async () => {
    const currentSession = useLearningStore.getState().session;
    const currentCourse = useCourseStore.getState().currentCourse;
    if (!currentSession || !currentCourse) return;
    
    try {
      setLoading(true);
      
      // 清空白板，开始新的知识点
      clearWhiteboard();
      
      // 标记当前知识点为已完成（计入进度）
      const completeRes = await learningApi.completeKnowledgePoint(currentSession.session_id);
      
      if (completeRes.data.success && completeRes.data.data.next_kp_id) {
        // 更新进度
        const progressRes = await learningApi.getProgress(currentCourse.id);
        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        }
        
        // 获取下一个知识点详情
        const kpRes = await courseApi.getKnowledgePoint(currentCourse.id, completeRes.data.data.next_kp_id);
        if (kpRes.data.success) {
          setCurrentKp(kpRes.data.data);
          
          // 提示进入下一个知识点
          addMessage({
            id: `msg-${Date.now()}`,
            role: 'ai',
            content: `很好！让我们继续学习下一个知识点：${kpRes.data.data.name}`,
            timestamp: new Date(),
          });
          
          // 后端已更新session的kp_id，直接获取教学内容
          setTimeout(async () => {
            await fetchTeachingContent(currentSession.session_id);
          }, 1000);
        }
      } else if (completeRes.data.success && !completeRes.data.data.next_kp_id) {
        // 更新进度
        const progressRes = await learningApi.getProgress(currentCourse.id);
        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        }
        
        // 所有知识点都学完了
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

  // 发送消息
  const handleSendMessage = async (msg: string) => {
    if (!session) return;

    // 添加学生消息
    addMessage({
      id: `msg-student-${Date.now()}`,
      role: 'student',
      content: msg,
      timestamp: new Date(),
    });

    // 检查是否要开始评估
    if (msg.includes('开始') || msg.includes('测试') || msg.includes('评估')) {
      await startAssessment();
      return;
    }

    // 发送给后端处理
    try {
      setLoading(true);
      const res = await learningApi.sendMessage(session.session_id, { message: msg });
      
      if (res.data.success) {
        const data = res.data.data;
        addWhiteboardBlock(data.whiteboard);
        
        const textContent = data.content as Record<string, any>;
        
        // 显示后端返回的反馈
        if (textContent.feedback) {
          addMessage({
            id: `msg-feedback-${Date.now()}`,
            role: 'ai',
            content: textContent.feedback,
            timestamp: new Date(),
          });
        }
        
        // 显示鼓励语
        if (textContent.encouragement) {
          setTimeout(() => {
            addMessage({
              id: `msg-encourage-${Date.now()}`,
              role: 'ai',
              content: `💪 ${textContent.encouragement}`,
              timestamp: new Date(),
            });
          }, 600);
        }
        
        // 显示补充说明
        if (textContent.supplement) {
          setTimeout(() => {
            addMessage({
              id: `msg-supplement-${Date.now()}`,
              role: 'ai',
              content: `📝 ${textContent.supplement}`,
              timestamp: new Date(),
            });
          }, 1200);
        }
        
        // 根据 next_action 决定下一步
        if (data.next_action === 'start_assessment') {
          // 开始评估
          setTimeout(async () => {
            await startAssessment();
          }, 1500);
        } else if (data.next_action === 'next_knowledge_point') {
          // 直接进入下一个知识点
          setTimeout(async () => {
            await moveToNextKnowledgePoint();
          }, 1500);
        }
        // wait_for_student 时不需要额外操作，学生可以继续输入
      }
    } catch (error) {
      message.error('发送失败');
    } finally {
      setLoading(false);
    }
  };

  // 开始评估
  const startAssessment = async () => {
    if (!session) return;
    
    try {
      setLoading(true);
      const res = await learningApi.getAssessment(session.session_id);
      
      if (res.data.success && res.data.data.questions.length > 0) {
        const questions = res.data.data.questions;
        setAssessmentQuestions(questions);
        setAssessmentMode(true);
        setSelectedAnswers({});
        setCurrentQuestionIndex(0);
        
        // 添加评估引导消息
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: `现在让我们来做 ${questions.length} 道题，检验一下学习效果：`,
          timestamp: new Date(),
        });
        
        // 只显示第一道题
        setTimeout(() => {
          const firstQuestion = questions[0];
          addMessage({
            id: `msg-question-${firstQuestion.id}`,
            role: 'ai',
            content: `**第 1 题**`,
            timestamp: new Date(),
            type: 'question',
            question: {
              id: firstQuestion.id,
              content: firstQuestion.content,
              options: firstQuestion.options,
            },
          });
        }, 500);
      }
    } catch (error) {
      message.error('获取题目失败');
    } finally {
      setLoading(false);
    }
  };

  // 提交评估
  const submitAssessment = async () => {
    if (!session || Object.keys(selectedAnswers).length === 0) return;
    
    try {
      setLoading(true);
      const answers = Object.entries(selectedAnswers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer,
      }));
      
      const res = await learningApi.submitAssessment(session.session_id, { answers });
      
      if (res.data.success) {
        const result = res.data.data;
        
        // 添加结果消息
        addMessage({
          id: `msg-${Date.now()}`,
          role: 'ai',
          content: result.passed
            ? `🎉 太棒了！你答对了 ${result.correct_count}/${result.total_questions} 题，成功通过！`
            : `❌ 很遗憾，你只答对了 ${result.correct_count}/${result.total_questions} 题，需要重新学习。`,
          timestamp: new Date(),
          type: 'feedback',
        });
        
        // 更新进度
        if (currentCourse) {
          const progressRes = await learningApi.getProgress(currentCourse.id);
          if (progressRes.data.success) {
            setProgress(progressRes.data.data);
          }
        }
        
        setAssessmentMode(false);
        setSelectedAnswers({});
        
        // 如果通过，准备下一个知识点
        if (result.passed && result.next_kp_id) {
          setTimeout(() => {
            addMessage({
              id: `msg-${Date.now() + 1}`,
              role: 'ai',
              content: `下一个知识点：${result.next_kp_name}。准备好了吗？输入"开始"继续学习。`,
              timestamp: new Date(),
            });
          }, 1500);
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
      
      // 开始新的学习
      await startLearning();
    } catch (error) {
      message.error('跳过失败');
    }
  };

  // 复习
  const handleReview = () => {
    setReviewModalVisible(true);
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

  return (
    <Layout className="learning-layout">
      <AppHeader />
      
      <Layout className="main-layout">
        <Content className="main-content">
          <div className="whiteboard-section">
            <Whiteboard loading={isLoading} />
          </div>
          
          <div className="chat-section">
            <ChatList 
              onSelectAnswer={handleSelectAnswer}
              selectedAnswers={selectedAnswers}
            />
            <ChatInput
              onSend={handleSendMessage}
              disabled={isLoading}
              placeholder={
                isAssessmentMode
                  ? '请点击上方选项选择答案'
                  : '请输入你的回答或问题...'
              }
            />
          </div>
        </Content>
        
        <Sider width={280} className="progress-sider">
          <ProgressPanel
            onSkip={() => setSkipModalVisible(true)}
            onReview={handleReview}
            onPause={handlePause}
          />
        </Sider>
      </Layout>

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

      {/* 复习选择弹窗 */}
      <Modal
        title="选择要复习的知识点"
        open={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        footer={null}
      >
        <Select
          style={{ width: '100%', marginBottom: 16 }}
          placeholder="选择知识点"
          options={
            progress?.completed_count
              ? [{ label: '选择已学习的知识点', value: '' }]
              : [{ label: '暂无可复习的知识点', value: '', disabled: true }]
          }
        />
        <Button type="primary" block>
          开始复习
        </Button>
      </Modal>
    </Layout>
  );
};

export default LearningPage;
