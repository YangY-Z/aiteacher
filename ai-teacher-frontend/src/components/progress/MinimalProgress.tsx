import React from 'react';
import './MinimalProgress.css';

interface KnowledgePoint {
  id: string;
  name: string;
  status: 'locked' | 'current' | 'completed';
}

interface MinimalProgressProps {
  currentModule: number;
  totalModules: number;
  moduleName: string;
  knowledgePoints?: KnowledgePoint[];
  showBadge?: boolean;
  badgeName?: string;
}

const MinimalProgress: React.FC<MinimalProgressProps> = ({
  currentModule,
  totalModules,
  moduleName,
  knowledgePoints = [],
  showBadge = false,
  badgeName
}) => {
  const progress = (currentModule / totalModules) * 100;
  
  // 计算环形进度
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="minimal-progress">
      {/* 顶部进度信息 */}
      <div className="progress-header">
        {/* 环形进度条 */}
        <div className="circular-progress">
          <svg width="60" height="60" viewBox="0 0 60 60">
            {/* 背景圆环 */}
            <circle
              cx="30"
              cy="30"
              r={radius}
              fill="none"
              stroke="#e5e5e7"
              strokeWidth="6"
            />
            {/* 进度圆环 */}
            <circle
              cx="30"
              cy="30"
              r={radius}
              fill="none"
              stroke="url(#gradient)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              style={{
                transition: 'stroke-dashoffset 0.5s ease',
                transform: 'rotate(-90deg)',
                transformOrigin: '50% 50%'
              }}
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#007aff" />
                <stop offset="100%" stopColor="#5856d6" />
              </linearGradient>
            </defs>
          </svg>
          <div className="progress-percentage">
            {Math.round(progress)}%
          </div>
        </div>
        
        {/* 进度文字信息 */}
        <div className="progress-info">
          <div className="module-name">{moduleName}</div>
          <div className="module-progress">
            进度 {currentModule}/{totalModules}
          </div>
          {showBadge && badgeName && (
            <div className="badge-earned">
              🏅 获得徽章：{badgeName}
            </div>
          )}
        </div>
      </div>

      {/* 知识树进度 */}
      {knowledgePoints.length > 0 && (
        <div className="knowledge-tree">
          {knowledgePoints.map((kp, index) => (
            <div
              key={kp.id}
              className={`knowledge-node ${kp.status}`}
              title={kp.name}
            >
              <div className="node-indicator">
                {kp.status === 'completed' && '✓'}
                {kp.status === 'current' && '●'}
                {kp.status === 'locked' && '○'}
              </div>
              {index < knowledgePoints.length - 1 && (
                <div className="node-connector" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MinimalProgress;
