import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Modal, Form, Input, InputNumber, message, Popconfirm, Select, Dropdown } from 'antd';
import { BookOutlined, PlusOutlined, EditOutlined, DeleteOutlined, LogoutOutlined, SettingOutlined, CloseOutlined, MoreOutlined } from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { chapterApi } from '../api/admin';
import './AdminCourses.css';

const { Header, Content } = Layout;

interface Chapter {
  id: string;
  name: string;
  grade: string;
  edition: string;
  subject: string;
  description: string;
  total_knowledge_points: number;
  estimated_hours: number;
  status: string;
  created_at: string;
}

interface BookData {
  grade: string;
  editions: {
    edition: string;
    subjects: {
      subject: string;
      chapters: Chapter[];
    }[];
  }[];
}

const AdminCourses: React.FC = () => {
  const navigate = useNavigate();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [books, setBooks] = useState<BookData[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingChapter, setEditingChapter] = useState<Chapter | null>(null);
  const [selectedBook, setSelectedBook] = useState<BookData | null>(null);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [configType, setConfigType] = useState<'grade' | 'subject'>('grade');
  const [editingGrade, setEditingGrade] = useState<string>('');
  const [editGradeModalVisible, setEditGradeModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editGradeForm] = Form.useForm();

  const token = localStorage.getItem('admin_token') || '';

  // 配置数据(可以从localStorage或后端加载)
  const [grades, setGrades] = useState<string[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [newItem, setNewItem] = useState('');

  useEffect(() => {
    loadConfig();
    loadChapters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadConfig = () => {
    const defaultGrades = ['初一', '初二', '初三', '高一', '高二', '高三'];
    const defaultSubjects = ['数学', '语文', '英语', '物理', '化学'];

    const savedGrades = localStorage.getItem('admin_grades');
    const savedSubjects = localStorage.getItem('admin_subjects');

    if (savedGrades) {
      setGrades(JSON.parse(savedGrades));
    } else {
      setGrades(defaultGrades);
      localStorage.setItem('admin_grades', JSON.stringify(defaultGrades));
    }

    if (savedSubjects) {
      setSubjects(JSON.parse(savedSubjects));
    } else {
      setSubjects(defaultSubjects);
      localStorage.setItem('admin_subjects', JSON.stringify(defaultSubjects));
    }
  };

  const loadChapters = async () => {
    setLoading(true);
    try {
      const response = await chapterApi.list(token, {});
      if (response.success) {
        setChapters(response.data.chapters);

        // 从 localStorage 读取最新配置
        const savedGrades = localStorage.getItem('admin_grades');
        const savedSubjects = localStorage.getItem('admin_subjects');
        const currentGrades = savedGrades ? JSON.parse(savedGrades) : [];
        const currentSubjects = savedSubjects ? JSON.parse(savedSubjects) : [];

        organizeBooks(response.data.chapters, currentGrades, currentSubjects);
      }
    } catch (error) {
      message.error('加载章节失败');
    } finally {
      setLoading(false);
    }
  };

  const organizeBooks = (chapters: Chapter[], gradeList: string[], subjectList: string[]) => {
    const bookMap = new Map<string, BookData>();

    // 先初始化所有已配置的年级（即使没有章节数据）
    gradeList.forEach(grade => {
      bookMap.set(grade, {
        grade: grade,
        editions: [{
          edition: '全部科目',
          subjects: subjectList.map(subject => ({
            subject: subject,
            chapters: []
          }))
        }]
      });
    });

    // 然后添加章节数据
    chapters.forEach(chapter => {
      if (!bookMap.has(chapter.grade)) {
        bookMap.set(chapter.grade, {
          grade: chapter.grade,
          editions: []
        });
      }
      const gradeData = bookMap.get(chapter.grade)!;

      // 获取"全部科目"版本
      let editionData = gradeData.editions.find(e => e.edition === '全部科目');
      if (!editionData) {
        editionData = {
          edition: '全部科目',
          subjects: subjectList.map(subject => ({
            subject: subject,
            chapters: []
          }))
        };
        gradeData.editions.push(editionData);
      }

      // 找到对应科目并添加章节
      let subjectData = editionData.subjects.find(s => s.subject === chapter.subject);
      if (!subjectData) {
        subjectData = {
          subject: chapter.subject,
          chapters: []
        };
        editionData.subjects.push(subjectData);
      }

      subjectData.chapters.push(chapter);
    });

    const booksArray = Array.from(bookMap.values()).sort((a, b) => {
      return gradeList.indexOf(a.grade) - gradeList.indexOf(b.grade);
    });

    setBooks(booksArray);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    navigate('/admin/login');
  };

  const handleCreate = (preFillGrade?: string, preFillSubject?: string) => {
    setEditingChapter(null);
    form.resetFields();
    if (preFillGrade) {
      form.setFieldsValue({ grade: preFillGrade });
    }
    if (preFillSubject) {
      form.setFieldsValue({ subject: preFillSubject });
    }
    setModalVisible(true);
  };

  const handleEdit = (chapter: Chapter) => {
    setEditingChapter(chapter);
    form.setFieldsValue(chapter);
    setModalVisible(true);
  };

  const handleDelete = async (chapterId: string) => {
    try {
      const response = await chapterApi.delete(token, chapterId);
      if (response.success) {
        message.success('删除成功');
        loadChapters();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      let response;
      if (editingChapter) {
        response = await chapterApi.update(token, editingChapter.id, values);
      } else {
        response = await chapterApi.create(token, values);
      }
      
      if (response.success) {
        message.success(editingChapter ? '更新成功' : '创建成功');
        setModalVisible(false);
        loadChapters();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const handleConfigKnowledgePoints = (chapterId: string) => {
    navigate(`/admin/knowledge-points/${chapterId}`);
  };

  const handleAddItem = () => {
    const trimmedItem = newItem.trim();
    if (!trimmedItem) {
      message.warning('请输入内容');
      return;
    }

    if (configType === 'grade') {
      const exists = grades.some(g => g.toLowerCase() === trimmedItem.toLowerCase());
      if (exists) {
        message.warning('该年级已存在');
        return;
      }
      const newGrades = [...grades, trimmedItem];
      setGrades(newGrades);
      localStorage.setItem('admin_grades', JSON.stringify(newGrades));
      // 重新组织年级展示
      organizeBooks(chapters, newGrades, subjects);
    } else {
      const exists = subjects.some(s => s.toLowerCase() === trimmedItem.toLowerCase());
      if (exists) {
        message.warning('该科目已存在');
        return;
      }
      const newSubjects = [...subjects, trimmedItem];
      setSubjects(newSubjects);
      localStorage.setItem('admin_subjects', JSON.stringify(newSubjects));
      // 重新组织科目展示
      organizeBooks(chapters, grades, newSubjects);
    }
    
    setNewItem('');
    setConfigModalVisible(false);
    message.success('添加成功');
  };

  const handleDeleteItem = (item: string, type: 'grade' | 'subject') => {
    if (type === 'grade') {
      const newGrades = grades.filter(g => g !== item);
      setGrades(newGrades);
      localStorage.setItem('admin_grades', JSON.stringify(newGrades));
      // 重新组织年级展示
      organizeBooks(chapters, newGrades, subjects);
    } else {
      const newSubjects = subjects.filter(s => s !== item);
      setSubjects(newSubjects);
      localStorage.setItem('admin_subjects', JSON.stringify(newSubjects));
      // 重新组织科目展示
      organizeBooks(chapters, grades, newSubjects);
    }
    message.success('删除成功');
  };

  const handleEditGrade = (grade: string) => {
    setEditingGrade(grade);
    editGradeForm.setFieldsValue({ name: grade });
    setEditGradeModalVisible(true);
  };

  const handleUpdateGrade = async (values: { name: string }) => {
    const newName = values.name.trim();

    if (!newName) {
      message.warning('年级名称不能为空');
      return;
    }

    if (newName === editingGrade) {
      setEditGradeModalVisible(false);
      return;
    }

    // 检查是否已存在（排除当前编辑的年级）
    const exists = grades.some(g => g.toLowerCase() === newName.toLowerCase() && g !== editingGrade);
    if (exists) {
      message.warning('该年级已存在');
      return;
    }

    // 更新年级列表
    const newGrades = grades.map(g => g === editingGrade ? newName : g);
    setGrades(newGrades);
    localStorage.setItem('admin_grades', JSON.stringify(newGrades));

    // 更新章节中的年级名称
    const updatedChapters = chapters.map(chapter =>
      chapter.grade === editingGrade ? { ...chapter, grade: newName } : chapter
    );
    setChapters(updatedChapters);

    // 重新组织展示
    organizeBooks(updatedChapters, newGrades, subjects);

    // TODO: 如果需要，调用后端API更新章节数据
    // for (const chapter of chapters.filter(c => c.grade === editingGrade)) {
    //   await chapterApi.update(token, chapter.id, { ...chapter, grade: newName });
    // }

    setEditGradeModalVisible(false);
    message.success('编辑成功');
  };

  const getTotalChapters = (book: BookData) => {
    return book.editions.reduce(
      (sum, edition) => sum + edition.subjects.reduce(
        (s, subject) => s + subject.chapters.length, 0
      ), 0
    );
  };

  const getTotalKnowledgePoints = (book: BookData) => {
    return book.editions.reduce(
      (sum, edition) => sum + edition.subjects.reduce(
        (s, subject) => s + subject.chapters.reduce((total, ch) => total + ch.total_knowledge_points, 0), 0
      ), 0
    );
  };

  const renderCourses = () => (
    <>
      {books.length === 0 && !loading ? (
        <div className="empty-state">
          <BookOutlined />
          <h3>暂无章节</h3>
          <p>开始创建你的第一个章节</p>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleCreate()}>
            创建章节
          </Button>
        </div>
      ) : (
        <div className="books-container">
          {books.map(book => {
            const menuItems: MenuProps['items'] = [
              {
                key: 'edit',
                icon: <EditOutlined />,
                label: '编辑年级',
                onClick: (info) => {
                  info.domEvent.stopPropagation();
                  handleEditGrade(book.grade);
                },
              },
              {
                key: 'delete',
                label: (
                  <Popconfirm
                    title="确定删除此年级?"
                    description="删除后该年级下的所有章节都将被删除"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDeleteItem(book.grade, 'grade');
                    }}
                    onCancel={(e) => e?.stopPropagation()}
                    okText="删除"
                    cancelText="取消"
                  >
                    <span onClick={(e) => e.stopPropagation()}>
                      <DeleteOutlined /> 删除年级
                    </span>
                  </Popconfirm>
                ),
              },
            ];

            return (
              <div 
                key={book.grade} 
                className="book-card"
                onClick={() => setSelectedBook(book)}
              >
                <div className="book-header">
                  <BookOutlined className="book-icon" />
                  <Dropdown 
                    menu={{ items: menuItems }} 
                    trigger={['click']}
                    placement="bottomRight"
                  >
                    <MoreOutlined 
                      className="card-more-icon"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Dropdown>
                </div>
                <div className="book-info">
                  <h2 className="grade-title">{book.grade}</h2>
                  <p className="grade-subtitle">
                    {getTotalChapters(book)} 个章节 · {getTotalKnowledgePoints(book)} 个知识点
                  </p>
                  <p className="book-meta">
                    {subjects.length} 个科目<br />
                    点击查看详情
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );

  return (
    <Layout className="admin-layout">
      <Header className="admin-header">
        <div className="admin-header-content">
          <div className="admin-header-left">
            <BookOutlined className="admin-header-icon" />
            <span className="admin-header-title">课程配置</span>
          </div>
          <div className="admin-header-right">
            <Button 
              type="link" 
              onClick={() => {
                setConfigType('grade');
                setConfigModalVisible(true);
              }}
            >
              新增年级
            </Button>
            <Button type="link" icon={<LogoutOutlined />} onClick={handleLogout}>
              退出
            </Button>
          </div>
        </div>
      </Header>

      <Content className="admin-content">
        {renderCourses()}
      </Content>

      {/* 详情面板 */}
      <div className={`book-expand ${selectedBook ? 'active' : ''}`} onClick={() => setSelectedBook(null)}>
        {selectedBook && (
          <div className="book-expand-content" onClick={(e) => e.stopPropagation()}>
            <div className="expand-header">
              <h2 className="expand-title">{selectedBook.grade}</h2>
              <div className="expand-header-actions">
                <Button 
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfigType('subject');
                    setConfigModalVisible(true);
                  }}
                >
                  新增科目
                </Button>
                <CloseOutlined className="expand-close" onClick={() => setSelectedBook(null)} />
              </div>
            </div>
            
            {selectedBook.editions.map(edition => (
              <div key={edition.edition} className="expand-section">
                {edition.subjects.map(subject => (
                  <div key={subject.subject} className="expand-item">
                    <div className="expand-item-header">
                      <div>
                        <div className="expand-item-title">{subject.subject}</div>
                        <div className="expand-item-meta">
                          {subject.chapters.length} 个章节 · {subject.chapters.reduce((sum, ch) => sum + ch.total_knowledge_points, 0)} 个知识点
                        </div>
                      </div>
                      <Button 
                        type="primary"
                        size="small"
                        icon={<PlusOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCreate(selectedBook.grade, subject.subject);
                        }}
                      >
                        新建章节
                      </Button>
                    </div>
                    <div className="expand-item-content">
                      {subject.chapters.length === 0 ? (
                        <div className="empty-subject">
                          <p>暂无章节，点击上方"新建章节"按钮添加</p>
                        </div>
                      ) : (
                        subject.chapters.map(chapter => (
                          <div key={chapter.id} className="nested-item">
                            <div>
                              <div className="nested-item-name">{chapter.name}</div>
                              <div className="nested-item-meta">
                                {chapter.total_knowledge_points} 个知识点 · {chapter.estimated_hours} 学时
                              </div>
                            </div>
                            <div className="chapter-actions">
                              <Button
                                size="small"
                                type="primary"
                                icon={<SettingOutlined />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleConfigKnowledgePoints(chapter.id);
                                }}
                              >
                                配置
                              </Button>
                              <Button
                                size="small"
                                icon={<EditOutlined />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleEdit(chapter);
                                }}
                              >
                                编辑
                              </Button>
                              <Popconfirm
                                title="确定删除此章节?"
                                onConfirm={(e) => {
                                  e?.stopPropagation();
                                  handleDelete(chapter.id);
                                }}
                                okText="删除"
                                cancelText="取消"
                              >
                                <Button
                                  size="small"
                                  danger
                                  icon={<DeleteOutlined />}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  删除
                                </Button>
                              </Popconfirm>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 配置添加弹窗 */}
      <Modal
        title={configType === 'grade' ? '添加年级' : '添加科目'}
        open={configModalVisible}
        onCancel={() => {
          setConfigModalVisible(false);
          setNewItem('');
        }}
        onOk={handleAddItem}
        okText="添加"
        cancelText="取消"
      >
        <Form>
          <Form.Item label={configType === 'grade' ? '年级名称' : '科目名称'}>
            <Input
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              placeholder={configType === 'grade' ? '如：初一' : '如：数学'}
              onPressEnter={handleAddItem}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑年级弹窗 */}
      <Modal
        title="编辑年级"
        open={editGradeModalVisible}
        onCancel={() => setEditGradeModalVisible(false)}
        onOk={() => editGradeForm.submit()}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editGradeForm} layout="vertical" onFinish={handleUpdateGrade}>
          <Form.Item
            name="name"
            label="年级名称"
            rules={[{ required: true, message: '请输入年级名称' }]}
          >
            <Input placeholder="如：初一" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingChapter ? '编辑章节' : '新建章节'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="name"
            label="章节名称"
            rules={[{ required: true, message: '请输入章节名称' }]}
          >
            <Input placeholder="如：一次函数" />
          </Form.Item>
          
          <Form.Item
            name="grade"
            label="年级"
            rules={[{ required: true, message: '请选择年级' }]}
          >
            <Select placeholder="选择年级">
              {grades.map(grade => (
                <Select.Option key={grade} value={grade}>{grade}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="edition"
            label="教材版本"
            rules={[{ required: true, message: '请选择教材版本' }]}
          >
            <Select placeholder="选择教材版本">
              <Select.Option value="人教版">人教版</Select.Option>
              <Select.Option value="北师大版">北师大版</Select.Option>
              <Select.Option value="苏教版">苏教版</Select.Option>
              <Select.Option value="鲁教版">鲁教版</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="subject"
            label="科目"
            rules={[{ required: true, message: '请选择科目' }]}
          >
            <Select placeholder="选择科目">
              {subjects.map(subject => (
                <Select.Option key={subject} value={subject}>{subject}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="章节描述" />
          </Form.Item>
          
          <Form.Item name="estimated_hours" label="预估学时（小时）">
            <InputNumber min={0} step={0.5} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default AdminCourses;
