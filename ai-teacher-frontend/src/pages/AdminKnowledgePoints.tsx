import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from 'antd/es/layout';
import Button from 'antd/es/button';
import Card from 'antd/es/card';
import Table from 'antd/es/table';
import Space from 'antd/es/space';
import Modal from 'antd/es/modal';
import Form from 'antd/es/form';
import Input from 'antd/es/input';
import Select from 'antd/es/select';
import InputNumber from 'antd/es/input-number';
import message from 'antd/es/message';
import Popconfirm from 'antd/es/popconfirm';
import Tree from 'antd/es/tree';
import { ArrowLeftOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { knowledgePointApi, chapterApi } from '../api/admin';
import './AdminKnowledgePoints.css';

const { Header, Content, Sider } = Layout;

interface KnowledgePoint {
  id: string;
  name: string;
  type: string;
  level: number;
  description: string;
  key_points: string[];
  mastery_criteria?: {
    type: string;
    method: string;
    question_count: number;
    pass_threshold: number;
  };
  teaching_config?: {
    use_examples: boolean;
    ask_questions: boolean;
    question_positions: string[];
  };
  created_at: string;
}

const AdminKnowledgePoints: React.FC = () => {
  const { chapterId } = useParams<{ chapterId: string }>();
  const navigate = useNavigate();
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([]);
  const [chapterInfo, setChapterInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingKP, setEditingKP] = useState<KnowledgePoint | null>(null);
  const [form] = Form.useForm();
  const [selectedLevel, setSelectedLevel] = useState<number | undefined>();

  const token = localStorage.getItem('admin_token') || '';

  useEffect(() => {
    loadChapterInfo();
    loadKnowledgePoints();
  }, [chapterId, selectedLevel]);

  const loadChapterInfo = async () => {
    if (!chapterId) return;
    try {
      const response = await chapterApi.get(token, chapterId);
      if (response.success) {
        setChapterInfo(response.data);
      }
    } catch (error) {
      message.error('加载章节信息失败');
    }
  };

  const loadKnowledgePoints = async () => {
    if (!chapterId) return;
    setLoading(true);
    try {
      const params: any = {};
      if (selectedLevel !== undefined) {
        params.level = selectedLevel;
      }
      const response = await knowledgePointApi.list(token, chapterId, params);
      if (response.success) {
        setKnowledgePoints(response.data.knowledge_points);
      }
    } catch (error) {
      message.error('加载知识点失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/admin/courses');
  };

  const handleCreate = () => {
    setEditingKP(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (kp: KnowledgePoint) => {
    setEditingKP(kp);
    form.setFieldsValue({
      ...kp,
      key_points: kp.key_points?.join('\n'),
    });
    setModalVisible(true);
  };

  const handleDelete = async (kpId: string) => {
    try {
      const response = await knowledgePointApi.delete(token, kpId);
      if (response.success) {
        message.success('删除成功');
        loadKnowledgePoints();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        key_points: values.key_points?.split('\n').filter((kp: string) => kp.trim()),
      };
      
      let response;
      if (editingKP) {
        response = await knowledgePointApi.update(token, editingKP.id, data);
      } else {
        response = await knowledgePointApi.create(token, chapterId!, data);
      }
      
      if (response.success) {
        message.success(editingKP ? '更新成功' : '创建成功');
        setModalVisible(false);
        loadKnowledgePoints();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 构建树形数据
  const buildTreeData = () => {
    const levelMap = new Map<number, KnowledgePoint[]>();
    knowledgePoints.forEach(kp => {
      if (!levelMap.has(kp.level)) {
        levelMap.set(kp.level, []);
      }
      levelMap.get(kp.level)!.push(kp);
    });

    const treeData = [];
    for (let level = 0; level <= 6; level++) {
      const kps = levelMap.get(level) || [];
      if (kps.length > 0) {
        const levelDesc = chapterInfo?.level_descriptions?.[level] || `Level ${level}`;
        treeData.push({
          title: `${levelDesc} (${kps.length}个知识点)`,
          key: `level-${level}`,
          children: kps.map(kp => ({
            title: `${kp.id} - ${kp.name}`,
            key: kp.id,
          })),
        });
      }
    }
    return treeData;
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '知识点名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
    },
    {
      title: '层级',
      dataIndex: 'level',
      key: 'level',
      width: 80,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: KnowledgePoint) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个知识点吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Layout className="kp-layout">
      <Header className="kp-header">
        <div className="kp-header-content">
          <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
            返回章节列表
          </Button>
          <h2 className="kp-header-title">
            {chapterInfo?.name || '知识点配置'}
          </h2>
        </div>
      </Header>
      
      <Layout>
        <Sider width={300} className="kp-sider" theme="light">
          <Card title="知识点层级" size="small">
            <Tree
              treeData={buildTreeData()}
              defaultExpandAll
              onSelect={(selectedKeys) => {
                if (selectedKeys.length > 0 && selectedKeys[0].toString().startsWith('level-')) {
                  const level = parseInt(selectedKeys[0].toString().split('-')[1]);
                  setSelectedLevel(level);
                } else {
                  setSelectedLevel(undefined);
                }
              }}
            />
          </Card>
        </Sider>
        
        <Content className="kp-content">
          <Card className="kp-card">
            <div className="kp-toolbar">
              <Space>
                {selectedLevel !== undefined && (
                  <Button onClick={() => setSelectedLevel(undefined)}>
                    显示全部
                  </Button>
                )}
              </Space>
              
              <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                新建知识点
              </Button>
            </div>
            
            <Table
              columns={columns}
              dataSource={knowledgePoints}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 20 }}
            />
          </Card>
        </Content>
      </Layout>
      
      <Modal
        title={editingKP ? '编辑知识点' : '新建知识点'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="id"
            label="知识点ID"
            rules={[{ required: true, message: '请输入知识点ID' }]}
          >
            <Input placeholder="如：K1, K2" disabled={!!editingKP} />
          </Form.Item>
          
          <Form.Item
            name="name"
            label="知识点名称"
            rules={[{ required: true, message: '请输入知识点名称' }]}
          >
            <Input placeholder="知识点名称" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select placeholder="选择类型">
              <Select.Option value="概念">概念</Select.Option>
              <Select.Option value="公式">公式</Select.Option>
              <Select.Option value="技能">技能</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="level"
            label="层级"
            rules={[{ required: true, message: '请选择层级' }]}
          >
            <Select placeholder="选择层级">
              {[0, 1, 2, 3, 4, 5, 6].map(level => (
                <Select.Option key={level} value={level}>
                  Level {level} - {chapterInfo?.level_descriptions?.[level] || ''}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="知识点描述" />
          </Form.Item>
          
          <Form.Item name="key_points" label="核心要点（每行一个）">
            <Input.TextArea rows={3} placeholder="核心要点，每行一个" />
          </Form.Item>
          
          <Form.Item name="sort_order" label="排序权重">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item label="掌握标准">
            <Input.Group compact>
              <Form.Item name={['mastery_criteria', 'type']} noStyle>
                <Select style={{ width: '33%' }} placeholder="检查类型">
                  <Select.Option value="concept_check">概念检查</Select.Option>
                  <Select.Option value="formula_check">公式检查</Select.Option>
                  <Select.Option value="skill_check">技能检查</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name={['mastery_criteria', 'method']} noStyle>
                <Select style={{ width: '33%' }} placeholder="评估方式">
                  <Select.Option value="选择题">选择题</Select.Option>
                  <Select.Option value="填空题">填空题</Select.Option>
                  <Select.Option value="判断题">判断题</Select.Option>
                  <Select.Option value="计算题">计算题</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name={['mastery_criteria', 'question_count']} noStyle>
                <InputNumber style={{ width: '17%' }} min={1} placeholder="题数" />
              </Form.Item>
              <Form.Item name={['mastery_criteria', 'pass_threshold']} noStyle>
                <InputNumber style={{ width: '17%' }} min={1} placeholder="通过阈值" />
              </Form.Item>
            </Input.Group>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default AdminKnowledgePoints;
