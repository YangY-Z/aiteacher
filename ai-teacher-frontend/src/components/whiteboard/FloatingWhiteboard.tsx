import React, { useEffect, useState, useRef } from 'react';
import { Button, Tooltip } from 'antd';
import { ExpandOutlined, CompressOutlined, CloseOutlined, DownloadOutlined } from '@ant-design/icons';
import Whiteboard from './Whiteboard';
import { useLearningStore } from '../../store';
import html2canvas from 'html2canvas';
import './FloatingWhiteboard.css';

interface FloatingWhiteboardProps {
  loading?: boolean;
}

const FloatingWhiteboard: React.FC<FloatingWhiteboardProps> = ({ loading = false }) => {
  const { 
    whiteboardMode, 
    setWhiteboardMode, 
    whiteboardBlocks,
    currentWhiteboard,
    clearWhiteboard 
  } = useLearningStore();

  // 拖动状态
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0, posX: 0, posY: 0 });
  const whiteboardRef = useRef<HTMLDivElement>(null);
  
  // 跟踪前一个模式，用于区分首次显示和收缩动画
  const prevModeRef = useRef(whiteboardMode);

  // 检测白板是否有内容
  const hasContent = whiteboardBlocks.length > 0 || 
    currentWhiteboard.title || 
    currentWhiteboard.key_points.length > 0 ||
    currentWhiteboard.formulas.length > 0 ||
    currentWhiteboard.examples.length > 0 ||
    currentWhiteboard.notes.length > 0;

  // 自动显示/隐藏白板 - 只显示mini状态
  useEffect(() => {
    if (hasContent && whiteboardMode === 'hidden') {
      setWhiteboardMode('mini');
    } else if (!hasContent && whiteboardMode !== 'hidden') {
      setWhiteboardMode('hidden');
    }
  }, [hasContent, whiteboardMode, setWhiteboardMode]);

  // 重置位置当模式改变
  useEffect(() => {
    if (whiteboardMode === 'expanded') {
      setPosition({ x: 0, y: 0 });
    }
  }, [whiteboardMode]);

  // 跟踪前一个模式，用于区分首次显示和收缩动画
  const [isShrinking, setIsShrinking] = useState(false);
  useEffect(() => {
    // 当从 expanded 变成 mini 时，设置 shrinking 为 true
    if (whiteboardMode === 'mini' && prevModeRef.current === 'expanded') {
      setIsShrinking(true);
    } else if (whiteboardMode !== 'mini') {
      setIsShrinking(false);
    }
    prevModeRef.current = whiteboardMode;
  }, [whiteboardMode]);

  // 拖动开始
  const handleMouseDown = (e: React.MouseEvent) => {
    if (whiteboardMode !== 'expanded') return;
    
    e.preventDefault();
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      posX: position.x,
      posY: position.y,
    };
  };

  // 拖动中
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      setPosition({
        x: dragStartRef.current.posX + dx,
        y: dragStartRef.current.posY + dy,
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // ESC 键关闭白板
  useEffect(() => {
    if (whiteboardMode !== 'expanded') return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setWhiteboardMode('mini');
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [whiteboardMode, setWhiteboardMode]);

  // 如果没有内容，不渲染
  if (whiteboardMode === 'hidden') {
    return null;
  }

  // 下载白板
  const handleDownload = async () => {
    const contentEl = whiteboardRef.current?.querySelector('.whiteboard-canvas') as HTMLElement;
    if (!contentEl) return;
    
    try {
      const canvas = await html2canvas(contentEl, {
        backgroundColor: '#ffffff',
        scale: 2,
      });
      
      const link = document.createElement('a');
      link.download = `知识要点_${new Date().toLocaleDateString()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // 处理清空白板
  const handleClear = () => {
    clearWhiteboard();
  };

  // 点击迷你白板展开
  const handleMiniClick = () => {
    if (whiteboardMode === 'mini') {
      setWhiteboardMode('expanded');
    }
  };

  // 展开态
  if (whiteboardMode === 'expanded') {
    return (
      <>
        {/* 透明遮罩层，点击收起白板 */}
        <div 
          className="whiteboard-overlay"
          onClick={() => setWhiteboardMode('mini')}
        />
        <div 
          ref={whiteboardRef}
          className="floating-whiteboard expanded"
          style={{
            transform: `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px))`,
          }}
        >
        <div 
          className="floating-whiteboard-header"
          onMouseDown={handleMouseDown}
        >
          <div className="header-title">
            <span className="title-icon">📝</span>
            <span>知识要点</span>
          </div>
        </div>
        <div className="floating-whiteboard-content">
          <Whiteboard loading={loading} />
        </div>
      </div>
      </>
    );
  }

  // 迷你态
  return (
    <div 
      className={`floating-whiteboard mini ${isShrinking ? 'shrinking' : 'initial'}`} 
      onClick={handleMiniClick}
    >
      <div className="mini-header">
        <span className="mini-title">📝 知识要点</span>
        <Tooltip title="点击放大">
          <Button 
            type="text" 
            icon={<ExpandOutlined />} 
            className="mini-expand-btn"
            onClick={(e) => {
              e.stopPropagation();
              setWhiteboardMode('expanded');
            }}
          />
        </Tooltip>
      </div>
      <div className="mini-preview">
        <Whiteboard loading={loading} />
      </div>
    </div>
  );
};

export default FloatingWhiteboard;