/**
 * WhiteboardHTML — 语义 HTML 白板渲染组件
 *
 * 接收 LLM 输出的 whiteboard_html（纯语义 HTML，无内联 style），
 * 经 DOMPurify 安全过滤后，用统一 CSS 主题渲染。
 *
 * 内置交互模式（React 后挂事件，无需 inline JS）：
 *   - interactive-reveal: 点击切换显示/隐藏答案
 *   - interactive-steps: 逐步揭示内容
 *   - interactive-quiz: 选择题点击反馈
 *   - interactive-flip: 卡片翻转
 *   - interactive-tabs: 选项卡切换
 */

import React, { useMemo, useRef, useEffect, useCallback } from 'react';
import katex from 'katex';
import DOMPurify from 'dompurify';
import './WhiteboardHTML.css';

interface WhiteboardHTMLProps {
  html: string;
  title?: string;
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

const ALLOWED_ATTR = [
  'class', 'id', 'href', 'target', 'rel', 'alt', 'src', 'title',
  'data-correct', 'data-hidden', 'data-tab', 'data-step',
];

/**
 * 预处理 HTML：将 $...$ 公式转换为 KaTeX 渲染的 span
 */
function preprocessFormulas(html: string): string {
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

  result = result.replace(/\$([^$\n]+?)\$/g, (_match, formula: string) => {
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

/* ── 交互模式 ── */

/**
 * 点击揭示 (interactive-reveal)
 * 点击容器切换 .reveal-answer 的可见性
 */
function initReveal(root: HTMLElement) {
  root.querySelectorAll<HTMLElement>('.interactive-reveal').forEach(el => {
    const answer = el.querySelector<HTMLElement>('.reveal-answer');
    if (!answer) return;
    el.classList.add('reveal-ready');
    el.addEventListener('click', (e) => {
      // 不干扰内部链接或按钮
      if ((e.target as HTMLElement).closest('a, button')) return;
      el.classList.toggle('revealed');
    });
  });
}

/**
 * 逐步揭示 (interactive-steps)
 * 初始只有第一步可见，点击展开下一步
 */
function initSteps(root: HTMLElement) {
  root.querySelectorAll<HTMLElement>('.interactive-steps').forEach(container => {
    const steps = container.querySelectorAll<HTMLElement>('.step');
    // 显式隐藏 data-hidden 的 steps
    steps.forEach(s => {
      if (s.getAttribute('data-hidden') !== null) {
        s.style.display = 'none';
      }
    });
    container.addEventListener('click', (e) => {
      const targetStep = (e.target as HTMLElement).closest<HTMLElement>('.step');
      if (!targetStep) return;
      // 找到下一个隐藏的 step
      const allSteps = Array.from(container.querySelectorAll<HTMLElement>('.step'));
      const currentIdx = allSteps.indexOf(targetStep);
      if (currentIdx < allSteps.length - 1) {
        const next = allSteps[currentIdx + 1];
        if (next.style.display === 'none') {
          next.style.display = 'flex';
          next.classList.add('step-enter');
          setTimeout(() => next.classList.remove('step-enter'), 300);
        }
      }
    });
  });
}

/**
 * 交互式选择题 (interactive-quiz)
 * 点击选项，data-correct 的变绿，其他的变红并禁用
 */
function initQuiz(root: HTMLElement) {
  root.querySelectorAll<HTMLElement>('.interactive-quiz').forEach(container => {
    const options = container.querySelectorAll<HTMLElement>('.quiz-option');
    let answered = false;
    options.forEach(opt => {
      opt.addEventListener('click', () => {
        if (answered) return;
        answered = true;
        const isCorrect = opt.getAttribute('data-correct') !== null;
        // 标记所有选项
        options.forEach(o => {
          if (o.getAttribute('data-correct') !== null) {
            o.classList.add('correct');
          } else {
            o.classList.add('wrong');
          }
        });
        // 给点击的选项加高亮
        opt.classList.add('selected');
        // 显示反馈
        const feedback = container.querySelector<HTMLElement>('.quiz-feedback');
        if (feedback) {
          feedback.textContent = isCorrect ? '✅ 回答正确！' : '❌ 再想想，注意左加右减哦！';
          feedback.classList.add('show');
        }
      });
    });
  });
}

/**
 * 翻转卡片 (interactive-flip)
 * 点击卡片切换 flip 状态
 */
function initFlip(root: HTMLElement) {
  root.querySelectorAll<HTMLElement>('.interactive-flip').forEach(el => {
    el.addEventListener('click', () => {
      el.classList.toggle('flipped');
    });
  });
}

/**
 * 选项卡 (interactive-tabs)
 * 点击 tab-trigger 切换对应 panel
 */
function initTabs(root: HTMLElement) {
  root.querySelectorAll<HTMLElement>('.interactive-tabs').forEach(container => {
    const triggers = container.querySelectorAll<HTMLElement>('.tab-trigger');
    const panels = container.querySelectorAll<HTMLElement>('.tab-panel');

    triggers.forEach(trigger => {
      trigger.addEventListener('click', () => {
        const tabName = trigger.getAttribute('data-tab');
        if (!tabName) return;
        // 更新 triggers
        triggers.forEach(t => t.classList.remove('active'));
        trigger.classList.add('active');
        // 更新 panels
        panels.forEach(p => {
          p.classList.remove('active');
          if (p.getAttribute('data-tab') === tabName) {
            p.classList.add('active');
          }
        });
      });
    });
  });
}

/* ── 入口：渲染后注活 ── */

const WhiteboardHTML: React.FC<WhiteboardHTMLProps> = ({
  html,
  title,
  showToolbar = false,
  onDownload,
  onClear,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  const safeHtml = useMemo(() => {
    const preprocessed = preprocessFormulas(html);
    return DOMPurify.sanitize(preprocessed, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
    });
  }, [html]);

  // 渲染后扫描 DOM，挂接交互事件
  useEffect(() => {
    if (!contentRef.current) return;
    const root = contentRef.current;
    initReveal(root);
    initSteps(root);
    initQuiz(root);
    initFlip(root);
    initTabs(root);
  }, [safeHtml]);

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
        ref={contentRef}
        className="whiteboard-html-content"
        dangerouslySetInnerHTML={{ __html: safeHtml }}
      />
    </div>
  );
};

export default WhiteboardHTML;
