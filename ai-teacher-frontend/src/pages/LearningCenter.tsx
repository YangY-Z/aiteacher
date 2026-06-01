import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store';
import { learningApi, courseApi } from '../api';
import type { ProgressResponse, KnowledgePointProgress, Course } from '../types';
import KnowledgeGraph from '../components/KnowledgeGraph';
import './LearningCenter.css';

interface Badge {
  id: number;
  name: string;
  icon: string;
  earned: boolean;
}

const LearningCenter: React.FC<{
  courseId?: string;
  recommendedKpId?: string | null;
  autoStart?: boolean;
  onLearningStarted?: () => void;
  onBackToSpace?: () => void;
}> = ({ 
  courseId,
  recommendedKpId, 
  autoStart, 
  onLearningStarted,
  onBackToSpace,
}) => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllLayers, setShowAllLayers] = useState(false);
  const [selectedChapterId, setSelectedChapterId] = useState<string>('all');

  // 默认课程ID（一次函数）
  const DEFAULT_COURSE_ID = 'MATH_JUNIOR_01';
  const activeCourseId = courseId || DEFAULT_COURSE_ID;
  const ALL_CHAPTER_ID = 'all';
  const UNASSIGNED_CHAPTER_ID = 'unassigned';

  // 当 autoStart 为 true 时，自动跳转到学习页面
  useEffect(() => {
    if (autoStart && recommendedKpId) {
      onLearningStarted?.();
      navigate(`/learn?kp_id=${recommendedKpId}`);
    }
  }, [autoStart, recommendedKpId, onLearningStarted, navigate]);

  // 加载学习进度和课程信息
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 检查是否已登录
        const token = localStorage.getItem('token');
        if (!token) {
          setError('未登录，请先登录');
          return;
        }
        
        // 获取课程信息
        console.log('正在获取课程信息...', activeCourseId);
        const courseRes = await courseApi.getById(activeCourseId);
        console.log('课程响应:', courseRes);

        if (courseRes.data.success) {
          setCourse(courseRes.data.data);
        } else {
          console.error('获取课程失败:', courseRes);
          setError(`获取课程失败: ${courseRes.data.message || '未知错误'}`);
          return;
        }

        // 获取学习进度
        console.log('正在获取学习进度...', activeCourseId);
        const progressRes = await learningApi.getProgress(activeCourseId);
        console.log('进度响应:', progressRes);

        if (progressRes.data.success) {
          setProgress(progressRes.data.data);
        } else {
          console.error('获取进度失败:', progressRes);
          setError(`获取进度失败: ${progressRes.data.message || '未知错误'}`);
          return;
        }
      } catch (error) {
        console.error('加载学习进度失败:', error);
        const errorMsg = error instanceof Error ? error.message : String(error);
        setError(`加载失败: ${errorMsg}`);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [activeCourseId]);

  useEffect(() => {
    setSelectedChapterId(ALL_CHAPTER_ID);
  }, [activeCourseId]);

  // 徽章数据（暂时硬编码，后续可以从API获取）
  const badges: Badge[] = [
    { id: 1, name: '快速学习者', icon: '🏅', earned: (progress?.mastery_rate || 0) > 0.3 },
    { id: 2, name: '首次满分', icon: '💯', earned: (progress?.mastered_count || 0) > 0 },
    { id: 3, name: '连续学习', icon: '🔥', earned: (progress?.session_count || 0) >= 3 },
    { id: 4, name: '完美通关', icon: '👑', earned: (progress?.mastery_rate || 0) === 1 },
    { id: 5, name: '坚持不懈', icon: '💪', earned: (progress?.total_time || 0) > 60 },
    { id: 6, name: '数学天才', icon: '🧠', earned: (progress?.mastered_count || 0) >= 10 },
  ];

  const earnedBadgeCount = badges.filter(b => b.earned).length;

  const chapterViews = useMemo(() => {
    if (!progress || !course) return [];

    const orderMap = new Map(
      (course.knowledge_points || []).map((kp) => [kp.id, kp.sort_order ?? 0])
    );
    const chapterMap = new Map((course.chapters || []).map((chapter) => [chapter.id, chapter]));
    const grouped = new Map<string, KnowledgePointProgress[]>();

    progress.knowledge_points.forEach((kp) => {
      const chapterId = kp.chapter_id || UNASSIGNED_CHAPTER_ID;
      const group = grouped.get(chapterId) || [];
      group.push(kp);
      grouped.set(chapterId, group);
    });

    const sortedKps = (kps: KnowledgePointProgress[]) =>
      [...kps].sort((a, b) => {
        const orderA = orderMap.get(a.id) ?? 0;
        const orderB = orderMap.get(b.id) ?? 0;
        if (orderA !== orderB) return orderA - orderB;
        if (a.level !== b.level) return a.level - b.level;
        return a.name.localeCompare(b.name, 'zh-CN');
      });

    const knownChapterViews = (course.chapters || [])
      .slice()
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
      .map((chapter) => {
        const knowledgePoints = sortedKps(grouped.get(chapter.id) || []);
        const mastered = knowledgePoints.filter((kp) => kp.status === 'completed').length;
        const hasCurrent = knowledgePoints.some(
          (kp) => kp.id === progress.current_kp_id || kp.status === 'current' || kp.status === 'in_progress'
        );

        return {
          id: chapter.id,
          name: chapter.name,
          description: chapter.description,
          sortOrder: chapter.sort_order ?? 0,
          total: knowledgePoints.length,
          mastered,
          skipped: knowledgePoints.filter((kp) => kp.status === 'skipped').length,
          locked: knowledgePoints.filter((kp) => kp.status === 'locked').length,
          percent: knowledgePoints.length ? Math.round((mastered / knowledgePoints.length) * 100) : 0,
          hasCurrent,
          knowledgePoints,
          levelDescriptions: chapter.level_descriptions || course.level_descriptions || {},
        };
      });

    const extraChapterViews = Array.from(grouped.entries())
      .filter(([chapterId]) => !chapterMap.has(chapterId))
      .map(([chapterId, kps]) => {
        const knowledgePoints = sortedKps(kps);
        const mastered = knowledgePoints.filter((kp) => kp.status === 'completed').length;
        const hasCurrent = knowledgePoints.some(
          (kp) => kp.id === progress.current_kp_id || kp.status === 'current' || kp.status === 'in_progress'
        );

        return {
          id: chapterId,
          name: chapterId === UNASSIGNED_CHAPTER_ID ? '未分章' : '未知章节',
          description: chapterId === UNASSIGNED_CHAPTER_ID ? '历史知识点暂未绑定章节' : undefined,
          sortOrder: Number.MAX_SAFE_INTEGER,
          total: knowledgePoints.length,
          mastered,
          skipped: knowledgePoints.filter((kp) => kp.status === 'skipped').length,
          locked: knowledgePoints.filter((kp) => kp.status === 'locked').length,
          percent: knowledgePoints.length ? Math.round((mastered / knowledgePoints.length) * 100) : 0,
          hasCurrent,
          knowledgePoints,
          levelDescriptions: course.level_descriptions || {},
        };
      });

    return [...knownChapterViews, ...extraChapterViews].filter((chapter) => chapter.total > 0);
  }, [course, progress]);

  const selectedChapter = useMemo(
    () => chapterViews.find((chapter) => chapter.id === selectedChapterId) || null,
    [chapterViews, selectedChapterId]
  );

  const displayedChapterViews = selectedChapter ? [selectedChapter] : chapterViews;

  const currentPathChapterName = selectedChapter?.name || '全部章节';

  useEffect(() => {
    if (selectedChapterId !== ALL_CHAPTER_ID && !chapterViews.some((chapter) => chapter.id === selectedChapterId)) {
      setSelectedChapterId(ALL_CHAPTER_ID);
    }
  }, [chapterViews, selectedChapterId]);

  const handleSelectModule = (kp: KnowledgePointProgress) => {
    navigate(`/learn?kp_id=${kp.id}&kp_name=${encodeURIComponent(kp.name)}`);
  };

  const findContinueTarget = (knowledgePoints: KnowledgePointProgress[]) => {
    const current = knowledgePoints.find(
      (kp) => kp.id === progress?.current_kp_id || kp.status === 'current' || kp.status === 'in_progress'
    );
    if (current) return current;

    const next = knowledgePoints.find(
      (kp) => kp.status !== 'completed' && kp.status !== 'skipped' && kp.status !== 'locked'
    );
    if (next) return next;

    return knowledgePoints.find((kp) => kp.status !== 'locked') || null;
  };

  const handleContinueLearning = () => {
    const scopedTarget = selectedChapter ? findContinueTarget(selectedChapter.knowledgePoints) : null;
    const globalTarget = findContinueTarget(progress?.knowledge_points || []);
    const target = scopedTarget || globalTarget;

    if (!target) {
      navigate('/learn');
      return;
    }

    navigate(`/learn?kp_id=${target.id}&kp_name=${encodeURIComponent(target.name)}`);
  };

  // 格式化时间（分钟）
  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${Math.round(minutes)} 分钟`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours} 小时 ${mins} 分钟`;
  };

  if (loading) {
    return (
      <div className="learning-center">
        <div className="center-container">
          <div className="loading">加载中...</div>
        </div>
      </div>
    );
  }

  if (!progress || !course) {
    return (
      <div className="learning-center">
        <div className="center-container">
          <div className="error">
            <div>{error || '加载失败，请重试'}</div>
            <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
              <div>课程数据: {course ? '✓ 已加载' : '✗ 未加载'}</div>
              <div>进度数据: {progress ? '✓ 已加载' : '✗ 未加载'}</div>
              <div style={{ marginTop: '10px' }}>
                <button onClick={() => window.location.reload()} style={{
                  padding: '8px 16px',
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}>
                  重新加载
                </button>
                <button onClick={() => {
                  localStorage.clear();
                  window.location.href = '/login';
                }} style={{
                  padding: '8px 16px',
                  background: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}>
                  清除数据并重新登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="learning-center">
      <div className="center-container">
        {/* 头部 */}
        <div className="center-header course-console-header">
          <div>
            <button type="button" className="space-back-btn" onClick={onBackToSpace}>
              学习空间
            </button>
            <h1>{course.name}</h1>
            <div className="learning-path" aria-label="当前学习路径">
              <span className="path-segment">{course.subject}</span>
              <span className="path-segment">{course.grade}</span>
              <span className="path-segment current">{currentPathChapterName}</span>
            </div>
            <p>
              已学习 {formatTime(progress?.total_time || 0)} · 
              预计剩余 {formatTime(((progress?.total_count || 0) - (progress?.mastered_count || 0)) * 10)}
            </p>
          </div>
          <div className="course-orbit" aria-hidden="true">
            <div
              className="orbit-ring"
              style={{ '--course-progress': `${Math.round((progress?.mastery_rate || 0) * 100)}%` } as React.CSSProperties}
            >
              <span>{Math.round((progress?.mastery_rate || 0) * 100)}%</span>
            </div>
          </div>
        </div>

        {/* 整体进度卡片 */}
        <div className="overview-card">
          <div className="overview-stats">
            <div className="stat-item">
              <div className="stat-number">{Math.round((progress?.mastery_rate || 0) * 100)}%</div>
              <div className="stat-label">已完成</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{progress?.mastered_count || 0}/{progress?.total_count || 0}</div>
              <div className="stat-label">知识点掌握</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">🏅 {earnedBadgeCount}</div>
              <div className="stat-label">获得徽章</div>
            </div>
          </div>
          <div className="progress-bar-overall">
            <div 
              className="progress-fill-overall"
              style={{ width: `${(progress?.mastery_rate || 0) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* 章节概览 */}
        <div className="chapter-overview">
          <button
            type="button"
            className={`chapter-card ${selectedChapterId === ALL_CHAPTER_ID ? 'active' : ''}`}
            onClick={() => setSelectedChapterId(ALL_CHAPTER_ID)}
          >
            <div className="chapter-card-header">
              <div>
                <div className="chapter-title">全部章节</div>
                <div className="chapter-meta">{progress.mastered_count}/{progress.total_count} 已掌握</div>
              </div>
              <span className="chapter-action">查看全部</span>
            </div>
            <div className="chapter-progress-bar" aria-hidden="true">
              <div
                className="chapter-progress-fill"
                style={{ width: `${Math.round((progress.mastery_rate || 0) * 100)}%` }}
              />
            </div>
          </button>

          {chapterViews.map((chapter) => (
            <button
              key={chapter.id}
              type="button"
              className={`chapter-card ${selectedChapterId === chapter.id ? 'active' : ''} ${chapter.hasCurrent ? 'current' : ''}`}
              onClick={() => setSelectedChapterId(chapter.id)}
            >
              <div className="chapter-card-header">
                <div>
                  <div className="chapter-title">{chapter.name}</div>
                  <div className="chapter-meta">
                    {chapter.mastered}/{chapter.total} 已掌握
                    {chapter.hasCurrent ? <span className="chapter-current-tag">进行中</span> : null}
                  </div>
                </div>
                <span className="chapter-action">{chapter.percent}%</span>
              </div>
              <div className="chapter-progress-bar" aria-hidden="true">
                <div className="chapter-progress-fill" style={{ width: `${chapter.percent}%` }} />
              </div>
            </button>
          ))}
        </div>

        {/* 智能知识地图 */}
        <div className="knowledge-map-section">
          <div className="map-header">
            <div>
              <h2>🗺️ 知识地图</h2>
              <div className="map-subtitle">
                {selectedChapter ? `当前仅显示 ${selectedChapter.name}` : '按章节查看知识点依赖'}
              </div>
            </div>
            <div className="map-controls">
              <button 
                className={`control-btn ${!showAllLayers ? 'active' : ''}`}
                onClick={() => setShowAllLayers(false)}
              >
                只显示已解锁
              </button>
              <button 
                className={`control-btn ${showAllLayers ? 'active' : ''}`}
                onClick={() => setShowAllLayers(true)}
              >
                显示全部
              </button>
            </div>
          </div>

          <div className="map-tip">
            <span className="map-tip-icon">💡</span>
            <span>知识点按章节和层级排列，点击节点进入对应知识点学习</span>
          </div>

          <div className="chapter-map-list">
            {displayedChapterViews.map((chapter) => (
              <section key={chapter.id} className="chapter-map-panel">
                <div className="chapter-map-header">
                  <div>
                    <h3 className="chapter-map-title">{chapter.name}</h3>
                    {chapter.description ? <p className="chapter-map-desc">{chapter.description}</p> : null}
                  </div>
                  <div className="chapter-map-stats">
                    <span>{chapter.mastered}/{chapter.total} 已掌握</span>
                    <span>{chapter.percent}%</span>
                  </div>
                </div>
                <KnowledgeGraph
                  knowledgePoints={chapter.knowledgePoints}
                  onNodeClick={handleSelectModule}
                  showAllLayers={showAllLayers}
                  levelDescriptions={chapter.levelDescriptions}
                />
              </section>
            ))}
          </div>

          {/* 图例 */}
          <div className="legend">
            <div className="legend-item">
              <div className="legend-node completed"></div>
              <span>已掌握</span>
            </div>
            <div className="legend-item">
              <div className="legend-node current"></div>
              <span>进行中</span>
            </div>
            <div className="legend-item">
              <div className="legend-node locked"></div>
              <span>未解锁</span>
            </div>
            <div className="legend-item">
              <div className="legend-line completed"></div>
              <span>已完成路径</span>
            </div>
            <div className="legend-item">
              <div className="legend-line active"></div>
              <span>学习路径</span>
            </div>
          </div>
        </div>

        {/* 徽章墙 */}
        <div className="badges-section">
          <div className="section-header">
            <div className="section-title">徽章收藏</div>
            <span className="section-subtitle">{earnedBadgeCount}/{badges.length}</span>
          </div>
          <div className="badge-grid">
            {badges.map((badge) => (
              <div key={badge.id} className={`badge-item ${badge.earned ? '' : 'locked'}`}>
                <div className="badge-icon">{badge.icon}</div>
                <div className="badge-name">{badge.name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="action-buttons">
          <button className="btn btn-primary" onClick={handleContinueLearning}>
            {progress.current_kp_id || selectedChapter ? '继续学习' : '开始学习'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LearningCenter;
