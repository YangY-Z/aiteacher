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

import React, { useMemo, useRef, useEffect, useCallback, useState } from 'react';
import katex from 'katex';
import DOMPurify from 'dompurify';
import './WhiteboardHTML.css';

const quizSelectionMemory = new Map<string, Record<string, string>>();

interface WhiteboardHTMLProps {
  html: string;
  title?: string;
  showToolbar?: boolean;
  onDownload?: () => void;
  onClear?: () => void;
  onQuizAnswer?: (answer: string, source?: 'quiz' | 'reveal') => void;
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
  'label', 'input', 'button',
  'small',
];

const ALLOWED_ATTR = [
  'class', 'id', 'href', 'target', 'rel', 'alt', 'src', 'title',
  'type', 'aria-label',
  'data-answer', 'data-value', 'data-correct', 'data-hidden', 'data-tab', 'data-step',
  'data-is-question', 'data-question-type',
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
function getQuizAnswerText(option: HTMLElement): string {
  return (
    option.getAttribute('data-answer') ||
    option.getAttribute('data-value') ||
    option.textContent ||
    ''
  ).trim();
}

function getQuizSelectionKey(option: HTMLElement): string {
  const container = option.closest<HTMLElement>('.interactive-quiz');
  const root = option.closest<HTMLElement>('.whiteboard-html-content');
  const quizIndex = container && root
    ? Array.from(root.querySelectorAll<HTMLElement>('.interactive-quiz')).indexOf(container)
    : 0;
  return `quiz-${Math.max(0, quizIndex)}`;
}

function applyQuizSelection(container: HTMLElement, selectedAnswer: string) {
  const options = container.querySelectorAll<HTMLElement>('.quiz-option');
  options.forEach(o => {
    const isSelected = getQuizAnswerText(o) === selectedAnswer;
    o.classList.toggle('selected', isSelected);
    o.classList.toggle('unselected', !isSelected);
    o.setAttribute('aria-pressed', isSelected ? 'true' : 'false');

    if (o.getAttribute('data-correct') !== null) {
      o.classList.add('correct');
    } else {
      o.classList.add('wrong');
    }
  });
}

function initQuiz(root: HTMLElement, onQuizAnswer?: (answer: string, source?: 'quiz' | 'reveal') => void) {
  root.querySelectorAll<HTMLElement>('.interactive-quiz').forEach(container => {
    const options = container.querySelectorAll<HTMLElement>('.quiz-option');
    let answered = false;
    options.forEach(opt => {
      opt.setAttribute('role', 'button');
      opt.setAttribute('tabindex', '0');
      if (!opt.getAttribute('aria-label')) {
        opt.setAttribute('aria-label', `选择 ${getQuizAnswerText(opt)}`);
      }

      const submitOption = () => {
        if (answered) return;
        answered = true;
        const answerText = getQuizAnswerText(opt);
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
        if (answerText) {
          onQuizAnswer?.(answerText, 'quiz');
        }
      };

      opt.addEventListener('click', submitOption);
      opt.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        submitOption();
      });
    });
  });
}

function submitQuizOption(option: HTMLElement, onQuizAnswer?: (answer: string, source?: 'quiz' | 'reveal') => void) {
  const container = option.closest<HTMLElement>('.interactive-quiz');
  if (!container || container.dataset.answered === 'true') return;

  container.dataset.answered = 'true';
  const options = container.querySelectorAll<HTMLElement>('.quiz-option');
  const answerText = getQuizAnswerText(option);
  const isCorrect = option.getAttribute('data-correct') !== null;

  options.forEach(o => {
    o.classList.toggle('selected', o === option);
    o.classList.toggle('unselected', o !== option);
    o.setAttribute('aria-pressed', o === option ? 'true' : 'false');

    if (o.getAttribute('data-correct') !== null) {
      o.classList.add('correct');
    } else {
      o.classList.add('wrong');
    }
  });

  const feedback = container.querySelector<HTMLElement>('.quiz-feedback');
  if (feedback) {
    feedback.textContent = isCorrect ? '✅ 回答正确！' : '❌ 再想想，注意左加右减哦！';
    feedback.classList.add('show');
  }

  if (answerText) {
    window.setTimeout(() => {
      onQuizAnswer?.(answerText, 'quiz');
    }, 800);
  }
}

function toggleReveal(reveal: HTMLElement) {
  const answer = reveal.querySelector<HTMLElement>('.reveal-answer');
  if (!answer) return;

  reveal.classList.add('reveal-ready');
  reveal.classList.toggle('revealed');
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
  onQuizAnswer,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const onQuizAnswerRef = useRef(onQuizAnswer);
  const [quizSelections, setQuizSelections] = useState<Record<string, string>>(
    () => quizSelectionMemory.get(html) || {}
  );

  useEffect(() => {
    onQuizAnswerRef.current = onQuizAnswer;
  }, [onQuizAnswer]);

  const safeHtml = useMemo(() => {
    const preprocessed = preprocessFormulas(html);
    return DOMPurify.sanitize(preprocessed, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
    });
  }, [html]);

  useEffect(() => {
    setQuizSelections(quizSelectionMemory.get(html) || {});
  }, [html, safeHtml]);

  // 渲染后扫描 DOM，挂接交互事件
  useEffect(() => {
    if (!contentRef.current) return;
    const root = contentRef.current;
    root.querySelectorAll<HTMLElement>('.interactive-reveal').forEach(el => {
      if (el.querySelector<HTMLElement>('.reveal-answer')) {
        el.classList.add('reveal-ready');
      }
    });
    initSteps(root);
    root.querySelectorAll<HTMLElement>('.interactive-quiz .quiz-option').forEach(opt => {
      opt.setAttribute('role', 'button');
      opt.setAttribute('tabindex', '0');
      if (!opt.getAttribute('aria-label')) {
        opt.setAttribute('aria-label', `选择 ${getQuizAnswerText(opt)}`);
      }
    });
    initFlip(root);
    initTabs(root);
  }, [safeHtml]);

  useEffect(() => {
    if (!contentRef.current) return;
    const root = contentRef.current;
    Object.entries(quizSelections).forEach(([key, selectedAnswer]) => {
      const index = Number(key.replace('quiz-', ''));
      const container = root.querySelectorAll<HTMLElement>('.interactive-quiz')[index];
      if (container) {
        container.dataset.answered = 'true';
        applyQuizSelection(container, selectedAnswer);
      }
    });
  }, [quizSelections]);

  const handleContentClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    const quizOption = target.closest<HTMLElement>('.interactive-quiz .quiz-option');
    if (quizOption) {
      const answer = getQuizAnswerText(quizOption);
      if (answer) {
        const key = getQuizSelectionKey(quizOption);
        setQuizSelections(prev => {
          const next = { ...prev, [key]: answer };
          quizSelectionMemory.set(html, next);
          return next;
        });
      }
      submitQuizOption(quizOption, (answer, source) => onQuizAnswerRef.current?.(answer, source));
      return;
    }

    const reveal = target.closest<HTMLElement>('.interactive-reveal');
    if (!reveal || target.closest('a, button')) return;

    toggleReveal(reveal);
  }, []);

  const handleContentKeyDown = useCallback((event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;

    const target = event.target as HTMLElement;
    const quizOption = target.closest<HTMLElement>('.interactive-quiz .quiz-option');
    if (!quizOption) return;

    event.preventDefault();
    const answer = getQuizAnswerText(quizOption);
    if (answer) {
      const key = getQuizSelectionKey(quizOption);
      setQuizSelections(prev => {
        const next = { ...prev, [key]: answer };
        quizSelectionMemory.set(html, next);
        return next;
      });
    }
    submitQuizOption(quizOption, (answer, source) => onQuizAnswerRef.current?.(answer, source));
  }, []);

  return (
    <div className="whiteboard-html-wrapper">
      {showToolbar && (onDownload || onClear) && (
        <div className="whiteboard-html-toolbar">
          {onDownload && (
            <button className="wb-html-btn" onClick={onDownload} title="下载" aria-label="下载白板内容">
              ⬇
            </button>
          )}
          {onClear && (
            <button className="wb-html-btn" onClick={onClear} title="清空" aria-label="清空白板内容">
              🗑
            </button>
          )}
        </div>
      )}
      {title && <div className="wb-html-title">{title}</div>}
      <div
        ref={contentRef}
        className="whiteboard-html-content"
        onClick={handleContentClick}
        onKeyDown={handleContentKeyDown}
        dangerouslySetInnerHTML={{ __html: safeHtml }}
      />
    </div>
  );
};

export default WhiteboardHTML;
