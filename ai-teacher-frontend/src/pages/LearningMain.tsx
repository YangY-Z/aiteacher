import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import LearningCenter from './LearningCenter';
import Improvement from './Improvement';
import XiaoAiTeacher from './XiaoAiTeacher';
import './LearningMain.css';

type TabType = 'xiaoai' | 'learning' | 'improvement';

const LearningMain: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('xiaoai');
  const [recommendedKpId, setRecommendedKpId] = useState<string | null>(null);
  const [shouldStartLearning, setShouldStartLearning] = useState(false);

  // 从小艾老师跳转到陪伴学习
  const handleStartLearning = useCallback((topic: string, kpId?: string) => {
    setRecommendedKpId(kpId || null);
    setShouldStartLearning(true);
    setActiveTab('learning');
  }, []);

  // 处理Tab切换
  const handleTabChange = useCallback((tab: TabType) => {
    if (tab !== 'learning') {
      // 离开陪伴学习页面时重置状态
      setShouldStartLearning(false);
      setRecommendedKpId(null);
    }
    setActiveTab(tab);
  }, []);

  // 陪伴学习开始后重置状态
  const handleLearningStarted = useCallback(() => {
    setShouldStartLearning(false);
    setRecommendedKpId(null);
  }, []);

  return (
    <div className="learning-main">
      {/* 顶部Tab切换 */}
      <div className="main-tabs">
        <button
          className={`main-tab-btn ${activeTab === 'xiaoai' ? 'active' : ''}`}
          onClick={() => handleTabChange('xiaoai')}
        >
          <span className="tab-icon">🤖</span>
          <span className="tab-label">小艾老师</span>
        </button>
        <button
          className={`main-tab-btn ${activeTab === 'learning' ? 'active' : ''}`}
          onClick={() => handleTabChange('learning')}
        >
          <span className="tab-icon">📚</span>
          <span className="tab-label">陪伴学习</span>
        </button>
        <button
          className={`main-tab-btn ${activeTab === 'improvement' ? 'active' : ''}`}
          onClick={() => handleTabChange('improvement')}
        >
          <span className="tab-icon">🎯</span>
          <span className="tab-label">专项突破</span>
        </button>
      </div>

      {/* 内容区域 */}
      <div className="main-content">
        {activeTab === 'xiaoai' && <XiaoAiTeacher onStartLearning={handleStartLearning} />}
        {activeTab === 'learning' && (
          <LearningCenter 
            recommendedKpId={recommendedKpId}
            autoStart={shouldStartLearning}
            onLearningStarted={handleLearningStarted}
          />
        )}
        {activeTab === 'improvement' && <Improvement />}
      </div>
    </div>
  );
};

export default LearningMain;
