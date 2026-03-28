import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Col, Form, Input, InputNumber, Layout, Row, Select, Space, Steps, Tag, Typography, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import AppHeader from '../components/layout/Header';
import { useAuthStore, useCourseStore, useImprovementStore } from '../store';
import { courseApi, improvementApi } from '../api';
import type { ImprovementPlanStep, QuizQuestion } from '../types';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

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

const ImprovementPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { currentCourse, setCurrentCourse } = useCourseStore();
  const { session, setSession, quiz, setQuiz, stepContent, setStepContent, isLoading, setLoading, reset } = useImprovementStore();

  const [form] = Form.useForm();
  const [clarifyAnswer, setClarifyAnswer] = useState('');
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const loadCourse = async () => {
      if (currentCourse) return;
      const res = await courseApi.getAll();
      if (res.data.success && res.data.data.length > 0) {
        setCurrentCourse(res.data.data[0]);
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

  const startImprovement = async (values: Record<string, unknown>) => {
    if (!currentCourse) return;
    try {
      setLoading(true);
      const res = await improvementApi.startSession({
        course_id: currentCourse.id,
        score_input: {
          exam_name: String(values.exam_name),
          score: Number(values.score),
          total_score: Number(values.total_score),
          error_description: values.error_description ? String(values.error_description) : undefined,
          available_time: Number(values.available_time),
          difficulty: values.difficulty as 'basic' | 'normal' | 'challenge',
          foundation: values.foundation as 'weak' | 'average' | 'good',
          max_clarification_rounds: Number(values.max_clarification_rounds),
        },
      });
      setSession(res.data.data);
      message.success('已创建专项提升会话');
    } catch {
      message.error('创建专项提升会话失败');
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
      message.error('提交澄清回答失败');
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
      message.success('学习方案已生成');
    } catch {
      message.error('生成学习方案失败');
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
      message.success(`已加载第 ${step.step_order} 步学习内容`);
    } catch {
      message.error('加载学习步骤失败');
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
      message.error('完成学习步骤失败');
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
      message.error('获取小测失败');
    } finally {
      setLoading(false);
    }
  };

  const submitQuiz = async () => {
    if (!session || !quiz) return;
    try {
      setLoading(true);
      const answers = Object.entries(quizAnswers).map(([question_id, answer]) => ({ question_id, answer }));
      const res = await improvementApi.submitQuiz(session.session_id, answers);
      message.success(res.data.data.feedback);
      const refreshed = await improvementApi.getSession(session.session_id);
      setSession(refreshed.data.data);
    } catch {
      message.error('提交小测失败');
    } finally {
      setLoading(false);
    }
  };

  const renderUpload = () => (
    <Card title="录入成绩并开始专项提升" loading={isLoading}>
      <Form form={form} layout="vertical" onFinish={startImprovement} initialValues={{ available_time: 30, difficulty: 'normal', foundation: 'average', max_clarification_rounds: 5 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="exam_name" label="试卷/作业名称" rules={[{ required: true }]}>
              <Input placeholder="如：一次函数单元测验" />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="score" label="得分" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="total_score" label="满分" rules={[{ required: true }]}>
              <InputNumber min={1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="error_description" label="错题描述 / 老师评语">
          <Input.TextArea rows={4} placeholder="可填写主要丢分点、老师评语、自己觉得不会的题型" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item name="available_time" label="可投入时间（分钟）" rules={[{ required: true }]}>
              <InputNumber min={10} max={180} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="max_clarification_rounds" label="最多追问次数" rules={[{ required: true }]}>
              <InputNumber min={1} max={5} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="difficulty" label="期望难度" rules={[{ required: true }]}>
              <Select options={[{ label: '基础巩固', value: 'basic' }, { label: '常规提升', value: 'normal' }, { label: '挑战提高', value: 'challenge' }]} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="foundation" label="自评基础" rules={[{ required: true }]}>
              <Select options={[{ label: '薄弱', value: 'weak' }, { label: '一般', value: 'average' }, { label: '较好', value: 'good' }]} />
            </Form.Item>
          </Col>
        </Row>
        <Button type="primary" htmlType="submit">开始诊断</Button>
      </Form>
    </Card>
  );

  const renderClarifying = () => {
    const latest = session?.clarification_rounds?.[session.clarification_rounds.length - 1];
    return (
      <Card
        title="进一步澄清薄弱点"
        loading={isLoading}
        extra={session ? <Text type="secondary">{session.clarification_rounds.length}/{session.max_clarification_rounds}</Text> : null}
      >
        {session?.clarification_rounds.map((item) => (
          <Card key={item.round_number} size="small" style={{ marginBottom: 12 }}>
            <Paragraph><Text strong>系统追问：</Text>{item.system_question}</Paragraph>
            {item.student_answer && <Paragraph><Text strong>你的回答：</Text>{item.student_answer}</Paragraph>}
          </Card>
        ))}
        {latest && !latest.student_answer && (
          <Space.Compact style={{ width: '100%' }}>
            <Input value={clarifyAnswer} onChange={(e) => setClarifyAnswer(e.target.value)} placeholder="请回答系统问题" />
            <Button type="primary" onClick={submitClarification}>提交</Button>
          </Space.Compact>
        )}
      </Card>
    );
  };

  const renderDiagnosis = () => (
    <Card title="诊断结果" loading={isLoading} extra={<Button type="primary" onClick={generatePlan}>生成学习方案</Button>}>
      <Title level={4}>{session?.diagnosis?.target_kp_name}</Title>
      <Paragraph>{session?.diagnosis?.reason}</Paragraph>
      <Paragraph>置信度：{Math.round((session?.diagnosis?.confidence || 0) * 100)}%</Paragraph>
      <Space wrap>
        {session?.diagnosis?.prerequisite_gaps.map((item) => <Tag key={item}>{item}</Tag>)}
      </Space>
    </Card>
  );

  const renderPlan = () => {
    const content = (stepContent?.content as Record<string, unknown> | undefined) ?? {};
    const whiteboard = (stepContent?.whiteboard as Record<string, unknown> | undefined) ?? {};
    const knowledgePoint = (stepContent?.knowledge_point as Record<string, unknown> | undefined) ?? {};
    const formulas = Array.isArray(whiteboard.formulas) ? (whiteboard.formulas as string[]) : [];
    const diagrams = Array.isArray(whiteboard.diagrams) ? (whiteboard.diagrams as string[]) : [];

    return (
    <Card title="个性化学习方案" loading={isLoading}>
      <Paragraph>预计总时长：{session?.plan?.total_estimated_minutes} 分钟</Paragraph>
      <Space direction="vertical" style={{ width: '100%' }}>
        {session?.plan?.steps.map((step) => (
          <Card key={step.step_order} size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Step {step.step_order} · {step.kp_name}</Text>
              <Text>{step.goal}</Text>
              <Text type="secondary">预计 {step.estimated_minutes} 分钟</Text>
              <Space>
                <Button onClick={() => startStep(step)} disabled={step.is_completed}>开始本步</Button>
                <Button type="primary" onClick={() => completeStep(step)} disabled={step.is_completed}>标记完成</Button>
              </Space>
            </Space>
          </Card>
        ))}
      </Space>
      {stepContent && (
        <Card type="inner" title={String(content.title || knowledgePoint.name || '学习内容')} style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            {content.introduction ? <Paragraph>{String(content.introduction)}</Paragraph> : null}
            {content.definition ? <Paragraph><Text strong>定义/要点：</Text>{String(content.definition)}</Paragraph> : null}
            {content.example ? <Paragraph><Text strong>示例：</Text>{String(content.example)}</Paragraph> : null}
            {content.question ? <Paragraph><Text strong>思考题：</Text>{String(content.question)}</Paragraph> : null}
            {content.summary ? <Paragraph><Text strong>总结：</Text>{String(content.summary)}</Paragraph> : null}
            {formulas.length > 0 && (
              <div>
                <Text strong>板书公式：</Text>
                <Space wrap style={{ marginLeft: 8 }}>
                  {formulas.map((item) => <Tag key={item}>{item}</Tag>)}
                </Space>
              </div>
            )}
            {diagrams.length > 0 && (
              <div>
                <Text strong>建议图示：</Text>
                <Space wrap style={{ marginLeft: 8 }}>
                  {diagrams.map((item) => <Tag key={item}>{item}</Tag>)}
                </Space>
              </div>
            )}
          </Space>
        </Card>
      )}
      {session?.status === 'quiz' && <Button type="primary" style={{ marginTop: 16 }} onClick={loadQuiz}>进入最终小测</Button>}
    </Card>
    );
  };

  const renderQuiz = () => (
    <Card title="最终小测" loading={isLoading} extra={!quiz && <Button onClick={loadQuiz}>加载题目</Button>}>
      {quiz?.questions.map((question: QuizQuestion, index: number) => (
        <Card key={question.id} size="small" style={{ marginBottom: 12 }}>
          <Paragraph><Text strong>第 {index + 1} 题：</Text>{question.content}</Paragraph>
          {question.options && question.options.length > 0 ? (
            <Select
              style={{ width: '100%' }}
              placeholder="请选择答案"
              value={quizAnswers[question.id]}
              onChange={(value) => setQuizAnswers((prev) => ({ ...prev, [question.id]: value }))}
              options={question.options.map((item) => ({ label: item, value: item }))}
            />
          ) : (
            <Input
              value={quizAnswers[question.id]}
              onChange={(e) => setQuizAnswers((prev) => ({ ...prev, [question.id]: e.target.value }))}
              placeholder="请输入答案"
            />
          )}
        </Card>
      ))}
      {quiz && <Button type="primary" onClick={submitQuiz}>提交小测</Button>}
    </Card>
  );

  const renderCompleted = () => (
    <Card title="专项提升完成">
      <Title level={4}>本次专项提升已完成</Title>
      <Paragraph>{session?.diagnosis?.target_kp_name}</Paragraph>
      <Paragraph>你已经完成诊断、方案学习和最终小测。</Paragraph>
      <Button onClick={() => navigate('/learn')}>返回学习模块</Button>
    </Card>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Card>
            <Title level={3} style={{ marginBottom: 8 }}>专项提升</Title>
            <Paragraph style={{ marginBottom: 0 }}>根据成绩、错因和时间预算，定位最需要补强的知识点并生成个性化提升方案。</Paragraph>
          </Card>

          <Card>
            <Steps
              current={currentStage}
              items={[
                { title: '录入成绩' },
                { title: '诊断/澄清' },
                { title: '生成方案' },
                { title: '分步学习' },
                { title: '最终小测' },
                { title: '完成' },
              ]}
            />
          </Card>

          {!session && renderUpload()}
          {session && (session.status === 'clarifying' || session.status === 'analyzing') && renderClarifying()}
          {session && (session.status === 'diagnosed' || session.status === 'planning') && renderDiagnosis()}
          {session && (session.status === 'learning' || session.status === 'quiz') && renderPlan()}
          {session && (session.status === 'quiz' || quiz) && renderQuiz()}
          {session && session.status === 'completed' && renderCompleted()}
        </Space>
      </Content>
    </Layout>
  );
};

export default ImprovementPage;
