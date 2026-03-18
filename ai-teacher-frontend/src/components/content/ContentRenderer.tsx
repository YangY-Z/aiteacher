/**
 * 动态内容渲染器
 * 根据教学模式动态渲染内容
 */

import React from 'react';
import './ContentRenderer.css';

export type TeachingModeType = 
  | 'concept_construction' 
  | 'procedural_skill' 
  | 'visual_understanding' 
  | 'contrast_analysis' 
  | 'problem_inquiry' 
  | 'error_diagnosis';

export interface TeachingContent {
  type: 'text' | 'video' | 'interactive' | 'visual' | 'practice';
  title?: string;
  body: string;
  media?: {
    type: 'image' | 'video' | 'animation';
    url?: string;
    description?: string;
  };
  interaction?: {
    type: 'choice' | 'input' | 'drag' | 'click';
    options?: Array<{ id: string; text: string }>;
    placeholder?: string;
  };
}

interface ContentRendererProps {
  teachingMode: TeachingModeType;
  phase: string;
  content: TeachingContent;
  onInteraction?: (type: string, data: any) => void;
}

/**
 * 根据教学模式动态渲染内容
 */
const ContentRenderer: React.FC<ContentRendererProps> = ({
  teachingMode,
  phase,
  content,
  onInteraction,
}) => {
  // 获取教学模式对应的样式类
  const getModeClass = () => {
    const modeClassMap: Record<TeachingModeType, string> = {
      concept_construction: 'mode-concept',
      procedural_skill: 'mode-skill',
      visual_understanding: 'mode-visual',
      contrast_analysis: 'mode-contrast',
      problem_inquiry: 'mode-inquiry',
      error_diagnosis: 'mode-error',
    };
    return modeClassMap[teachingMode] || '';
  };

  // 渲染媒体内容
  const renderMedia = () => {
    if (!content.media) return null;

    switch (content.media.type) {
      case 'image':
        return (
          <div className="content-media image">
            <img 
              src={content.media.url} 
              alt={content.media.description || ''} 
            />
            {content.media.description && (
              <p className="media-description">{content.media.description}</p>
            )}
          </div>
        );
      case 'video':
        return (
          <div className="content-media video">
            <video 
              src={content.media.url} 
              controls
              poster={content.media.description}
            />
          </div>
        );
      case 'animation':
        return (
          <div className="content-media animation">
            <div className="animation-placeholder">
              🎬 动画演示区域
              {content.media.description && (
                <p>{content.media.description}</p>
              )}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  // 渲染交互内容
  const renderInteraction = () => {
    if (!content.interaction) return null;

    switch (content.interaction.type) {
      case 'choice':
        return (
          <div className="content-interaction choice">
            {content.interaction.options?.map((option) => (
              <button
                key={option.id}
                className="interaction-option"
                onClick={() => onInteraction?.('choice', option)}
              >
                {option.text}
              </button>
            ))}
          </div>
        );
      case 'input':
        return (
          <div className="content-interaction input">
            <input
              type="text"
              placeholder={content.interaction.placeholder || '请输入答案...'}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onInteraction?.('input', (e.target as HTMLInputElement).value);
                }
              }}
            />
          </div>
        );
      case 'click':
        return (
          <div className="content-interaction click">
            <div className="click-area">
              点击此区域进行交互
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`content-renderer ${getModeClass()} phase-${phase.replace(/\s+/g, '-')}`}>
      {content.title && (
        <h3 className="content-title">{content.title}</h3>
      )}
      
      <div className="content-body">
        {content.body}
      </div>

      {renderMedia()}
      {renderInteraction()}
    </div>
  );
};

export default ContentRenderer;
