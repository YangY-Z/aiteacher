/**
 * 单流布局组件
 * 基于V2设计方案：极简顶部 + 主学习区 + 底部对话区
 */

import React from 'react';
import { Button, Drawer } from 'antd';
import { MenuOutlined, BookOutlined, PauseCircleOutlined, ForwardOutlined } from '@ant-design/icons';
import './SingleStreamLayout.css';

interface SingleStreamLayoutProps {
  currentTask: string;
  children: React.ReactNode;
  onOpenLearningMap?: () => void;
  learningMapContent?: React.ReactNode;
  onPause?: () => void;
  onSkip?: () => void;
}

/**
 * 单流布局
 * - 极简顶部：只显示当前任务，不显示进度
 * - 主学习区：单一焦点
 * - 底部：AI助手 + 结构化对话
 */
const SingleStreamLayout: React.FC<SingleStreamLayoutProps> = ({
  currentTask,
  children,
  onOpenLearningMap,
  learningMapContent,
  onPause,
  onSkip,
}) => {
  const [mapVisible, setMapVisible] = React.useState(false);

  const handleOpenMap = () => {
    setMapVisible(true);
    onOpenLearningMap?.();
  };

  return (
    <div className="single-stream-layout">
      {/* 极简顶部 */}
      <header className="minimal-header">
        <div className="header-left">
          <span className="current-task">
            当前任务：{currentTask}
          </span>
        </div>
        <div className="header-right">
          {onSkip && (
            <Button
              type="text"
              icon={<ForwardOutlined />}
              onClick={onSkip}
              className="action-btn"
            >
              跳过
            </Button>
          )}
          {onPause && (
            <Button
              type="text"
              icon={<PauseCircleOutlined />}
              onClick={onPause}
              className="action-btn"
            >
              暂停
            </Button>
          )}
          <Button
            type="text"
            icon={<BookOutlined />}
            onClick={handleOpenMap}
            className="learning-map-btn"
          >
            我的学习地图
          </Button>
        </div>
      </header>

      {/* 主学习区 - 单一焦点 */}
      <main className="main-learning-area">
        {children}
      </main>

      {/* 学习地图抽屉 */}
      <Drawer
        title="学习地图"
        placement="right"
        width={360}
        open={mapVisible}
        onClose={() => setMapVisible(false)}
        className="learning-map-drawer"
      >
        {learningMapContent || (
          <div className="learning-map-placeholder">
            <p>学习地图加载中...</p>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default SingleStreamLayout;
