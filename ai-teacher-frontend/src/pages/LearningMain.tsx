import React, { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import LearningCenter from './LearningCenter';
import LearningSpace from './LearningSpace';
import Improvement from './Improvement';
import XiaoAiTeacher from './XiaoAiTeacher';
import './LearningMain.css';

type TabType = 'space' | 'xiaoai' | 'learning' | 'improvement';

const DEFAULT_COURSE_ID = 'COURSE_RENJIAO_7_MATH';
const LEGACY_COURSE_ID = 'MATH_JUNIOR_01';
const LAST_COURSE_KEY = 'learning:last_course_id';
const isTabType = (tab: string | null): tab is TabType => (
  tab === 'space' || tab === 'xiaoai' || tab === 'learning' || tab === 'improvement'
);

interface OpenCourseOptions {
  chapterId?: string;
  kpId?: string;
  startLearning?: boolean;
}

const LearningMain: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<TabType>(() => {
    const tab = searchParams.get('tab');
    return isTabType(tab) ? tab : 'space';
  });
  const [selectedCourseId, setSelectedCourseId] = useState(
    () => {
      const queryCourseId = searchParams.get('course_id');
      if (queryCourseId && queryCourseId !== LEGACY_COURSE_ID) {
        localStorage.setItem(LAST_COURSE_KEY, queryCourseId);
        return queryCourseId;
      }
      const savedCourseId = localStorage.getItem(LAST_COURSE_KEY);
      if (!savedCourseId || savedCourseId === LEGACY_COURSE_ID) {
        localStorage.setItem(LAST_COURSE_KEY, DEFAULT_COURSE_ID);
        return DEFAULT_COURSE_ID;
      }
      return savedCourseId;
    }
  );
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(() => searchParams.get('chapter_id'));
  const [recommendedKpId, setRecommendedKpId] = useState<string | null>(null);
  const [shouldStartLearning, setShouldStartLearning] = useState(false);

  useEffect(() => {
    const tab = searchParams.get('tab');
    const courseId = searchParams.get('course_id');
    const chapterId = searchParams.get('chapter_id');

    if (isTabType(tab)) {
      setActiveTab(tab);
    }
    if (courseId && courseId !== LEGACY_COURSE_ID) {
      localStorage.setItem(LAST_COURSE_KEY, courseId);
      setSelectedCourseId(courseId);
    }
    setSelectedChapterId(chapterId);
  }, [searchParams]);

  // 从小艾老师跳转到陪伴学习
  const handleStartLearning = useCallback((topic: string, kpId?: string) => {
    setRecommendedKpId(kpId || null);
    setShouldStartLearning(true);
    setActiveTab('learning');
  }, []);

  const handleOpenCourse = useCallback((courseId: string, options?: OpenCourseOptions) => {
    localStorage.setItem(LAST_COURSE_KEY, courseId);
    setSelectedCourseId(courseId);
    setSelectedChapterId(options?.chapterId || null);
    setRecommendedKpId(options?.kpId || null);
    setShouldStartLearning(Boolean(options?.startLearning && options?.kpId));
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
          className={`main-tab-btn ${activeTab === 'space' ? 'active' : ''}`}
          onClick={() => handleTabChange('space')}
        >
          <span className="tab-symbol space"></span>
          <span className="tab-label">学习空间</span>
        </button>
        <button
          className={`main-tab-btn ${activeTab === 'xiaoai' ? 'active' : ''}`}
          onClick={() => handleTabChange('xiaoai')}
        >
          <span className="tab-symbol teacher"></span>
          <span className="tab-label">小艾老师</span>
        </button>
        <button
          className={`main-tab-btn ${activeTab === 'learning' ? 'active' : ''}`}
          onClick={() => handleTabChange('learning')}
        >
          <span className="tab-symbol course"></span>
          <span className="tab-label">课程控制台</span>
        </button>
        <button
          className={`main-tab-btn ${activeTab === 'improvement' ? 'active' : ''}`}
          onClick={() => handleTabChange('improvement')}
        >
          <span className="tab-symbol focus"></span>
          <span className="tab-label">专项突破</span>
        </button>
      </div>

      {/* 内容区域 */}
      <div className="main-content">
        {activeTab === 'space' && (
          <LearningSpace
            onOpenCourse={handleOpenCourse}
          />
        )}
        {activeTab === 'xiaoai' && <XiaoAiTeacher onStartLearning={handleStartLearning} />}
        {activeTab === 'learning' && (
          <LearningCenter 
            courseId={selectedCourseId}
            initialChapterId={selectedChapterId}
            recommendedKpId={recommendedKpId}
            autoStart={shouldStartLearning}
            onLearningStarted={handleLearningStarted}
            onBackToSpace={() => handleTabChange('space')}
          />
        )}
        {activeTab === 'improvement' && <Improvement />}
      </div>
    </div>
  );
};

export default LearningMain;
