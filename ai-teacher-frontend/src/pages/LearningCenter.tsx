import React, { useState, useEffect, useMemo, useRef } from 'react';
import * as d3 from 'd3';
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
  initialChapterId?: string | null;
  recommendedKpId?: string | null;
  autoStart?: boolean;
  onLearningStarted?: () => void;
  onBackToSpace?: () => void;
}> = ({ 
  courseId,
  initialChapterId,
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
  const [showAllLayers, setShowAllLayers] = useState(true);
  const [selectedChapterId, setSelectedChapterId] = useState<string>('all');
  const [knowledgeMapFlashKey, setKnowledgeMapFlashKey] = useState(0);
  const [isKnowledgeMapHighlighted, setIsKnowledgeMapHighlighted] = useState(false);
  const chapterMapSvgRef = useRef<SVGSVGElement>(null);
  const chapterMapGroupRef = useRef<SVGGElement>(null);
  const chapterMapZoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const knowledgeMapSectionRef = useRef<HTMLDivElement>(null);
  const shouldFocusKnowledgeMapRef = useRef(false);

  // 默认课程ID（初一数学）
  const DEFAULT_COURSE_ID = 'COURSE_RENJIAO_7_MATH';
  const activeCourseId = courseId || DEFAULT_COURSE_ID;
  const ALL_CHAPTER_ID = 'all';
  const UNASSIGNED_CHAPTER_ID = 'unassigned';

  // 当 autoStart 为 true 时，自动跳转到学习页面
  useEffect(() => {
    if (autoStart && recommendedKpId) {
      onLearningStarted?.();
      navigate(buildLearnUrl(recommendedKpId));
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
    setSelectedChapterId(initialChapterId || ALL_CHAPTER_ID);
  }, [activeCourseId, initialChapterId]);

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
          prerequisiteChapterIds: chapter.prerequisite_chapter_ids || [],
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
          prerequisiteChapterIds: [],
          knowledgePoints,
          levelDescriptions: course.level_descriptions || {},
        };
      });

    return [...knownChapterViews, ...extraChapterViews];
  }, [course, progress]);

  const selectedChapter = useMemo(
    () => chapterViews.find((chapter) => chapter.id === selectedChapterId) || null,
    [chapterViews, selectedChapterId]
  );

  const chapterRouteColumns = useMemo(() => {
    const chapterMap = new Map(chapterViews.map((chapter) => [chapter.id, chapter]));
    const columnMap = new Map<string, number>();
    const visiting = new Set<string>();

    const resolveColumn = (chapterId: string): number => {
      if (columnMap.has(chapterId)) return columnMap.get(chapterId)!;
      if (visiting.has(chapterId)) return 0;

      visiting.add(chapterId);
      const chapter = chapterMap.get(chapterId);
      const prerequisiteIds = chapter?.prerequisiteChapterIds || [];
      const knownPrerequisites = prerequisiteIds.filter((id) => chapterMap.has(id));

      if (!chapter || knownPrerequisites.length === 0) {
        columnMap.set(chapterId, 0);
        visiting.delete(chapterId);
        return 0;
      }

      const column = Math.max(...knownPrerequisites.map(resolveColumn)) + 1;
      columnMap.set(chapterId, column);
      visiting.delete(chapterId);
      return column;
    };

    chapterViews.forEach((chapter) => resolveColumn(chapter.id));

    const grouped = new Map<number, typeof chapterViews>();
    chapterViews.forEach((chapter) => {
      const column = columnMap.get(chapter.id) || 0;
      grouped.set(column, [...(grouped.get(column) || []), chapter]);
    });

    return Array.from(grouped.entries())
      .sort(([a], [b]) => a - b)
      .map(([column, chapters]) => ({
        column,
        chapters: chapters.slice().sort((a, b) => a.sortOrder - b.sortOrder),
      }));
  }, [chapterViews]);

  const chapterMapLayout = useMemo(() => {
    const nodeWidth = 230;
    const nodeHeight = 108;
    const columnGap = 118;
    const rowGap = 34;
    const paddingX = 48;
    const paddingY = 44;
    const maxRows = Math.max(1, ...chapterRouteColumns.map((column) => column.chapters.length));
    const contentHeight = maxRows * nodeHeight + (maxRows - 1) * rowGap;
    const nodeMap = new Map<string, {
      chapter: typeof chapterViews[number];
      x: number;
      y: number;
      width: number;
      height: number;
    }>();

    chapterRouteColumns.forEach((column, columnIndex) => {
      const columnHeight = column.chapters.length * nodeHeight + Math.max(0, column.chapters.length - 1) * rowGap;
      const yOffset = paddingY + Math.max(0, (contentHeight - columnHeight) / 2);
      column.chapters.forEach((chapter, rowIndex) => {
        nodeMap.set(chapter.id, {
          chapter,
          x: paddingX + columnIndex * (nodeWidth + columnGap),
          y: yOffset + rowIndex * (nodeHeight + rowGap),
          width: nodeWidth,
          height: nodeHeight,
        });
      });
    });

    const links: Array<{
      id: string;
      from: { x: number; y: number };
      to: { x: number; y: number };
      completed: boolean;
    }> = [];

    chapterViews.forEach((chapter) => {
      const target = nodeMap.get(chapter.id);
      if (!target) return;

      chapter.prerequisiteChapterIds
        .map((id) => nodeMap.get(id))
        .filter((node): node is NonNullable<typeof node> => Boolean(node))
        .forEach((source) => {
          links.push({
            id: `${source.chapter.id}-${chapter.id}`,
            from: {
              x: source.x + source.width,
              y: source.y + source.height / 2,
            },
            to: {
              x: target.x,
              y: target.y + target.height / 2,
            },
            completed: source.chapter.percent === 100,
          });
        });
    });

    return {
      nodeWidth,
      nodeHeight,
      width: Math.max(920, paddingX * 2 + chapterRouteColumns.length * nodeWidth + Math.max(0, chapterRouteColumns.length - 1) * columnGap),
      height: Math.max(260, paddingY * 2 + contentHeight),
      nodes: Array.from(nodeMap.values()),
      links,
    };
  }, [chapterRouteColumns, chapterViews]);

  const currentPathChapterName = selectedChapter?.name || '章节地图';

  useEffect(() => {
    if (selectedChapterId !== ALL_CHAPTER_ID && !chapterViews.some((chapter) => chapter.id === selectedChapterId)) {
      setSelectedChapterId(ALL_CHAPTER_ID);
    }
  }, [chapterViews, selectedChapterId]);

  const buildLearnUrl = (kpId?: string | null, kpName?: string | null, chapterId?: string | null) => {
    const params = new URLSearchParams();
    params.set('return_to', 'course');
    params.set('course_id', activeCourseId);

    const resolvedChapterId = chapterId || selectedChapter?.id || null;
    if (resolvedChapterId) params.set('chapter_id', resolvedChapterId);
    if (kpId) params.set('kp_id', kpId);
    if (kpName) params.set('kp_name', kpName);

    return `/learn?${params.toString()}`;
  };

  const handleSelectModule = (kp: KnowledgePointProgress) => {
    navigate(buildLearnUrl(kp.id, kp.name, kp.chapter_id));
  };

  const handleSelectChapter = (chapterId: string) => {
    shouldFocusKnowledgeMapRef.current = true;
    setSelectedChapterId(chapterId);
    setKnowledgeMapFlashKey((key) => key + 1);
    setIsKnowledgeMapHighlighted(true);
  };

  useEffect(() => {
    if (!chapterMapSvgRef.current || !chapterMapGroupRef.current) return;

    const svg = d3.select(chapterMapSvgRef.current);
    const group = d3.select(chapterMapGroupRef.current);
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 2])
      .on('zoom', (event) => {
        group.attr('transform', event.transform);
      });

    chapterMapZoomRef.current = zoom;
    svg.call(zoom);

    return () => {
      svg.on('.zoom', null);
    };
  }, [chapterMapLayout.width, chapterMapLayout.height]);

  const resetChapterMapView = () => {
    if (!chapterMapSvgRef.current || !chapterMapZoomRef.current) return;
    d3.select(chapterMapSvgRef.current)
      .transition()
      .duration(180)
      .call(chapterMapZoomRef.current.transform, d3.zoomIdentity);
  };

  useEffect(() => {
    if (!selectedChapter || !shouldFocusKnowledgeMapRef.current) return;

    const frameId = window.requestAnimationFrame(() => {
      knowledgeMapSectionRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
      shouldFocusKnowledgeMapRef.current = false;
    });

    return () => window.cancelAnimationFrame(frameId);
  }, [selectedChapter, knowledgeMapFlashKey]);

  useEffect(() => {
    if (!isKnowledgeMapHighlighted) return;

    const timerId = window.setTimeout(() => {
      setIsKnowledgeMapHighlighted(false);
    }, 780);

    return () => window.clearTimeout(timerId);
  }, [isKnowledgeMapHighlighted, knowledgeMapFlashKey]);

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
      navigate(buildLearnUrl(null, null, selectedChapter?.id));
      return;
    }

    navigate(buildLearnUrl(target.id, target.name, target.chapter_id));
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

        {/* 章节地图 */}
        <div className="chapter-overview">
          <div className="chapter-overview-header">
            <div>
              <h2>章节地图</h2>
              <p>按章节前置关系安排学习顺序，点击章节查看对应知识地图</p>
            </div>
            <div className="chapter-map-actions">
              <button type="button" className="chapter-clear-btn" onClick={resetChapterMapView}>
                重置视图
              </button>
              {selectedChapter ? (
                <button type="button" className="chapter-clear-btn" onClick={() => setSelectedChapterId(ALL_CHAPTER_ID)}>
                  收起知识地图
                </button>
              ) : null}
            </div>
          </div>

          <div className="chapter-route" aria-label="章节地图">
            <svg
              ref={chapterMapSvgRef}
              className="chapter-route-svg"
              viewBox={`0 0 ${chapterMapLayout.width} ${chapterMapLayout.height}`}
              role="img"
              aria-label="章节学习顺序地图"
            >
              <defs>
                <marker id="chapter-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M 0 0 L 8 4 L 0 8 z" fill="#c7c7cc" />
                </marker>
                <marker id="chapter-arrow-completed" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M 0 0 L 8 4 L 0 8 z" fill="#69c779" />
                </marker>
              </defs>
              <g ref={chapterMapGroupRef}>
                {chapterMapLayout.links.map((link) => {
                  const midX = (link.from.x + link.to.x) / 2;
                  return (
                    <path
                      key={link.id}
                      className={`chapter-svg-link ${link.completed ? 'completed' : ''}`}
                      d={`M ${link.from.x} ${link.from.y} C ${midX} ${link.from.y}, ${midX} ${link.to.y}, ${link.to.x} ${link.to.y}`}
                      markerEnd={`url(#${link.completed ? 'chapter-arrow-completed' : 'chapter-arrow'})`}
                    />
                  );
                })}

                {chapterMapLayout.nodes.map(({ chapter, x, y, width, height }) => {
                  const isActive = selectedChapterId === chapter.id;
                  const isCompleted = chapter.percent === 100;
                  const title = chapter.name.length > 10 ? `${chapter.name.slice(0, 10)}...` : chapter.name;
                  return (
                    <g
                      key={chapter.id}
                      className={`chapter-svg-node ${isActive ? 'active' : ''} ${chapter.hasCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`}
                      role="button"
                      tabIndex={0}
                      transform={`translate(${x}, ${y})`}
                      onClick={() => handleSelectChapter(chapter.id)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          handleSelectChapter(chapter.id);
                        }
                      }}
                    >
                      <rect width={width} height={height} rx="12" />
                      <text className="chapter-svg-title" x="18" y="30">{title}</text>
                      <text className="chapter-svg-percent" x={width - 18} y="30" textAnchor="end">{chapter.percent}%</text>
                      <text className="chapter-svg-meta" x="18" y="55">
                        {chapter.mastered}/{chapter.total} 已掌握
                      </text>
                      {chapter.hasCurrent ? (
                        <g className="chapter-svg-current" transform="translate(18, 64)">
                          <rect width="54" height="18" rx="8" />
                          <text x="27" y="13" textAnchor="middle">进行中</text>
                        </g>
                      ) : null}
                      <rect className="chapter-svg-progress-bg" x="18" y={height - 18} width={width - 36} height="5" rx="3" />
                      <rect className="chapter-svg-progress-fill" x="18" y={height - 18} width={(width - 36) * (chapter.percent / 100)} height="5" rx="3" />
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>
        </div>

        {/* 智能知识地图 */}
        {selectedChapter ? (
        <div
          key={`${selectedChapter.id}-${knowledgeMapFlashKey}`}
          ref={knowledgeMapSectionRef}
          className={`knowledge-map-section ${isKnowledgeMapHighlighted ? 'knowledge-map-section-updated' : ''}`}
        >
          <div className="map-header">
            <div>
              <h2>🗺️ 知识地图</h2>
              <div className="map-subtitle">
                当前章节：{selectedChapter.name}
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
              <section key={selectedChapter.id} className="chapter-map-panel">
                <div className="chapter-map-header">
                  <div>
                    <h3 className="chapter-map-title">{selectedChapter.name}</h3>
                    {selectedChapter.description ? <p className="chapter-map-desc">{selectedChapter.description}</p> : null}
                  </div>
                  <div className="chapter-map-stats">
                    <span>{selectedChapter.mastered}/{selectedChapter.total} 已掌握</span>
                    <span>{selectedChapter.percent}%</span>
                  </div>
                </div>
                {selectedChapter.knowledgePoints.length > 0 ? (
                  <KnowledgeGraph
                    knowledgePoints={selectedChapter.knowledgePoints}
                    onNodeClick={handleSelectModule}
                    showAllLayers={showAllLayers}
                    levelDescriptions={selectedChapter.levelDescriptions}
                  />
                ) : (
                  <div className="chapter-map-empty">管理员还没有为本章配置知识点</div>
                )}
              </section>
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
        ) : null}

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
