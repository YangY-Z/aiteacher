/**
 * 教学图片组件
 * 用于显示教学图片，支持加载状态和错误处理
 */

import React from 'react';
import Spin from 'antd/es/spin';
import Alert from 'antd/es/alert';
import { useTeachingImage } from '../../hooks/useTeachingImage';
import './TeachingImage.css';

interface TeachingImageProps {
  imageId: string;
  alt?: string;
  className?: string;
  style?: React.CSSProperties;
  showDescription?: boolean;
  onLoad?: () => void;
  onError?: (error: string) => void;
}

/**
 * 教学图片组件
 */
const TeachingImage: React.FC<TeachingImageProps> = ({
  imageId,
  alt = '教学图片',
  className = '',
  style,
  showDescription = false,
  onLoad,
  onError,
}) => {
  const { imageUrl, imageData, loading, error } = useTeachingImage(imageId);

  React.useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  React.useEffect(() => {
    if (imageUrl && onLoad) {
      onLoad();
    }
  }, [imageUrl, onLoad]);

  // 加载中
  if (loading) {
    return (
      <div className={`teaching-image-loading ${className}`} style={style}>
        <Spin size="large" tip="加载图片中..." />
      </div>
    );
  }

  // 错误
  if (error) {
    return (
      <div className={`teaching-image-error ${className}`} style={style}>
        <Alert 
          type="error" 
          message="图片加载失败" 
          description={error}
          showIcon
        />
      </div>
    );
  }

  // 无图片
  if (!imageUrl || !imageData) {
    return null;
  }

  // 正常显示
  return (
    <div className={`teaching-image-container ${className}`} style={style}>
      <img
        src={imageUrl}
        alt={alt}
        className="teaching-image"
        onError={(e) => {
          console.error(`Failed to load image: ${imageUrl}`);
          e.currentTarget.src = '/placeholder.png'; // 使用占位图
        }}
      />
      {showDescription && imageData.description && (
        <p className="teaching-image-description">{imageData.description}</p>
      )}
    </div>
  );
};

export default TeachingImage;
