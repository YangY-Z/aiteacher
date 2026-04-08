/**
 * AdminCourses 组件更新示例
 *
 * 这个文件展示了如何将localStorage管理年级科目改为使用新的API
 * 主要变更点：
 * 1. loadConfig() -> 调用 gradeApi.list() 和 subjectApi.list()
 * 2. handleAddItem() -> 调用 gradeApi.create() 或 subjectApi.create()
 * 3. handleDeleteGrade() -> 调用 gradeApi.delete()
 * 4. handleEditGrade() -> 调用 gradeApi.update()
 */

import React, { useState, useEffect } from 'react';
import { message } from 'antd';
import { gradeApi, subjectApi } from '../api/admin';

// 定义类型
interface Grade {
  id: string;
  name: string;
  code: string;
  level: string;
  subjects: GradeSubject[];
  sort_order: number;
  status: string;
}

interface Subject {
  id: string;
  name: string;
  code: string;
  category: string;
  sort_order: number;
  status: string;
}

interface GradeSubject {
  id: string;
  grade_id: string;
  subject_id: string;
  sort_order: number;
  status: string;
}

const AdminCoursesExample: React.FC = () => {
  // 状态
  const [grades, setGrades] = useState<Grade[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  /**
   * 加载年级和科目配置 - 使用新API
   */
  const loadConfig = async () => {
    setLoading(true);
    try {
      // 并行加载年级和科目
      const [gradesRes, subjectsRes] = await Promise.all([
        gradeApi.list({ active_only: true }),
        subjectApi.list({ active_only: true })
      ]);

      // 新API返回格式: { grades: [...], total: N }
      if (gradesRes.grades) {
        setGrades(gradesRes.grades);
      }

      // 新API返回格式: { subjects: [...], total: N }
      if (subjectsRes.subjects) {
        setSubjects(subjectsRes.subjects);
      }

    } catch (error: any) {
      console.error('加载配置失败:', error);
      message.error(error.response?.data?.detail || '加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 添加年级 - 使用新API
   */
  const handleAddGrade = async (name: string) => {
    try {
      // 生成年级代码（简化示例）
      const code = name.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

      // 判断学段
      let level = 'middle';
      if (name.includes('初')) {
        level = 'middle';
      } else if (name.includes('高')) {
        level = 'high';
      }

      // 调用API创建年级
      const response = await gradeApi.create({
        name,
        code,
        level,
        sort_order: grades.length + 1
      });

      message.success('年级创建成功');

      // 重新加载年级列表
      loadConfig();

      return response;
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '创建年级失败';
      message.error(errorMsg);
      throw error;
    }
  };

  /**
   * 添加科目 - 使用新API
   */
  const handleAddSubject = async (name: string) => {
    try {
      // 生成科目代码（简化示例）
      const code = name.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

      // 判断科目类别（简化示例）
      let category = 'comprehensive';
      if (['数学', '物理', '化学'].includes(name)) {
        category = 'science';
      } else if (['语文', '英语'].includes(name)) {
        category = 'language';
      }

      // 调用API创建科目
      const response = await subjectApi.create({
        name,
        code,
        category,
        sort_order: subjects.length + 1
      });

      message.success('科目创建成功');

      // 重新加载科目列表
      loadConfig();

      return response;
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '创建科目失败';
      message.error(errorMsg);
      throw error;
    }
  };

  /**
   * 为年级添加科目 - 使用新API
   */
  const handleAddSubjectToGrade = async (gradeId: string, subjectId: string) => {
    try {
      await gradeApi.addSubject(gradeId, {
        subject_id: subjectId,
        sort_order: 1
      });

      message.success('科目已添加到年级');
      loadConfig();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '添加失败';
      message.error(errorMsg);
    }
  };

  /**
   * 删除年级 - 使用新API
   */
  const handleDeleteGrade = async (gradeId: string) => {
    try {
      await gradeApi.delete(gradeId);
      message.success('年级删除成功');
      loadConfig();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '删除失败';
      message.error(errorMsg);
    }
  };

  /**
   * 编辑年级 - 使用新API
   */
  const handleEditGrade = async (gradeId: string, newName: string) => {
    try {
      await gradeApi.update(gradeId, { name: newName });
      message.success('年级更新成功');
      loadConfig();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '更新失败';
      message.error(errorMsg);
    }
  };

  /**
   * 组织章节数据展示 - 需要更新使用 grade_id 和 subject_id
   */
  const organizeBooksWithNewStructure = (chapters: any[]) => {
    // 首先根据年级ID分组
    const gradeMap = new Map<string, any>();

    grades.forEach(grade => {
      gradeMap.set(grade.id, {
        grade_name: grade.name,
        grade_id: grade.id,
        subjects: grade.subjects.map(gs => {
          // 查找科目详情
          const subject = subjects.find(s => s.id === gs.subject_id);
          return {
            subject_id: gs.subject_id,
            subject_name: subject?.name || '未知科目',
            chapters: []
          };
        })
      });
    });

    // 将章节分配到对应的年级和科目
    chapters.forEach(chapter => {
      const gradeData = gradeMap.get(chapter.grade_id);
      if (!gradeData) return;

      const subjectData = gradeData.subjects.find(
        (s: any) => s.subject_id === chapter.subject_id
      );
      if (subjectData) {
        subjectData.chapters.push(chapter);
      }
    });

    return Array.from(gradeMap.values());
  };

  return (
    <div>
      {/* 组件UI实现 */}
      <p>这是一个示例组件，展示如何使用新的API</p>
      <p>已加载 {grades.length} 个年级</p>
      <p>已加载 {subjects.length} 个科目</p>
    </div>
  );
};

export default AdminCoursesExample;

/**
 * 使用说明：
 *
 * 1. 替换 loadConfig() 函数：
 *    - 删除 localStorage.getItem('admin_grades') 相关代码
 *    - 使用 gradeApi.list() 和 subjectApi.list() 从后端加载
 *
 * 2. 替换 handleAddItem() 函数：
 *    - 删除 localStorage.setItem('admin_grades') 相关代码
 *    - 使用 gradeApi.create() 或 subjectApi.create() 创建
 *
 * 3. 更新 Chapter 接口：
 *    interface Chapter {
 *      id: string;
 *      name: string;
 *      grade: string;  // 保留用于显示
 *      grade_id: string;  // 新增：年级ID
 *      subject: string;  // 保留用于显示
 *      subject_id: string;  // 新增：科目ID
 *      edition: string;
 *      // ... 其他字段
 *    }
 *
 * 4. 更新 organizeBooks() 函数：
 *    - 使用 chapter.grade_id 和 chapter.subject_id 进行匹配
 *    - 从 grades 和 subjects 数组中查找对应的名称
 *
 * 5. 新增功能：
 *    - 为年级添加科目：gradeApi.addSubject(gradeId, { subject_id, sort_order })
 *    - 从年级移除科目：gradeApi.removeSubject(gradeId, subjectId)
 *    - 更新年级信息：gradeApi.update(gradeId, { name, sort_order, status })
 *    - 删除年级：gradeApi.delete(gradeId)
 */
