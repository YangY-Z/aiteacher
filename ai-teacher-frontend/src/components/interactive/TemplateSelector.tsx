import React from 'react';
import { useInteractiveStore } from './interactiveStore';
import { allTemplates } from './templates';
import './TemplateSelector.css';

const subjectLabels: Record<string, string> = {
  math: '数学',
  physics: '物理',
  chemistry: '化学',
  general: '通用',
};

const TemplateSelector: React.FC = () => {
  const { currentTemplate, setTemplate } = useInteractiveStore();

  return (
    <div className="template-selector">
      <span className="selector-label">模板：</span>
      <div className="template-list">
        {allTemplates.map((template) => (
          <button
            key={template.id}
            className={`template-btn ${currentTemplate?.id === template.id ? 'active' : ''}`}
            onClick={() => setTemplate(template)}
            title={template.guide}
          >
            <span className="template-name">{template.name}</span>
            <span className="template-subject">{subjectLabels[template.subject]}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default TemplateSelector;
