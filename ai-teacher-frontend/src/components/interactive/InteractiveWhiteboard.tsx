import React, { useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import * as fabric from 'fabric';
import { useInteractiveStore } from './interactiveStore';
import { useLearningStore } from '../../store';
import DrawingCanvas from './DrawingCanvas';
import ToolBar from './ToolBar';
import TemplateSelector from './TemplateSelector';
import type { WhiteboardMode, AIFeedback, InteractiveTask } from './types';
import './InteractiveWhiteboard.css';

interface InteractiveWhiteboardProps {
  mode?: WhiteboardMode;
  onModeChange?: (mode: WhiteboardMode) => void;
  interactiveTask?: InteractiveTask | null;
  aiFeedback?: AIFeedback | null;
  onSubmit?: (imageData: string) => void;
  isSubmitting?: boolean;
  width?: number;
  height?: number;
  compact?: boolean;
}

export interface InteractiveWhiteboardRef {
  exportImage: () => string;
  clearCanvas: () => void;
  switchMode: (mode: WhiteboardMode) => void;
}

const InteractiveWhiteboard = forwardRef<InteractiveWhiteboardRef, InteractiveWhiteboardProps>(
  (
    {
      mode: propMode,
      onModeChange,
      interactiveTask,
      aiFeedback,
      onSubmit,
      isSubmitting = false,
      width = 800,
      height = 600,
      compact = false,
    },
    ref
  ) => {
    const canvasRef = useRef<any>(null);
    const {
      mode: storeMode,
      setMode,
      currentTemplate,
      setTemplate,
      aiFeedback: storeFeedback,
      setAIFeedback,
    } = useInteractiveStore();

    const { currentWhiteboard } = useLearningStore();

    const mode = propMode || storeMode;
    const feedback = aiFeedback || storeFeedback;

    const handleModeChange = useCallback(
      (newMode: WhiteboardMode) => {
        setMode(newMode);
        onModeChange?.(newMode);
      },
      [setMode, onModeChange]
    );

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
      switchMode: handleModeChange,
    }));

    React.useEffect(() => {
      if (interactiveTask?.template) {
        setTemplate(interactiveTask.template);
      }
    }, [interactiveTask, setTemplate]);

    React.useEffect(() => {
      if (aiFeedback) {
        setAIFeedback(aiFeedback);
      }
    }, [aiFeedback, setAIFeedback]);

    const renderDisplayMode = () => (
      <div className="whiteboard-display">
        <div className="whiteboard-header">
          {currentWhiteboard.title && (
            <h3 className="whiteboard-title">{currentWhiteboard.title}</h3>
          )}
        </div>
        <div className="whiteboard-content">
          {currentWhiteboard.key_points.length > 0 && (
            <div className="whiteboard-section">
              <h4>要点</h4>
              <ul>
                {currentWhiteboard.key_points.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {currentWhiteboard.formulas.length > 0 && (
            <div className="whiteboard-section">
              <h4>公式</h4>
              {currentWhiteboard.formulas.map((formula, idx) => (
                <div key={idx} className="formula-item">
                  {formula}
                </div>
              ))}
            </div>
          )}
          {currentWhiteboard.examples.length > 0 && (
            <div className="whiteboard-section">
              <h4>示例</h4>
              {currentWhiteboard.examples.map((example, idx) => (
                <div key={idx} className="example-item">
                  {example}
                </div>
              ))}
            </div>
          )}
          {currentWhiteboard.notes.length > 0 && (
            <div className="whiteboard-section">
              <h4>注意</h4>
              {currentWhiteboard.notes.map((note, idx) => (
                <div key={idx} className="note-item">
                  💡 {note}
                </div>
              ))}
            </div>
          )}
          {currentWhiteboard.image && (
            <div className="whiteboard-section">
              <img
                src={currentWhiteboard.image.url}
                alt={currentWhiteboard.image.title || '教学图片'}
                className="whiteboard-image"
              />
            </div>
          )}
        </div>
      </div>
    );

    const renderInteractiveMode = () => (
      <div className="whiteboard-interactive">
        {interactiveTask && (
          <div className="task-instruction">
            <span className="task-label">任务：</span>
            {interactiveTask.instruction}
          </div>
        )}
        {compact ? (
          <details className="compact-template-panel">
            <summary>模板</summary>
            <TemplateSelector />
          </details>
        ) : (
          <TemplateSelector />
        )}
        <ToolBar
          onUndo={handleUndo}
          onRedo={handleRedo}
          onClear={handleClearCanvas}
          onSubmit={handleSubmit}
          showSubmit={!!interactiveTask}
          isSubmitting={isSubmitting}
          compact={compact}
        />
        <div className="canvas-wrapper">
          <DrawingCanvas
            ref={canvasRef}
            width={width}
            height={height}
            template={currentTemplate}
            disabled={isSubmitting}
          />
        </div>
      </div>
    );

    const renderAnnotateMode = () => (
      <div className="whiteboard-annotate">
        <div className="annotate-content">
          {renderDisplayMode()}
          <div className="annotate-overlay">
            <DrawingCanvas
              width={width}
              height={height}
              disabled={isSubmitting}
            />
          </div>
        </div>
      </div>
    );

    const renderFeedback = () => {
      if (!feedback) return null;
      return (
        <div className={`ai-feedback ${feedback.correct ? 'correct' : 'incorrect'}`}>
          <div className="feedback-header">
            {feedback.correct ? '✓ 正确' : '✗ 需要改进'}
            {feedback.score !== undefined && (
              <span className="feedback-score">{feedback.score}分</span>
            )}
          </div>
          <div className="feedback-content">{feedback.feedback}</div>
        </div>
      );
    };

    return (
      <div className={`interactive-whiteboard ${compact ? 'compact-whiteboard' : ''}`}>
        {!compact && (
          <div className="mode-tabs">
            <button
              className={`mode-tab ${mode === 'display' ? 'active' : ''}`}
              onClick={() => handleModeChange('display')}
            >
              📖 展示白板
            </button>
            <button
              className={`mode-tab ${mode === 'interactive' ? 'active' : ''}`}
              onClick={() => handleModeChange('interactive')}
            >
              ✏️ 互动白板
            </button>
            <button
              className={`mode-tab ${mode === 'annotate' ? 'active' : ''}`}
              onClick={() => handleModeChange('annotate')}
            >
              📝 标注
            </button>
          </div>
        )}

        <div className="whiteboard-body">
          {mode === 'display' && renderDisplayMode()}
          {mode === 'interactive' && renderInteractiveMode()}
          {mode === 'annotate' && renderAnnotateMode()}
          {renderFeedback()}
        </div>
      </div>
    );
  }
);

InteractiveWhiteboard.displayName = 'InteractiveWhiteboard';

export default InteractiveWhiteboard;
