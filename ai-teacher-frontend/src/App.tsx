import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MinimalLearning from './pages/MinimalLearning';
import './styles/globals.css';

/**
 * 极简版AI教师 - 单页面应用
 * 
 * 设计原则：
 * 1. 无登录 - 直接学习
 * 2. 单列布局 - 居中对话
 * 3. 三步流程 - 讲解→提问→反馈
 */
const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#5B8DEF',
          colorSuccess: '#52C41A',
          colorError: '#FF4D4F',
          borderRadius: 12,
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
      }}
    >
      <MinimalLearning />
    </ConfigProvider>
  );
};

export default App;