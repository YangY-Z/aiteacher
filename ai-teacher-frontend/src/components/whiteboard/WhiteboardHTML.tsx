/**
 * WhiteboardHTML — 语义 HTML 白板渲染组件
 *
 * 接收 LLM 输出的 whiteboard_html（纯语义 HTML，无内联 style），
 * 经 DOMPurify 安全过滤后，用统一 CSS 主题渲染。
 *
 * 内置 $...$ 公式预处理：
 *   渲染前扫描 KaTeX 公式标记，替换为带 class 的 span，由外部 CSS 控制样式。
 */

import React, { useMemo, useRef, useEffect } from 'react';
import katex from 'katex';
import DOMPurify from 'dompurify';
import './WhiteboardHTML.css';

interface WhiteboardHTMLProps {
  /** LLM 输出的语义 HTML 字符串（无内联 style） */
  html: string;
  /** 可选的标题（显示在 HTML 内容上方） */
  title?: string;
  /** 是否显示下载/清空按钮 */
  showToolbar?: boolean;
  onDownload?: () => void;
  onClear?: () => void;
}

/** 允许的 HTML 标签白名单 */
const ALLOWED_TAGS = [
  'article', 'section', 'header', 'footer', 'nav',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'br', 'hr', 'blockquote', 'pre', 'code',
  'ul', 'ol', 'li', 'dl', 'dt', 'dd',
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
  'div', 'span', 'strong', 'em', 'b', 'i', 'u', 's', 'sub', 'sup',
  'img', 'figure', 'figcaption',
  'details', 'summary',
  'label', 'input',
  'small',
];

const ALLOWED_ATTR = ['class', 'id', 'href', 'target', 'rel', 'alt', 'src', 'title'];

/**
 * 预处理 HTML：将 $...$ 公式转换为 KaTeX 渲染的 span
 */
function preprocessFormulas(html: string): string {
  // 替换 $$...$$（块级公式）为带 class 的 div
  let result = html.replace(/\$\$([\s\S]*?)\$\$/g, (_match, formula: string) => {
    try {
      const rendered = katex.renderToString(formula.trim(), {
        throwOnError: false,
        displayMode: true,
      });
      return `<div class="kb-formula-block">${rendered}</div>`;
    } catch {
      return `<div class="kb-formula-block">${formula.trim()}</div>`;
    }
  });

  // 替换 $...$（行内公式）为带 class 的 span
  result = result.replace(/\$([^$
]+?)\$/g, (_match, formula: string) => {
    try {
      const rendered = katex.renderToString(formula.trim(), {
        throwOnError: false,
        displayMode: false,
      });
      return `<span class="kb-formula-inline">${rendered}</span>`;
    } catch {
      return `<span class="kb-formula-inline">${formula.trim()}</span>`;
    }
  });

  return result;
}

const WhiteboardHTML: React.FC<WhiteboardHTMLProps> = ({
  html,
  title,
  showToolbar = false,
  onDownload,
  onClear,
}) => {
  const safeHtml = useMemo(() => {
    const preprocessed = preprocessFormulas(html);
    return DOMPurify.sanitize(preprocessed, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
    });
  }, [html]);

  return (
    <div className="whiteboard-html-wrapper">
      {showToolbar && (onDownload || onClear) && (
        <div className="whiteboard-html-toolbar">
          {onDownload && (
            <button className="wb-html-btn" onClick={onDownload} title="下载">
              ⬇
            </button>
          )}
          {onClear && (
            <button className="wb-html-btn" onClick={onClear} title="清空">
              🗑
            </button>
          )}
        </div>
      )}
      {title && <div className="wb-html-title">{title}</div>}
      <div
        className="whiteboard-html-content"
        dangerouslySetInnerHTML={{ __html: safeHtml }}
      />
    </div>
  );
};

export default WhiteboardHTML;
