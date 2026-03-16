import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Avatar, Progress, Dropdown } from 'antd';
import { UserOutlined, LogoutOutlined, BookOutlined } from '@ant-design/icons';
import { useAuthStore, useLearningStore, useCourseStore } from '../../store';
import './Header.css';

const { Header: AntHeader } = Layout;

const AppHeader: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { progress } = useLearningStore();
  const { currentCourse } = useCourseStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const masteryRate = progress ? Math.round(progress.mastery_rate * 100) : 0;

  return (
    <AntHeader className="app-header">
      <div className="header-left">
        <div className="logo" onClick={() => navigate('/')}>
          <span className="logo-icon">📚</span>
          <span className="logo-text">AI虚拟教师</span>
        </div>
      </div>

      <div className="header-center">
        {currentCourse && (
          <div className="course-info">
            <BookOutlined />
            <span className="course-name">{currentCourse.name}</span>
          </div>
        )}
      </div>

      <div className="header-right">
        {progress && (
          <div className="progress-info">
            <span className="progress-label">学习进度</span>
            <Progress 
              percent={masteryRate} 
              size="small" 
              style={{ width: 120 }}
              strokeColor="#4A90D9"
            />
          </div>
        )}
        
        <Dropdown menu={{ items: menuItems }} placement="bottomRight">
          <div className="user-info">
            <Avatar 
              icon={<UserOutlined />} 
              src={user?.avatar_url}
              style={{ backgroundColor: '#4A90D9' }}
            />
            <span className="user-name hide-mobile">{user?.name || '学生'}</span>
          </div>
        </Dropdown>
      </div>
    </AntHeader>
  );
};

export default AppHeader;
