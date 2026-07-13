import React, { useEffect, useMemo, useState } from 'react';
import { courseApi, learningApi } from '../api';
import { useAuthStore } from '../store';
import type { Course, ProgressResponse } from '../types';
import './LearningSpace.css';

interface LearningSpaceProps {
  onOpenCourse: (courseId: string, options?: { chapterId?: string; kpId?: string; startLearning?: boolean }) => void;
}

interface CourseProgressView {
  course: Course;
  progress: ProgressResponse | null;
}

const EDITIONS = ['人教版', '北师大版', '苏教版', '鲁教版', '华师大版', '人教版新教材'];
const GRADES = ['初一', '初二', '初三', '高一', '高二', '高三'];
const ALL_SUBJECTS = ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理'];
const SUBJECT_ICONS: Record<string, string> = {
  '数学': '📐', '语文': '📖', '英语': '🌐', '物理': '⚛️',
  '化学': '🧪', '生物': '🧬', '历史': '📜', '地理': '🗺️',
};

const LAST_COURSE_KEY = 'learning:last_course_id';

const LearningSpace: React.FC<LearningSpaceProps> = ({
  onOpenCourse,
}) => {
  const user = useAuthStore((s) => s.user);
  const [courses, setCourses] = useState<CourseProgressView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [edition, setEdition] = useState(user?.edition || '人教版');
  const [grade, setGrade] = useState(user?.grade || '初二');

  useEffect(() => {
    if (user) {
      if (user.edition) setEdition(user.edition);
      if (user.grade) setGrade(user.grade);
    }
  }, [user]);

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

        const courseList = (courseRes.data.data || []).filter((c) => {
          const matchEdition = !edition || c.edition === edition;
          const matchGrade = !grade || c.grade === grade;
          return matchEdition && matchGrade;
        });

        const progressList = await Promise.all(
          courseList.map(async (course) => {
            try {
              const progressRes = await learningApi.getProgress(course.id);
              return { course, progress: progressRes.data.success ? progressRes.data.data : null };
            } catch {
              return { course, progress: null };
            }
          })
        );

        setCourses(progressList);
      } catch (loadError) {
        console.error('学习空间加载失败:', loadError);
        setError(loadError instanceof Error ? loadError.message : String(loadError));
      } finally {
        setLoading(false);
      }
    };

    loadCourses();
  }, [edition, grade]);

  const featuredCourse = useMemo(() => {
    const lastCourseId = localStorage.getItem(LAST_COURSE_KEY);
    return (
      courses.find(({ course }) => course.id === lastCourseId) ||
      courses.find(({ progress }) => progress?.current_kp_id) ||
      courses[0] ||
      null
    );
  }, [courses]);

  const subjectProgressMap = useMemo(() => {
    const map: Record<string, {
      totalKps: number;
      masteredKps: number;
      courseCount: number;
      primary: CourseProgressView | null;
      currentKpName: string;
    }> = {};

    for (const { course, progress } of courses) {
      if (!map[course.subject]) {
        map[course.subject] = {
          totalKps: 0,
          masteredKps: 0,
          courseCount: 0,
          primary: null,
          currentKpName: '',
        };
      }
      const stats = map[course.subject];
      stats.courseCount += 1;
      stats.totalKps += progress?.total_count || course.total_knowledge_points;
      stats.masteredKps += progress?.mastered_count || 0;

      if (!stats.primary || progress?.current_kp_id) {
        stats.primary = { course, progress };
      }
      if (progress?.current_kp_name) {
        stats.currentKpName = progress.current_kp_name;
      }
    }
    return map;
  }, [courses]);

  const spaceStats = useMemo(() => {
    const totalCourses = courses.length;
    const totalKps = courses.reduce(
      (sum, { course, progress }) => sum + (progress?.total_count || course.total_knowledge_points || 0),
      0
    );
    const masteredKps = courses.reduce(
      (sum, { progress }) => sum + (progress?.mastered_count || 0),
      0
    );
    const activeSubjects = Object.values(subjectProgressMap).filter((stats) => stats.courseCount > 0).length;
    const masteryRate = totalKps > 0 ? Math.round((masteredKps / totalKps) * 100) : 0;

    return { totalCourses, totalKps, masteredKps, activeSubjects, masteryRate };
  }, [courses, subjectProgressMap]);

  const handleContinueLearning = () => {
    if (!featuredCourse) return;
    const progress = featuredCourse.progress;
    const kpId = progress?.current_kp_id || undefined;
    localStorage.setItem(LAST_COURSE_KEY, featuredCourse.course.id);
    onOpenCourse(featuredCourse.course.id, { kpId, startLearning: true });
  };

  const handleOpenSubject = (subject: string) => {
    const targetCourse = subjectProgressMap[subject]?.primary?.course;
    if (!targetCourse) return;
    localStorage.setItem(LAST_COURSE_KEY, targetCourse.id);
    onOpenCourse(targetCourse.id);
  };

  if (loading) {
    return (
      <div className="learning-space">
        <div className="space-shell"><div className="space-loading">正在整理你的学习空间...</div></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="learning-space">
        <div className="space-shell"><div className="space-error">{error}</div></div>
      </div>
    );
  }

  return (
    <div className="learning-space">
      <div className="space-shell">
        <header className="space-header">
          <div>
            <div className="space-context" aria-label="当前教材和年级">
              <select value={edition} onChange={(e) => setEdition(e.target.value)}>
                {EDITIONS.map((e) => <option key={e} value={e}>{e}</option>)}
              </select>
              <span className="context-sep">·</span>
              <select value={grade} onChange={(e) => setGrade(e.target.value)}>
                {GRADES.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <h1>学习空间</h1>
            <p>从科目总览进入课程控制台，继续当前知识点。</p>
          </div>
          <div className="space-orbit" aria-hidden="true">
            <div
              className="space-orbit-ring"
              style={{ '--space-progress': `${spaceStats.masteryRate}%` } as React.CSSProperties}
            >
              <span>{spaceStats.masteryRate}%</span>
            </div>
          </div>
        </header>

        <section className="space-overview-card">
          <div className="space-stat">
            <strong>{spaceStats.totalCourses}</strong>
            <span>可学课程</span>
          </div>
          <div className="space-stat">
            <strong>{spaceStats.activeSubjects}</strong>
            <span>已开科目</span>
          </div>
          <div className="space-stat">
            <strong>{spaceStats.masteredKps}/{spaceStats.totalKps}</strong>
            <span>知识点掌握</span>
          </div>
          <div className="space-overview-progress" aria-hidden="true">
            <div style={{ width: `${spaceStats.masteryRate}%` }} />
          </div>
        </section>

        {featuredCourse && (
          <section className="space-continue-card">
            <div className="hero-left">
              <div className="hero-eyebrow">
                {SUBJECT_ICONS[featuredCourse.course.subject]} 继续学习
              </div>
              <h2>
                {featuredCourse.course.name}
                {featuredCourse.progress?.current_kp_name
                  ? ` · ${featuredCourse.progress.current_kp_name}`
                  : ''}
              </h2>
              <div className="hero-progress">
                <div className="hero-progress-bar">
                  <div style={{ width: `${Math.round((featuredCourse.progress?.mastery_rate || 0) * 100)}%` }} />
                </div>
                <span>{Math.round((featuredCourse.progress?.mastery_rate || 0) * 100)}%</span>
              </div>
              <span className="hero-meta">
                已掌握 {featuredCourse.progress?.mastered_count || 0}/{featuredCourse.progress?.total_count || featuredCourse.course.total_knowledge_points}
              </span>
            </div>
            <button className="hero-cta" onClick={handleContinueLearning}>
              继续学习 →
            </button>
          </section>
        )}

        <section className="subject-section">
          <div className="subject-section-header">
            <div>
              <h2>选择科目</h2>
              <p>点击科目直接进入对应课程控制台</p>
            </div>
          </div>
          <div className="subject-grid">
            {ALL_SUBJECTS.map((subject) => {
              const stats = subjectProgressMap[subject];
              const hasCourses = stats && stats.courseCount > 0;
              const percent = stats && stats.totalKps > 0
                ? Math.round((stats.masteredKps / stats.totalKps) * 100)
                : 0;
              const course = stats?.primary?.course;
              return (
                <button
                  key={subject}
                  type="button"
                  className={`subject-card ${hasCourses ? 'active' : 'empty'}`}
                  onClick={() => hasCourses && handleOpenSubject(subject)}
                  disabled={!hasCourses}
                >
                  <span className="subject-icon">{SUBJECT_ICONS[subject]}</span>
                  <span className="subject-name">{subject}</span>
                  <span className="subject-meta">
                    {hasCourses && course ? `${course.grade} · ${course.edition}` : '暂无课程'}
                  </span>
                  <span className="subject-current">
                    {hasCourses ? (stats.currentKpName ? `当前：${stats.currentKpName}` : course?.name || '进入课程控制台') : '等待开课'}
                  </span>
                  <span className="subject-progress">
                    {hasCourses ? `${percent}%` : '--'}
                  </span>
                  <span className="subject-count">
                    {hasCourses ? `${stats.masteredKps}/${stats.totalKps} 已掌握` : '暂无课程'}
                  </span>
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
};

export default LearningSpace;
