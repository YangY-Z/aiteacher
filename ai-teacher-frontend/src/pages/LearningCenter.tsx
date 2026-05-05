import React, { useState, useEffect } from 'react';
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
  recommendedKpId?: string | null;
  autoStart?: boolean;
  onLearningStarted?: () => void;
}> = ({ 
  recommendedKpId, 
  autoStart, 
  onLearningStarted 
}) => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllLayers, setShowAllLayers] = useState(false);

  // 默认课程ID（一次函数）
  const DEFAULT_COURSE_ID = 'MATH_JUNIOR_01';

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
        console.log('正在获取课程信息...', DEFAULT_COURSE_ID);
        const courseRes = await courseApi.getById(DEFAULT_COURSE_ID);
        console.log('课程响应:', courseRes);

        if (courseRes.data.success) {
          setCourse(courseRes.data.data);
        } else {
          console.error('获取课程失败:', courseRes);
          setError(`获取课程失败: ${courseRes.data.message || '未知错误'}`);
          return;
        }

        // 获取学习进度
        console.log('正在获取学习进度...', DEFAULT_COURSE_ID);
        const progressRes = await learningApi.getProgress(DEFAULT_COURSE_ID);
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
  }, []);

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

  const handleSelectModule = (kp: KnowledgePointProgress) => {
    navigate(`/learn?kp_id=${kp.id}&kp_name=${encodeURIComponent(kp.name)}`);
  };

  const handleContinueLearning = () => {
    if (progress?.current_kp_id) {
      const kpName = progress.current_kp_name || '';
      navigate(`/learn?kp_id=${progress.current_kp_id}&kp_name=${encodeURIComponent(kpName)}`);
    } else {
      navigate('/learn');
    }
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
        <div className="center-header">
          <h1>陪伴学习</h1>
          <p>
            {course?.name || '加载中'} · 
            已学习 {formatTime(progress?.total_time || 0)} · 
            预计剩余 {formatTime(((progress?.total_count || 0) - (progress?.mastered_count || 0)) * 10)}
          </p>
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

        {/* 智能知识地图 */}
        <div className="knowledge-map-section">
          <div className="map-header">
            <h2>🗺️ 知识地图</h2>
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
            <span>知识点按层级分层排列，点击节点查看依赖关系，可缩放查看</span>
          </div>

          <KnowledgeGraph 
            knowledgePoints={progress?.knowledge_points || []}
            onNodeClick={handleSelectModule}
            showAllLayers={showAllLayers}
            levelDescriptions={course?.level_descriptions || {}}
          />

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
            {progress.current_kp_id ? '继续学习' : '开始学习'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LearningCenter;
