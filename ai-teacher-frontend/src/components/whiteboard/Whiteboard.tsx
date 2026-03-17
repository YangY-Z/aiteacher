import React, { useRef, useEffect } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Spin, Button, Tooltip } from 'antd';
import { DownloadOutlined, ClearOutlined, ExpandOutlined } from '@ant-design/icons';
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
  const { whiteboardBlocks, clearWhiteboard } = useLearningStore();

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [whiteboardBlocks]);

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

  // 渲染混合内容（文字中可能包含 $...$ 公式）
  const renderMixedContent = (text: string, keyPrefix: string) => {
    // 匹配 $...$ 格式的公式
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
  };

  // 渲染公式
  const renderFormula = (formula: string, index: number) => {
    const containerId = `formula-${index}-${Date.now()}`;
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
                <li key={i}>{point}</li>
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
                  {example}
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
                  {note}
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
          
          {whiteboardBlocks.length === 0 && !loading && (
            <div className="whiteboard-empty">
              <div className="empty-icon">📝</div>
              <div className="empty-text">等待讲解开始</div>
              <div className="empty-hint">知识点要点将在这里展示</div>
            </div>
          )}

          {whiteboardBlocks.map((block, index) => renderBlock(block, index))}
        </div>
      </div>

      {/* 加载遮罩 */}
      {loading && (
        <div className="whiteboard-loading">
          <Spin size="large" tip="正在生成教学内容..." />
        </div>
      )}
    </div>
  );
};

export default Whiteboard;