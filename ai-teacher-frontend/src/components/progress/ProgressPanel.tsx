import React from 'react';
import { Progress, Button, Divider } from 'antd';
import { FastForwardOutlined, ReloadOutlined, PauseCircleOutlined } from '@ant-design/icons';
import { useLearningStore } from '../../store';
import './ProgressPanel.css';

interface ProgressPanelProps {
  onSkip: () => void;
  onReview: () => void;
  onPause: () => void;
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({ onSkip, onReview, onPause }) => {
  const { progress, currentKp } = useLearningStore();

  const masteryRate = progress ? Math.round(progress.mastery_rate * 100) : 0;
  const currentTime = progress?.total_time || 0;
  const minutes = Math.floor(currentTime / 60);

  return (
    <div className="progress-panel">
      <div className="panel-section">
        <div className="section-title">
          <span className="title-icon">📍</span>
          当前知识点
        </div>
        <div className="current-kp">
          {currentKp ? (
            <>
              <div className="kp-id">{currentKp.id}</div>
              <div className="kp-name">{currentKp.name}</div>
            </>
          ) : (
            <div className="kp-placeholder">等待开始学习</div>
          )}
        </div>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      <div className="panel-section">
        <div className="section-title">
          <span className="title-icon">📊</span>
          学习进度
        </div>
        <div className="progress-stats">
          <Progress 
            percent={masteryRate} 
            strokeColor={{ '0%': '#4A90D9', '100%': '#67C23A' }}
            trailColor="#E4E7ED"
          />
          <div className="progress-text">
            {progress?.mastered_count || 0} / {progress?.total_count || 32} 知识点
          </div>
        </div>
      </div>

      <div className="panel-section">
        <div className="section-title">
          <span className="title-icon">🕐</span>
          今日学习
        </div>
        <div className="time-stat">{minutes} 分钟</div>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      <div className="panel-section">
        <div className="section-title">
          <span className="title-icon">🎯</span>
          操作
        </div>
        <div className="action-buttons">
          <Button 
            block 
            icon={<FastForwardOutlined />}
            onClick={onSkip}
            className="action-btn skip-btn"
          >
            跳过此知识点
          </Button>
          <Button 
            block 
            icon={<ReloadOutlined />}
            onClick={onReview}
            className="action-btn review-btn"
          >
            我要复习
          </Button>
          <Button 
            block 
            icon={<PauseCircleOutlined />}
            onClick={onPause}
            className="action-btn pause-btn"
          >
            暂停学习
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProgressPanel;
