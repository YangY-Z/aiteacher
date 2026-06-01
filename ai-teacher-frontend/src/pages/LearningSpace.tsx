import React, { useEffect, useMemo, useState } from 'react';
import { courseApi, learningApi } from '../api';
import type { Course, KnowledgePointProgress, ProgressResponse } from '../types';
import './LearningSpace.css';

interface LearningSpaceProps {
  onOpenCourse: (courseId: string) => void;
  onAskTeacher: () => void;
  onOpenImprovement: () => void;
}

interface CourseProgressView {
  course: Course;
  progress: ProgressResponse | null;
}

const LAST_COURSE_KEY = 'learning:last_course_id';

const subjectClassName = (subject: string) => {
  if (subject.includes('数学')) return 'math';
  if (subject.includes('英语')) return 'english';
  if (subject.includes('物理')) return 'physics';
  if (subject.includes('化学')) return 'chemistry';
  return 'default';
};

const findNextKnowledgePoint = (progress: ProgressResponse | null): KnowledgePointProgress | null => {
  const kps = progress?.knowledge_points || [];
  return (
    kps.find((kp) => kp.id === progress?.current_kp_id || kp.status === 'current' || kp.status === 'in_progress') ||
    kps.find((kp) => kp.status !== 'completed' && kp.status !== 'skipped' && kp.status !== 'locked') ||
    kps.find((kp) => kp.status !== 'locked') ||
    null
  );
};

const LearningSpace: React.FC<LearningSpaceProps> = ({
  onOpenCourse,
  onAskTeacher,
  onOpenImprovement,
}) => {
  const [courses, setCourses] = useState<CourseProgressView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');

  useEffect(() => {
    const loadCourses = async () => {
      try {
        setLoading(true);
        setError(null);
        const courseRes = await courseApi.getAll();
        if (!courseRes.data.success) {
          setError(courseRes.data.message || '课程加载失败');
          return;
        }

        const courseList = courseRes.data.data || [];
        const progressList = await Promise.all(
          courseList.map(async (course) => {
            try {
              const progressRes = await learningApi.getProgress(course.id);
              return {
                course,
                progress: progressRes.data.success ? progressRes.data.data : null,
              };
            } catch (progressError) {
              console.warn('课程进度加载失败:', course.id, progressError);
              return { course, progress: null };
            }
          })
        );

        setCourses(progressList);
      } catch (loadError) {
        console.error('学习空间加载失败:', loadError);
        const message = loadError instanceof Error ? loadError.message : String(loadError);
        setError(`学习空间加载失败: ${message}`);
      } finally {
        setLoading(false);
      }
    };

    loadCourses();
  }, []);

  const subjects = useMemo(
    () => ['all', ...Array.from(new Set(courses.map(({ course }) => course.subject)))],
    [courses]
  );

  const grades = useMemo(
    () => ['all', ...Array.from(new Set(courses.map(({ course }) => course.grade)))],
    [courses]
  );

  const filteredCourses = useMemo(
    () =>
      courses.filter(({ course }) => {
        const subjectMatched = selectedSubject === 'all' || course.subject === selectedSubject;
        const gradeMatched = selectedGrade === 'all' || course.grade === selectedGrade;
        return subjectMatched && gradeMatched;
      }),
    [courses, selectedGrade, selectedSubject]
  );

  const featuredCourse = useMemo(() => {
    const lastCourseId = localStorage.getItem(LAST_COURSE_KEY);
    return (
      courses.find(({ course }) => course.id === lastCourseId) ||
      courses.find(({ progress }) => progress?.current_kp_id) ||
      courses[0] ||
      null
    );
  }, [courses]);

  const handleOpenCourse = (courseId: string) => {
    localStorage.setItem(LAST_COURSE_KEY, courseId);
    onOpenCourse(courseId);
  };

  if (loading) {
    return (
      <div className="learning-space">
        <div className="space-shell">
          <div className="space-loading">正在整理你的学习空间...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="learning-space">
        <div className="space-shell">
          <div className="space-error">{error}</div>
        </div>
      </div>
    );
  }

  const featuredNext = findNextKnowledgePoint(featuredCourse?.progress || null);
  const featuredPercent = Math.round((featuredCourse?.progress?.mastery_rate || 0) * 100);

  return (
    <div className="learning-space">
      <div className="space-shell">
        <section className="space-hero">
          <div className="space-hero-copy">
            <div className="space-eyebrow">学习空间</div>
            <h1>今天继续哪一门？</h1>
            <p>{featuredNext ? `下一步：${featuredNext.name}` : '选择一门课程，开始今天的学习节奏。'}</p>
          </div>

          {featuredCourse ? (
            <button
              type="button"
              className={`space-feature-card ${subjectClassName(featuredCourse.course.subject)}`}
              onClick={() => handleOpenCourse(featuredCourse.course.id)}
            >
              <div className="feature-visual" aria-hidden="true">
                <div className="visual-grid" />
                <div className="visual-curve" />
              </div>
              <div className="feature-content">
                <span>{featuredCourse.course.subject}</span>
                <strong>{featuredCourse.course.name}</strong>
                <small>{featuredCourse.course.grade}</small>
              </div>
              <div className="feature-progress" style={{ '--progress': `${featuredPercent}%` } as React.CSSProperties}>
                <span>{featuredPercent}%</span>
              </div>
            </button>
          ) : null}
        </section>

        <div className="space-filter-row" aria-label="学习范围筛选">
          <div className="space-filter-group">
            {subjects.map((subject) => (
              <button
                key={subject}
                type="button"
                className={`space-chip ${selectedSubject === subject ? 'active' : ''}`}
                onClick={() => setSelectedSubject(subject)}
              >
                {subject === 'all' ? '全部科目' : subject}
              </button>
            ))}
          </div>
          <div className="space-filter-group">
            {grades.map((grade) => (
              <button
                key={grade}
                type="button"
                className={`space-chip ${selectedGrade === grade ? 'active' : ''}`}
                onClick={() => setSelectedGrade(grade)}
              >
                {grade === 'all' ? '全部年级' : grade}
              </button>
            ))}
          </div>
        </div>

        <section className="course-gallery">
          {filteredCourses.map(({ course, progress }) => {
            const percent = Math.round((progress?.mastery_rate || 0) * 100);
            const nextKp = findNextKnowledgePoint(progress);
            const subjectClass = subjectClassName(course.subject);

            return (
              <button
                key={course.id}
                type="button"
                className={`course-tile ${subjectClass}`}
                onClick={() => handleOpenCourse(course.id)}
              >
                <div className="course-art" aria-hidden="true">
                  <div className="course-art-grid" />
                  <div className="course-art-mark" />
                </div>
                <div className="course-tile-body">
                  <div className="course-tile-top">
                    <span>{course.subject}</span>
                    <span>{course.grade}</span>
                  </div>
                  <h2>{course.name}</h2>
                  <p>{nextKp ? nextKp.name : '准备开始'}</p>
                  <div className="course-progress-line" aria-hidden="true">
                    <div style={{ width: `${percent}%` }} />
                  </div>
                  <div className="course-tile-bottom">
                    <strong>{percent}%</strong>
                    <span>{progress?.mastered_count || 0}/{progress?.total_count || course.total_knowledge_points}</span>
                  </div>
                </div>
              </button>
            );
          })}
        </section>

        <section className="space-dock" aria-label="快捷入口">
          <button type="button" onClick={onAskTeacher}>
            <span className="dock-mark teacher" />
            小艾老师
          </button>
          <button type="button" onClick={onOpenImprovement}>
            <span className="dock-mark focus" />
            专项突破
          </button>
        </section>
      </div>
    </div>
  );
};

export default LearningSpace;
