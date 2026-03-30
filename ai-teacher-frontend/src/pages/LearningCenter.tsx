import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store';
import './LearningCenter.css';

interface Module {
  id: number;
  name: string;
  desc: string;
  progress: number;
  status: 'completed' | 'current' | 'locked';
  icon: string;
  time: string;
}

interface Badge {
  id: number;
  name: string;
  icon: string;
  earned: boolean;
}

interface KnowledgeNode {
  id: string;
  name: string;
  status: 'completed' | 'current' | 'locked';
  progress?: number;
  x: number;
  y: number;
  size: number;
}

interface KnowledgeLink {
  from: string;
  to: string;
}

interface LearningCenterProps {
  recommendedKpId?: string | null;
  autoStart?: boolean;
  onLearningStarted?: () => void;
}

const modules: Module[] = [
  { id: 1, name: '函数概念', desc: '理解变量、函数定义、表示法', progress: 100, status: 'completed', icon: '📘', time: '10 分钟' },
  { id: 2, name: '一次函数定义', desc: '学习标准形式 y=kx+b，理解斜率和截距', progress: 20, status: 'current', icon: '📗', time: '2/10 分钟' },
  { id: 3, name: '画图像', desc: '掌握描点法、两点法画图', progress: 0, status: 'locked', icon: '📈', time: '预计 12 分钟' },
  { id: 4, name: '斜率深入', desc: '理解斜率正负、大小、平行关系', progress: 0, status: 'locked', icon: '📐', time: '预计 10 分钟' },
  { id: 5, name: '截距应用', desc: '掌握 y 截距、x 截距的计算和应用', progress: 0, status: 'locked', icon: '📊', time: '预计 8 分钟' },
  { id: 6, name: '解析式求解', desc: '根据条件求一次函数解析式', progress: 0, status: 'locked', icon: '✏️', time: '预计 10 分钟' },
  { id: 7, name: '性质总结', desc: '单调性、奇偶性、图像特征', progress: 0, status: 'locked', icon: '📝', time: '预计 8 分钟' },
  { id: 8, name: '实际应用', desc: '行程问题、成本问题等应用', progress: 0, status: 'locked', icon: '🌍', time: '预计 15 分钟' },
  { id: 9, name: '综合练习', desc: '混合题型综合训练', progress: 0, status: 'locked', icon: '📋', time: '预计 15 分钟' },
  { id: 10, name: '单元测试', desc: '本单元综合测试', progress: 0, status: 'locked', icon: '✅', time: '预计 10 分钟' },
];

const badges: Badge[] = [
  { id: 1, name: '快速学习者', icon: '🏅', earned: true },
  { id: 2, name: '首次满分', icon: '💯', earned: true },
  { id: 3, name: '连续学习', icon: '🔥', earned: true },
  { id: 4, name: '完美通关', icon: '👑', earned: false },
  { id: 5, name: '坚持不懈', icon: '💪', earned: false },
  { id: 6, name: '数学天才', icon: '🧠', earned: false },
];

const nodes: KnowledgeNode[] = [
  { id: 'coord', name: '坐标系', status: 'completed', x: 500, y: 80, size: 35 },
  { id: 'var', name: '变量概念', status: 'completed', x: 300, y: 180, size: 35 },
  { id: 'func', name: '函数定义', status: 'completed', x: 500, y: 180, size: 35 },
  { id: 'graph', name: '图像基础', status: 'completed', x: 700, y: 180, size: 35 },
  { id: 'prep', name: '前置汇总', status: 'completed', x: 400, y: 280, size: 35 },
  { id: 'linear', name: '一次函数', status: 'current', progress: 62, x: 500, y: 380, size: 45 },
  { id: 'prop', name: '图像性质', status: 'locked', x: 300, y: 480, size: 35 },
  { id: 'app', name: '应用问题', status: 'locked', x: 500, y: 480, size: 35 },
  { id: 'practice', name: '综合练习', status: 'locked', x: 700, y: 480, size: 35 },
  { id: 'final', name: '通关', status: 'locked', x: 500, y: 560, size: 40 },
];

const links: KnowledgeLink[] = [
  { from: 'coord', to: 'var' },
  { from: 'coord', to: 'func' },
  { from: 'coord', to: 'graph' },
  { from: 'var', to: 'prep' },
  { from: 'func', to: 'prep' },
  { from: 'graph', to: 'prep' },
  { from: 'prep', to: 'linear' },
  { from: 'linear', to: 'prop' },
  { from: 'linear', to: 'app' },
  { from: 'linear', to: 'practice' },
  { from: 'prop', to: 'final' },
  { from: 'app', to: 'final' },
  { from: 'practice', to: 'final' },
];

type TabType = 'modules' | 'map';

const LearningCenter: React.FC<LearningCenterProps> = ({ 
  recommendedKpId, 
  autoStart, 
  onLearningStarted 
}) => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>('modules');

  // 当 autoStart 为 true 时，自动跳转到学习页面
  useEffect(() => {
    if (autoStart && recommendedKpId) {
      // 通知父组件学习已开始
      onLearningStarted?.();
      // 跳转到学习页面
      navigate(`/learn?kp_id=${recommendedKpId}`);
    }
  }, [autoStart, recommendedKpId, onLearningStarted, navigate]);

  const completedCount = modules.filter(m => m.status === 'completed').length;
  const earnedBadgeCount = badges.filter(b => b.earned).length;

  const handleSelectModule = (module: Module) => {
    if (module.status === 'locked') {
      alert('请先完成前置模块');
    } else {
      navigate('/learn');
    }
  };

  const handleContinueLearning = () => {
    navigate('/learn');
  };

  const getNodeById = (id: string) => nodes.find(n => n.id === id);

  const getLinkStatus = (link: KnowledgeLink) => {
    const fromNode = getNodeById(link.from);
    const toNode = getNodeById(link.to);
    if (fromNode?.status === 'completed' && toNode?.status === 'completed') {
      return 'completed';
    }
    if (fromNode?.status === 'completed' || fromNode?.status === 'current') {
      return 'active';
    }
    return '';
  };

  return (
    <div className="learning-center">
      <div className="center-container">
        {/* 头部 */}
        <div className="center-header">
          <h1>陪伴学习</h1>
          <p>一次函数 · 已学习 12 分钟 · 预计剩余 86 分钟</p>
        </div>

        {/* 整体进度卡片 */}
        <div className="overview-card">
          <div className="overview-stats">
            <div className="stat-item">
              <div className="stat-number">12%</div>
              <div className="stat-label">已完成</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{completedCount}/10</div>
              <div className="stat-label">模块完成</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">🏅 {earnedBadgeCount}</div>
              <div className="stat-label">获得徽章</div>
            </div>
          </div>
        </div>

        {/* Tab 切换 */}
        <div className="tab-switcher">
          <button
            className={`tab-btn ${activeTab === 'modules' ? 'active' : ''}`}
            onClick={() => setActiveTab('modules')}
          >
            模块列表
          </button>
          <button
            className={`tab-btn ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            知识地图
          </button>
        </div>

        {/* 模块列表视图 */}
        {activeTab === 'modules' && (
          <div className="modules-section">
            <div className="modules-grid">
              {modules.map((module) => (
                <div
                  key={module.id}
                  className={`module-card ${module.status}`}
                  onClick={() => handleSelectModule(module)}
                >
                  <div className="module-header">
                    <div className={`module-icon ${module.status}`}>{module.icon}</div>
                    <div className="module-name">{module.name}</div>
                    <span className={`module-status ${module.status}`}>
                      {module.status === 'completed' ? '已完成' : module.status === 'current' ? '进行中' : '未开始'}
                    </span>
                  </div>
                  <div className="module-desc">{module.desc}</div>
                  <div className="module-progress-bar">
                    <div
                      className="module-progress-fill"
                      style={{ width: `${module.progress}%` }}
                    />
                  </div>
                  <div className="module-stats">
                    <span>{module.progress}%</span>
                    <span>{module.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 知识地图视图 */}
        {activeTab === 'map' && (
          <div className="map-section">
            <div className="map-container">
              <svg className="knowledge-map-svg" viewBox="0 0 1000 620">
                {/* 连线 */}
                {links.map((link, index) => {
                  const from = getNodeById(link.from);
                  const to = getNodeById(link.to);
                  if (!from || !to) return null;
                  
                  return (
                    <line
                      key={index}
                      className={`link-line ${getLinkStatus(link)}`}
                      x1={from.x}
                      y1={from.y}
                      x2={to.x}
                      y2={to.y}
                    />
                  );
                })}

                {/* 节点 */}
                {nodes.map((node) => (
                  <g key={node.id} className="node-group" transform={`translate(${node.x}, ${node.y})`}>
                    <circle
                      className={`node-circle ${node.status}`}
                      r={node.size}
                      style={node.id === 'final' ? { stroke: '#ffd700', strokeWidth: 3 } : undefined}
                    />
                    <text
                      className="node-text"
                      y={node.status === 'current' ? -5 : 5}
                      style={node.status === 'current' ? { fill: 'white' } : undefined}
                    >
                      {node.id === 'final' ? '🎯 ' : ''}{node.name}
                    </text>
                    {node.status === 'completed' && (
                      <text className="node-subtext" y={20}>✓ 已掌握</text>
                    )}
                    {node.status === 'current' && node.progress && (
                      <text className="node-subtext" y={20} style={{ fill: 'rgba(255,255,255,0.9)' }}>
                        {node.progress}% 掌握
                      </text>
                    )}
                    {node.status === 'locked' && (
                      <text className="node-subtext" y={20}>○ 未开始</text>
                    )}
                  </g>
                ))}
              </svg>

              {/* 图例 */}
              <div className="legend">
                <div className="legend-item">
                  <div className="legend-dot completed"></div>
                  <span>已掌握</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot current"></div>
                  <span>进行中</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot locked"></div>
                  <span>未开始</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 徽章墙 */}
        <div className="badges-section">
          <div className="section-header">
            <div className="section-title">徽章收藏</div>
            <span className="section-subtitle">{earnedBadgeCount}/6</span>
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
            继续学习
          </button>
        </div>
      </div>
    </div>
  );
};

export default LearningCenter;
