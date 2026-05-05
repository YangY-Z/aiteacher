import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ConfigProvider from 'antd/es/config-provider';
import zhCN from 'antd/locale/zh_CN';
import Login from './pages/Login';
import MinimalLearning from './pages/MinimalLearning';
import LearningMain from './pages/LearningMain';
import AdminLogin from './pages/AdminLogin';
import AdminCourses from './pages/AdminCourses';
import AdminKnowledgePoints from './pages/AdminKnowledgePoints';
import { useAuthStore } from './store';
import './styles/globals.css';

// 私有路由组件 - 需要登录才能访问
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = useAuthStore((state) => state.token);
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// 管理员路由守卫
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const adminToken = localStorage.getItem('admin_token');
  
  if (!adminToken) {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#007aff',
          colorSuccess: '#34c759',
          colorError: '#ff3b30',
          borderRadius: 12,
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* 登录页面 */}
          <Route path="/login" element={<Login />} />
          
          {/* 学习页面 - 需要登录 */}
          <Route
            path="/learn"
            element={
              <PrivateRoute>
                <MinimalLearning />
              </PrivateRoute>
            }
          />
          
          {/* 学习中心 - 包含陪伴学习和专项突破两个Tab */}
          <Route
            path="/center"
            element={
              <PrivateRoute>
                <LearningMain />
              </PrivateRoute>
            }
          />
          
          {/* 管理员路由 */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route
            path="/admin/courses"
            element={
              <AdminRoute>
                <AdminCourses />
              </AdminRoute>
            }
          />
          <Route
            path="/admin/knowledge-points/:chapterId"
            element={
              <AdminRoute>
                <AdminKnowledgePoints />
              </AdminRoute>
            }
          />
          
          {/* 默认重定向到学习中心 */}
          <Route path="/" element={<Navigate to="/center" replace />} />
          
          {/* 兼容旧路由 */}
          <Route path="/progress" element={<Navigate to="/center" replace />} />
          <Route path="/map" element={<Navigate to="/center" replace />} />
          
          {/* 其他路径重定向到学习中心 */}
          <Route path="*" element={<Navigate to="/center" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
