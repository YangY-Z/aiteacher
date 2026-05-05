import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Form from 'antd/es/form';
import Input from 'antd/es/input';
import Button from 'antd/es/button';
import Card from 'antd/es/card';
import message from 'antd/es/message';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { adminApi } from '../api/admin';
import './AdminLogin.css';

const AdminLogin: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values: { phone: string; password: string }) => {
    setLoading(true);
    try {
      const response = await adminApi.login(values.phone, values.password);
      
      if (response.success) {
        const { access_token, admin_id, admin_name } = response.data;
        
        // 保存 token
        localStorage.setItem('admin_token', access_token);
        
        // 保存管理员信息
        const admin = {
          id: admin_id,
          name: admin_name,
          phone: values.phone,
          role: 'admin',
        };
        localStorage.setItem('admin_user', JSON.stringify(admin));
        
        message.success(`欢迎，${admin_name}！`);
        navigate('/admin/courses');
      }
    } catch (error: any) {
      console.error('登录错误:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查账号和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page">
      <div className="admin-login-background">
        <div className="bg-shape shape1"></div>
        <div className="bg-shape shape2"></div>
      </div>
      
      <Card className="admin-login-card">
        <div className="admin-login-header">
          <div className="logo">
            <span className="logo-icon">⚙️</span>
            <span className="logo-text">课程配置系统</span>
          </div>
          <p className="admin-login-subtitle">管理员登录</p>
        </div>

        <Form
          name="admin_login"
          onFinish={handleLogin}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="phone"
            rules={[{ required: true, message: '请输入管理员账号' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="管理员账号" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="admin-login-footer">
          <p>默认账号: admin / admin@2026</p>
        </div>
      </Card>
    </div>
  );
};

export default AdminLogin;
