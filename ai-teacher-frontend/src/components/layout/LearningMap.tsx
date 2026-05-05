/**
 * 学习地图组件
 * 展示知识点解锁状态，采用解锁式设计（类似游戏关卡）
 */

import React from 'react';
import Progress from 'antd/es/progress';
import Tag from 'antd/es/tag';
import Empty from 'antd/es/empty';
import { CheckCircleOutlined, LockOutlined, PlayCircleOutlined } from '@ant-design/icons';
import './LearningMap.css';

interface KnowledgePointStatus {
  id: string;
  name: string;
  status: 'mastered' | 'current' | 'locked';
  masteryLevel?: number;
}

interface LearningMapProps {
  knowledgePoints?: KnowledgePointStatus[];
  currentKpId?: string;
  progress?: any;
  onSelectKp?: (kpId: string) => void;
}

/**
 * 学习地图组件
 * 隐藏总量，只显示解锁状态
 */
const LearningMap: React.FC<LearningMapProps> = ({
  knowledgePoints,
  currentKpId,
  progress,
  onSelectKp,
}) => {
  // 从progress生成知识点列表
  const kpList: KnowledgePointStatus[] = React.useMemo(() => {
    if (knowledgePoints) return knowledgePoints;
    
    if (progress?.knowledge_points) {
      return progress.knowledge_points.map((kp: any) => ({
        id: kp.id,
        name: kp.name,
        status: kp.status || (kp.mastery_level >= 0.8 ? 'mastered' : 'current'),
        masteryLevel: kp.mastery_level ? Math.round(kp.mastery_level * 100) : undefined,
      }));
    }
    
    return [];
  }, [knowledgePoints, progress]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'mastered':
        return <CheckCircleOutlined className="status-icon mastered" />;
      case 'current':
        return <PlayCircleOutlined className="status-icon current" />;
      case 'locked':
        return <LockOutlined className="status-icon locked" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'mastered':
        return '已掌握';
      case 'current':
        return '学习中';
      case 'locked':
        return '待解锁';
      default:
        return '';
    }
  };

  if (kpList.length === 0) {
    return (
      <Empty
        description="暂无学习数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  return (
    <div className="learning-map">
      <div className="map-header">
        <h3>学习地图</h3>
        <p className="map-subtitle">按顺序解锁知识点</p>
      </div>

      <div className="knowledge-points-list">
        {kpList.map((kp, index) => (
          <div
            key={kp.id}
            className={`kp-item ${kp.status} ${kp.id === currentKpId ? 'active' : ''}`}
            onClick={() => {
              if (kp.status !== 'locked' && onSelectKp) {
                onSelectKp(kp.id);
              }
            }}
          >
            <div className="kp-index">
              {index + 1}
            </div>
            
            <div className="kp-content">
              <div className="kp-name">{kp.name}</div>
              <div className="kp-status">
                <Tag 
                  color={
                    kp.status === 'mastered' ? 'success' :
                    kp.status === 'current' ? 'processing' : 'default'
                  }
                >
                  {getStatusIcon(kp.status)}
                  <span>{getStatusText(kp.status)}</span>
                </Tag>
              </div>
            </div>

            {kp.status === 'mastered' && kp.masteryLevel && (
              <div className="kp-mastery">
                <Progress 
                  percent={kp.masteryLevel} 
                  size="small"
                  showInfo={false}
                  strokeColor="#52c41a"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="map-footer">
        <p className="map-tip">完成当前知识点后解锁下一个</p>
      </div>
    </div>
  );
};

export default LearningMap;