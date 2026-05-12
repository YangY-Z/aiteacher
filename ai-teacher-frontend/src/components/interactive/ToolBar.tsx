import React from 'react';
import {
  EditOutlined,
  DeleteOutlined,
  MinusOutlined,
  BorderOutlined,
  FontSizeOutlined,
  DragOutlined,
  UndoOutlined,
  RedoOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import { useInteractiveStore } from './interactiveStore';
import type { DrawingTool } from './types';
import './ToolBar.css';

interface ToolBarProps {
  onUndo?: () => void;
  onRedo?: () => void;
  onClear?: () => void;
  onSubmit?: () => void;
  showSubmit?: boolean;
  isSubmitting?: boolean;
}

const tools: { id: DrawingTool; icon: React.ReactNode; label: string }[] = [
  { id: 'select', icon: <DragOutlined />, label: '选择' },
  { id: 'pen', icon: <EditOutlined />, label: '画笔' },
  { id: 'eraser', icon: <DeleteOutlined />, label: '橡皮擦' },
  { id: 'line', icon: <MinusOutlined />, label: '直线' },
  { id: 'circle', icon: <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid currentColor', borderRadius: '50%' }} />, label: '圆形' },
  { id: 'rectangle', icon: <BorderOutlined />, label: '矩形' },
  { id: 'text', icon: <FontSizeOutlined />, label: '文本' },
];

const colors = [
  '#000000',
  '#ff0000',
  '#00ff00',
  '#0000ff',
  '#ff9900',
  '#9900ff',
];

const lineWidths = [
  { value: 1, label: '细' },
  { value: 2, label: '中' },
  { value: 4, label: '粗' },
  { value: 8, label: '特粗' },
];

const ToolBar: React.FC<ToolBarProps> = ({
  onUndo,
  onRedo,
  onClear,
  onSubmit,
  showSubmit = false,
  isSubmitting = false,
}) => {
  const {
    currentTool,
    setCurrentTool,
    penColor,
    setPenColor,
    penWidth,
    setPenWidth,
  } = useInteractiveStore();

  return (
    <div className="interactive-toolbar">
      <div className="toolbar-section">
        <span className="section-label">工具</span>
        <div className="tool-buttons">
          {tools.map((tool) => (
            <button
              key={tool.id}
              className={`tool-btn ${currentTool === tool.id ? 'active' : ''}`}
              onClick={() => setCurrentTool(tool.id)}
              title={tool.label}
            >
              {tool.icon}
            </button>
          ))}
        </div>
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-section">
        <span className="section-label">颜色</span>
        <div className="color-buttons">
          {colors.map((color) => (
            <button
              key={color}
              className={`color-btn ${penColor === color ? 'active' : ''}`}
              style={{ backgroundColor: color }}
              onClick={() => setPenColor(color)}
              title={color}
            />
          ))}
        </div>
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-section">
        <span className="section-label">粗细</span>
        <div className="width-buttons">
          {lineWidths.map((lw) => (
            <button
              key={lw.value}
              className={`width-btn ${penWidth === lw.value ? 'active' : ''}`}
              onClick={() => setPenWidth(lw.value)}
              title={lw.label}
            >
              {lw.label}
            </button>
          ))}
        </div>
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-section">
        <span className="section-label">操作</span>
        <div className="action-buttons">
          <button
            className="action-btn"
            onClick={onUndo}
            title="撤销"
          >
            <UndoOutlined />
          </button>
          <button
            className="action-btn"
            onClick={onRedo}
            title="重做"
          >
            <RedoOutlined />
          </button>
          <button
            className="action-btn danger"
            onClick={onClear}
            title="清空"
          >
            <ClearOutlined />
          </button>
        </div>
      </div>

      {showSubmit && (
        <>
          <div className="toolbar-divider" />
          <div className="toolbar-section">
            <button
              className="submit-btn"
              onClick={onSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? '提交中...' : '提交给AI'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ToolBar;
