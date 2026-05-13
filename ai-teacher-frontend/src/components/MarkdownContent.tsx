/**
 * MarkdownContent — 渲染带有 Markdown 格式 + LaTeX 公式的教学内容
 *
 * 支持：
 * - 标准 Markdown（粗体、斜体、列表、标题、代码、链接等）
 * - 行内公式 $...$ 、块级公式 $$...$$
 * - 反斜杠格式 \[...\]、\(...\)
 */
import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import DOMPurify from 'dompurify';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

// 占位符前缀
let placeholderCounter = 0;
const PLACEHOLDER_PREFIX = '%%KATEX_FORMULA_';

/**
 * 预处理文本：将 LaTeX 公式替换为占位符，返回替换后的文本和公式映射表
 */
function extractFormulas(text: string): {
  processed: string;
  formulas: Map<string, { formula: string; isBlock: boolean }>;
} {
  const formulas = new Map<string, { formula: string; isBlock: boolean }>();

  // 1. 先处理块级公式 $$...$$
  let result = text.replace(/\$\$([\s\S]*?)\$\$/g, (_match, formula: string) => {
    const key = `${PLACEHOLDER_PREFIX}${placeholderCounter++}__`;
    formulas.set(key, { formula: formula.trim(), isBlock: true });
    return key;
  });

  // 2. 处理 \[...\] 块级
  result = result.replace(/\\\[([\s\S]*?)\\\]/g, (_match, formula: string) => {
    const key = `${PLACEHOLDER_PREFIX}${placeholderCounter++}__`;
    formulas.set(key, { formula: formula.trim(), isBlock: true });
    return key;
  });

  // 3. 处理行内 $...$（非跨行）
  result = result.replace(/\$([^$\n]+?)\$/g, (_match, formula: string) => {
    const key = `${PLACEHOLDER_PREFIX}${placeholderCounter++}__`;
    formulas.set(key, { formula: formula.trim(), isBlock: false });
    return key;
  });

  // 4. 处理 \(...\) 行内
  result = result.replace(/\\\(([^)]+?)\\\)/g, (_match, formula: string) => {
    const key = `${PLACEHOLDER_PREFIX}${placeholderCounter++}__`;
    formulas.set(key, { formula: formula.trim(), isBlock: false });
    return key;
  });

  return { processed: result, formulas };
}

/**
 * 渲染单个公式
 */
function renderFormula(formula: string, isBlock: boolean): string {
  try {
    return katex.renderToString(formula, {
      throwOnError: false,
      displayMode: isBlock,
    });
  } catch {
    return formula;
  }
}

/**
 * 将 markdown 渲染为 HTML，并替换公式占位符为 KaTeX HTML
 */
function renderToHtml(markdown: string): string {
  const { processed, formulas } = extractFormulas(markdown);

  // 用 react-markdown 渲染 markdown → 需要先做 inline 转换
  // 但 react-markdown 是 React 组件不是纯函数，我们需要另一种方式
  // 直接使用 react-markdown 组件，然后在 rendered 内部处理公式
  return processed;
}

const MarkdownContent: React.FC<MarkdownContentProps> = ({ content, className }) => {
  // 确保内容存在
  if (!content) return null;

  const { processed, formulas } = useMemo(() => {
    placeholderCounter = 0;
    return extractFormulas(content);
  }, [content]);

  // 自定义渲染组件
  const components = useMemo(() => ({
    // 在 p 标签中替换公式占位符
    p: ({ children, ...props }: any) => {
      // 处理 children 中的公式占位符
      const processedChildren = React.Children.map(children, (child) => {
        if (typeof child === 'string') {
          // 检查是否包含公式占位符
          const formulaEntry = formulas.get(child);
          if (formulaEntry) {
            const html = renderFormula(formulaEntry.formula, formulaEntry.isBlock);
            if (formulaEntry.isBlock) {
              return (
                <div
                  className="formula-block"
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              );
            }
            return (
              <span
                className="formula-inline"
                dangerouslySetInnerHTML={{ __html: html }}
              />
            );
          }
          // 检查是否包含 embedded 占位符（和普通文本混在一起的情况）
          const parts: React.ReactNode[] = [];
          let remaining = child;
          let match: RegExpExecArray | null;
          const regex = new RegExp(`${PLACEHOLDER_PREFIX}\\d+__`, 'g');
          let lastIdx = 0;
          while ((match = regex.exec(remaining)) !== null) {
            // 占位符前的文本
            if (match.index > lastIdx) {
              parts.push(remaining.slice(lastIdx, match.index));
            }
            const formulaEntry = formulas.get(match[0]);
            if (formulaEntry) {
              const html = renderFormula(formulaEntry.formula, false);
              parts.push(
                <span
                  key={match.index}
                  className="formula-inline"
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              );
            }
            lastIdx = match.index + match[0].length;
          }
          if (lastIdx < remaining.length) {
            parts.push(remaining.slice(lastIdx));
          }
          return parts.length > 0 ? parts : child;
        }
        return child;
      });
      return <p {...props}>{processedChildren}</p>;
    },

    // 自定义 li — 支持公式
    li: ({ children, ...props }: any) => {
      const processedChildren = React.Children.map(children, (child) => {
        if (typeof child === 'string') {
          const parts: React.ReactNode[] = [];
          let remaining = child;
          const regex = new RegExp(`${PLACEHOLDER_PREFIX}\\d+__`, 'g');
          let match: RegExpExecArray | null;
          let lastIdx = 0;
          while ((match = regex.exec(remaining)) !== null) {
            if (match.index > lastIdx) {
              parts.push(remaining.slice(lastIdx, match.index));
            }
            const formulaEntry = formulas.get(match[0]);
            if (formulaEntry) {
              const html = renderFormula(formulaEntry.formula, false);
              parts.push(
                <span
                  key={match.index}
                  className="formula-inline"
                  dangerouslySetInnerHTML={{ __html: html }}
                />
              );
            }
            lastIdx = match.index + match[0].length;
          }
          if (lastIdx < remaining.length) {
            parts.push(remaining.slice(lastIdx));
          }
          return parts.length > 0 ? parts : child;
        }
        return child;
      });
      return <li {...props}>{processedChildren}</li>;
    },

    // 自定义 h1-h6, td, th, div, span — 都支持公式
    h1: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <h1 {...props}>{processedChildren}</h1>;
    },
    h2: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <h2 {...props}>{processedChildren}</h2>;
    },
    h3: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <h3 {...props}>{processedChildren}</h3>;
    },
    h4: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <h4 {...props}>{processedChildren}</h4>;
    },
    strong: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <strong {...props}>{processedChildren}</strong>;
    },
    em: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <em {...props}>{processedChildren}</em>;
    },
    code: ({ children, ...props }: any) => {
      return <code {...props}>{children}</code>;
    },
    // 自定义 td / th
    td: ({ children, ...props }: any) => {
      const processedChildren = processChildren(children, formulas);
      return <td {...props}>{processedChildren}</td>;
    },
  }), [formulas]);

  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {processed}
      </ReactMarkdown>
    </div>
  );
};

/**
 * 递归处理 children 中的公式占位符
 */
function processChildren(
  children: React.ReactNode,
  formulas: Map<string, { formula: string; isBlock: boolean }>
): React.ReactNode {
  return React.Children.map(children, (child) => {
    if (typeof child === 'string') {
      const parts: React.ReactNode[] = [];
      let remaining = child;
      const regex = new RegExp(`${PLACEHOLDER_PREFIX}\\d+__`, 'g');
      let match: RegExpExecArray | null;
      let lastIdx = 0;
      while ((match = regex.exec(remaining)) !== null) {
        if (match.index > lastIdx) {
          parts.push(remaining.slice(lastIdx, match.index));
        }
        const formulaEntry = formulas.get(match[0]);
        if (formulaEntry) {
          const html = renderFormula(formulaEntry.formula, false);
          parts.push(
            <span
              key={match.index}
              className="formula-inline"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        }
        lastIdx = match.index + match[0].length;
      }
      if (lastIdx < remaining.length) {
        parts.push(remaining.slice(lastIdx));
      }
      return parts.length > 0 ? parts : child;
    }
    // 递归处理嵌套 children
    if (React.isValidElement(child) && (child.props as any)?.children) {
      const el = child as any;
      return React.cloneElement(
        el,
        el.props,
        processChildren(el.props.children, formulas)
      );
    }
    return child;
  });
}

export default MarkdownContent;
