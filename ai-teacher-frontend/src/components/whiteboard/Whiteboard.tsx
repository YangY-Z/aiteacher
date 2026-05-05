import React, { useRef, useEffect } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import Button from 'antd/es/button';
import Tooltip from 'antd/es/tooltip';
import { DownloadOutlined, ClearOutlined } from '@ant-design/icons';
import html2canvas from 'html2canvas';
import { useLearningStore } from '../../store';
import type { WhiteboardContent } from '../../types';
import './Whiteboard.css';

interface WhiteboardProps {
  loading?: boolean;
}

const Whiteboard: React.FC<WhiteboardProps> = ({ loading = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const { whiteboardBlocks, currentWhiteboard, clearWhiteboard } = useLearningStore();

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [whiteboardBlocks, currentWhiteboard]);

  // 下载白板
  const handleDownload = async () => {
    if (!contentRef.current) return;
    
    try {
      const canvas = await html2canvas(contentRef.current, {
        backgroundColor: '#1a1a2e',
        scale: 2,
      });
      
      const link = document.createElement('a');
      link.download = `黑板笔记_${new Date().toLocaleDateString()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // 渲染混合内容（文字中可能包含 $...$ 公式或纯 LaTeX）
  const renderMixedContent = (text: unknown, keyPrefix: string) => {
    // 类型检查：确保是字符串
    if (typeof text !== 'string') {
      return <span key={`${keyPrefix}-text`}>{String(text)}</span>;
    }
    
    // 检测是否包含 LaTeX 命令
    const latexCommands = ['\\frac', '\\sqrt', '\\pi', '\\ge', '\\le', '\\neq', '\\ne', '\\pm', '\\cdot', '\\times', '\\div', '\\sum', '\\int', '\\alpha', '\\beta', '\\gamma', '\\theta', '\\infty', '\\rightarrow', '\\left', '\\right', '\\overline', '\\underline', '\\vec', '\\hat', '\\bar'];
    const hasLatex = latexCommands.some(cmd => text.includes(cmd));
    
    // 如果有 $...$ 格式，按 $ 分割
    if (text.includes('$')) {
      const parts = text.split(/(\$[^$]+\$)/g);
      
      return parts.map((part, index) => {
        if (part.startsWith('$') && part.endsWith('$')) {
          // 是公式，去掉 $ 符号后渲染
          const formula = part.slice(1, -1);
          return (
            <span 
              key={`${keyPrefix}-formula-${index}`}
              ref={(el) => {
                if (el) {
                  try {
                    katex.render(formula, el, {
                      throwOnError: false,
                      displayMode: false,
                    });
                  } catch (e) {
                    el.textContent = formula;
                  }
                }
              }}
              className="inline-formula"
            />
          );
        }
        // 普通文字
        return <span key={`${keyPrefix}-text-${index}`}>{part}</span>;
      });
    }
    
    // 如果没有 $ 但包含 LaTeX 命令，尝试整体渲染
    if (hasLatex) {
      return (
        <span 
          key={`${keyPrefix}-latex`}
          ref={(el) => {
            if (el) {
              try {
                katex.render(text, el, {
                  throwOnError: false,
                  displayMode: false,
                });
              } catch (e) {
                // 如果整体渲染失败，尝试识别公式部分
                el.textContent = text;
              }
            }
          }}
          className="inline-formula"
        />
      );
    }
    
    // 纯文本
    return <span key={`${keyPrefix}-text`}>{text}</span>;
  };

  // 渲染公式
  const renderFormula = (formula: unknown, index: number) => {
    const containerId = `formula-${index}-${Date.now()}`;
    
    // 类型检查：确保是字符串
    if (typeof formula !== 'string') {
      return (
        <div key={index} className="whiteboard-formula">
          {String(formula)}
        </div>
      );
    }
    
    // 去掉 $ 符号，KaTeX 不需要它们
    const cleanFormula = formula.replace(/^\$+|\$+$/g, '').trim();
    
    // 检查是否包含混合内容（公式中夹杂文字说明）
    if (cleanFormula.includes('$') || /[\u4e00-\u9fa5]/.test(cleanFormula)) {
      // 有中文或嵌套$，可能是混合内容
      if (cleanFormula.includes('$')) {
        return (
          <div key={index} className="whiteboard-formula-mixed">
            {renderMixedContent(cleanFormula, `formula-${index}`)}
          </div>
        );
      }
    }
    
    return (
      <div 
        key={index} 
        className="whiteboard-formula"
        id={containerId}
        ref={(el) => {
          if (el) {
            try {
              katex.render(cleanFormula, el, {
                throwOnError: false,
                displayMode: true,
              });
            } catch (e) {
              el.textContent = cleanFormula;
            }
          }
        }}
      />
    );
  };

  // 渲染单个内容块
  const renderBlock = (block: WhiteboardContent, index: number) => {
    return (
      <div key={index} className="whiteboard-block">
        {block.title && (
          <div className="block-title">
            <span className="title-decoration">◆</span>
            {block.title}
          </div>
        )}
        
        {block.key_points && block.key_points.length > 0 && (
          <div className="block-section">
            <div className="section-label">要点</div>
            <ul className="key-points-list">
              {block.key_points.map((point, i) => (
                <li key={i}>{renderMixedContent(point, `kp-${i}`)}</li>
              ))}
            </ul>
          </div>
        )}
        
        {block.formulas && block.formulas.length > 0 && (
          <div className="block-section">
            <div className="section-label">公式</div>
            <div className="formulas-container">
              {block.formulas.map((formula, i) => renderFormula(formula, i))}
            </div>
          </div>
        )}
        
        {block.examples && block.examples.length > 0 && (
          <div className="block-section">
            <div className="section-label">示例</div>
            <div className="examples-container">
              {block.examples.map((example, i) => (
                <div key={i} className="example-item">
                  <span className="example-icon">📌</span>
                  {renderMixedContent(example, `example-${i}`)}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {block.notes && block.notes.length > 0 && (
          <div className="block-section">
            <div className="section-label">注意</div>
            <div className="notes-container">
              {block.notes.map((note, i) => (
                <div key={i} className="note-item">
                  <span className="note-icon">⚠️</span>
                  {renderMixedContent(note, `note-${i}`)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="whiteboard">
      {/* 工具栏 */}
      <div className="whiteboard-toolbar">
        <Tooltip title="下载笔记">
          <Button 
            type="text" 
            icon={<DownloadOutlined />} 
            onClick={handleDownload}
            className="toolbar-btn"
          />
        </Tooltip>
        <Tooltip title="清空白板">
          <Button 
            type="text" 
            icon={<ClearOutlined />} 
            onClick={clearWhiteboard}
            className="toolbar-btn"
          />
        </Tooltip>
      </div>

      {/* 画布容器 */}
      <div className="whiteboard-canvas-container" ref={containerRef}>
        <div className="whiteboard-canvas" ref={contentRef}>
          {/* 装饰性网格 */}
          <div className="canvas-grid" />
          
          {whiteboardBlocks.length === 0 && !currentWhiteboard.title && !loading && (
            <div className="whiteboard-empty">
              <div className="empty-icon">📝</div>
              <div className="empty-text">等待讲解开始</div>
              <div className="empty-hint">知识点要点将在这里展示</div>
            </div>
          )}

          {/* 渲染已提交的白板块 */}
          {whiteboardBlocks.map((block, index) => renderBlock(block, index))}
          
          {/* 渲染当前正在增量更新的白板内容 */}
          {(currentWhiteboard.title || 
            currentWhiteboard.key_points.length > 0 || 
            currentWhiteboard.formulas.length > 0 || 
            currentWhiteboard.examples.length > 0 || 
            currentWhiteboard.notes.length > 0) && (
            <div className="whiteboard-block streaming">
              {currentWhiteboard.title && (
                <div className="block-title">
                  <span className="title-decoration">◆</span>
                  {currentWhiteboard.title}
                </div>
              )}
              
              {currentWhiteboard.key_points.length > 0 && (
                <div className="block-section">
                  <div className="section-label">要点</div>
                  <ul className="key-points-list">
                    {currentWhiteboard.key_points.map((point, i) => (
                      <li key={i}>{renderMixedContent(point, `kp-${i}`)}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {currentWhiteboard.formulas.length > 0 && (
                <div className="block-section">
                  <div className="section-label">公式</div>
                  <div className="formulas-container">
                    {currentWhiteboard.formulas.map((formula, i) => renderFormula(formula, i))}
                  </div>
                </div>
              )}
              
              {currentWhiteboard.examples.length > 0 && (
                <div className="block-section">
                  <div className="section-label">示例</div>
                  <div className="examples-container">
                    {currentWhiteboard.examples.map((example, i) => (
                      <div key={i} className="example-item">
                        <span className="example-icon">📌</span>
                        {renderMixedContent(example, `example-${i}`)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {currentWhiteboard.notes.length > 0 && (
                <div className="block-section">
                  <div className="section-label">注意</div>
                  <div className="notes-container">
                    {currentWhiteboard.notes.map((note, i) => (
                      <div key={i} className="note-item">
                        <span className="note-icon">⚠️</span>
                        {renderMixedContent(note, `note-${i}`)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Whiteboard;