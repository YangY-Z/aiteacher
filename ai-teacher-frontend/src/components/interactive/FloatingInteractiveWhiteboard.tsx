import React, { useState, useRef, useCallback, useEffect, forwardRef, useImperativeHandle } from 'react';
import { CompressOutlined } from '@ant-design/icons';
import DrawingCanvas from './DrawingCanvas';
import type { DrawingCanvasRef } from './DrawingCanvas';
import ToolBar from './ToolBar';
import TemplateSelector from './TemplateSelector';
import { useInteractiveStore } from './interactiveStore';
import type { AIFeedback, InteractiveTask } from './types';
import './FloatingInteractiveWhiteboard.css';

export interface FloatingInteractiveWhiteboardRef {
  exportImage: () => string;
  clearCanvas: () => void;
  setTask: (task: InteractiveTask | null) => void;
  setFeedback: (feedback: AIFeedback | null) => void;
}

interface FloatingInteractiveWhiteboardProps {
  visible?: boolean;
  onClose?: () => void;
  onSubmit?: (imageData: string) => void;
  isSubmitting?: boolean;
}

const FloatingInteractiveWhiteboard = forwardRef<FloatingInteractiveWhiteboardRef, FloatingInteractiveWhiteboardProps>(
  ({ visible = false, onClose, onSubmit, isSubmitting = false }, ref) => {
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const isDraggingRef = useRef(false);
    const dragStartRef = useRef({ x: 0, y: 0, posX: 0, posY: 0 });
    const panelRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<DrawingCanvasRef>(null);

    const {
      currentTemplate,
      setTemplate,
      aiFeedback,
      setAIFeedback,
    } = useInteractiveStore();

    const [task, setTaskState] = useState<InteractiveTask | null>(null);

    const handleDragStart = useCallback((e: React.MouseEvent) => {
      e.preventDefault();
      isDraggingRef.current = false;
      setIsDragging(true);
      dragStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        posX: position.x,
        posY: position.y,
      };
    }, [position]);

    useEffect(() => {
      if (!isDragging) return;

      const handleMouseMove = (e: MouseEvent) => {
        const dx = e.clientX - dragStartRef.current.x;
        const dy = e.clientY - dragStartRef.current.y;
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
          isDraggingRef.current = true;
        }
        const newX = dragStartRef.current.posX + dx;
        const newY = dragStartRef.current.posY + dy;

        const panelWidth = 480;
        const maxX = Math.max(0, window.innerWidth - panelWidth - 16);
        const maxY = Math.max(0, window.innerHeight - 200);

        setPosition({
          x: Math.max(-16, Math.min(newX, maxX)),
          y: Math.max(-64, Math.min(newY, maxY)),
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

    const handleExportImage = useCallback((): string => {
      if (canvasRef.current) {
        return canvasRef.current.exportImage();
      }
      return '';
    }, []);

    const handleClearCanvas = useCallback(() => {
      if (canvasRef.current) {
        canvasRef.current.clearCanvas();
      }
    }, []);

    const handleUndo = useCallback(() => {
      if (canvasRef.current) {
        canvasRef.current.undo();
      }
    }, []);

    const handleRedo = useCallback(() => {
      if (canvasRef.current) {
        canvasRef.current.redo();
      }
    }, []);

    const handleSubmit = useCallback(() => {
      const imageData = handleExportImage();
      onSubmit?.(imageData);
    }, [handleExportImage, onSubmit]);

    useImperativeHandle(ref, () => ({
      exportImage: handleExportImage,
      clearCanvas: handleClearCanvas,
      setTask: (newTask: InteractiveTask | null) => {
        setTaskState(newTask);
        if (newTask?.template) {
          setTemplate(newTask.template);
        }
      },
      setFeedback: (feedback: AIFeedback | null) => {
        setAIFeedback(feedback);
      },
    }));

    if (!visible) return null;

    return (
      <div
        ref={panelRef}
        className={`floating-interactive-panel ${isDragging ? 'dragging' : ''}`}
        style={{
          left: 16 + position.x,
          top: 80 + position.y,
        }}
      >
        <div
          className="panel-header"
          onMouseDown={handleDragStart}
        >
          <span className="panel-title">🎨 互动白板</span>
          <div className="panel-actions">
            {onClose && (
              <button
                className="panel-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onClose();
                }}
                title="收起到按钮"
              >
                <CompressOutlined />
              </button>
            )}
          </div>
        </div>

        <div className="panel-content">
          {task && (
            <div className="task-instruction">
              <span className="task-label">📝 任务：</span>
              {task.instruction}
            </div>
          )}

          <TemplateSelector />

          <ToolBar
            onUndo={handleUndo}
            onRedo={handleRedo}
            onClear={handleClearCanvas}
            onSubmit={handleSubmit}
            showSubmit={!!task}
            isSubmitting={isSubmitting}
          />

          <div className="canvas-wrapper">
            <DrawingCanvas
              ref={canvasRef}
              width={450}
              height={350}
              template={currentTemplate}
              disabled={isSubmitting}
            />
          </div>

          {aiFeedback && (
            <div className={`ai-feedback ${aiFeedback.correct ? 'correct' : 'incorrect'}`}>
              <div className="feedback-header">
                {aiFeedback.correct ? '✓ 正确' : '✗ 需要改进'}
                {aiFeedback.score !== undefined && (
                  <span className="feedback-score">{aiFeedback.score}分</span>
                )}
              </div>
              <div className="feedback-content">{aiFeedback.feedback}</div>
            </div>
          )}
        </div>
      </div>
    );
  }
);

FloatingInteractiveWhiteboard.displayName = 'FloatingInteractiveWhiteboard';

export default FloatingInteractiveWhiteboard;
