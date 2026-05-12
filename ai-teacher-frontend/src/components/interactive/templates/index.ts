import type { DrawingTemplate } from '../types';

export const blankTemplate: DrawingTemplate = {
  id: 'blank',
  name: '空白画布',
  subject: 'general',
  background: '',
  guide: '自由绘制',
};

export const gridTemplate: DrawingTemplate = {
  id: 'grid',
  name: '方格纸',
  subject: 'math',
  background: `
    <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
        </pattern>
        <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
          <rect width="100" height="100" fill="url(#smallGrid)"/>
          <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#ccc" stroke-width="1"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
    </svg>
  `,
  guide: '在方格纸上绘图',
};

export const coordinateTemplate: DrawingTemplate = {
  id: 'coordinate',
  name: '平面直角坐标系',
  subject: 'math',
  background: `
    <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="smallGridCoord" width="25" height="25" patternUnits="userSpaceOnUse">
          <path d="M 25 0 L 0 0 0 25" fill="none" stroke="#f0f0f0" stroke-width="0.5"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#smallGridCoord)" />
      
      <line x1="400" y1="0" x2="400" y2="600" stroke="#333" stroke-width="2"/>
      <line x1="0" y1="300" x2="800" y2="300" stroke="#333" stroke-width="2"/>
      
      <polygon points="400,10 395,25 405,25" fill="#333"/>
      <polygon points="790,300 775,295 775,305" fill="#333"/>
      
      <text x="410" y="25" font-size="16" fill="#333">y</text>
      <text x="775" y="290" font-size="16" fill="#333">x</text>
      <text x="410" y="315" font-size="14" fill="#333">O</text>
      
      ${Array.from({ length: 15 }, (_, i) => {
        const x = 100 + i * 50;
        return `<line x1="${x}" y1="295" x2="${x}" y2="305" stroke="#333" stroke-width="1"/>`;
      }).join('')}
      
      ${Array.from({ length: 11 }, (_, i) => {
        const y = 50 + i * 50;
        return `<line x1="395" y1="${y}" x2="405" y2="${y}" stroke="#333" stroke-width="1"/>`;
      }).join('')}
    </svg>
  `,
  guide: '在坐标系中绘制函数图像',
};

export const numberLineTemplate: DrawingTemplate = {
  id: 'number-line',
  name: '数轴',
  subject: 'math',
  background: `
    <svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg">
      <line x1="50" y1="100" x2="750" y2="100" stroke="#333" stroke-width="2"/>
      <polygon points="750,100 735,95 735,105" fill="#333"/>
      
      ${Array.from({ length: 14 }, (_, i) => {
        const x = 100 + i * 50;
        return `<line x1="${x}" y1="90" x2="${x}" y2="110" stroke="#333" stroke-width="1"/>
                <text x="${x}" y="130" font-size="12" fill="#333" text-anchor="middle">${i - 3}</text>`;
      }).join('')}
    </svg>
  `,
  guide: '在数轴上标出点',
};

export const allTemplates: DrawingTemplate[] = [
  blankTemplate,
  gridTemplate,
  coordinateTemplate,
  numberLineTemplate,
];

export function getTemplateById(id: string): DrawingTemplate | undefined {
  return allTemplates.find((t) => t.id === id);
}
