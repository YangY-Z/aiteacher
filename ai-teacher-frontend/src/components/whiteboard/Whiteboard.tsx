import React, { useEffect, useMemo, useRef, useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import Button from 'antd/es/button';
import Tooltip from 'antd/es/tooltip';
import { DownloadOutlined, ClearOutlined, LeftOutlined, RightOutlined, FilePdfOutlined } from '@ant-design/icons';
import html2canvas from 'html2canvas';
import { useLearningStore } from '../../store';
import type { WhiteboardContent } from '../../types';
import WhiteboardHTML from './WhiteboardHTML';
import './Whiteboard.css';

interface WhiteboardProps {
  loading?: boolean;
  onQuizAnswer?: (answer: string, source?: 'quiz' | 'reveal') => void;
}

type PdfImage = {
  bytes: Uint8Array;
  width: number;
  height: number;
};

const PDF_PAGE_WIDTH = 841.89;
const PDF_PAGE_HEIGHT = 595.28;

const getFileDate = () => new Date().toISOString().slice(0, 10);

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.download = filename;
  link.href = url;
  link.click();
  URL.revokeObjectURL(url);
};

const dataUrlToBytes = (dataUrl: string) => {
  const base64 = dataUrl.split(',')[1] || '';
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  return bytes;
};

const buildPdfFromImages = (images: PdfImage[]) => {
  const encoder = new TextEncoder();
  const chunks: Uint8Array[] = [];
  const offsets: number[] = [0];
  let byteLength = 0;

  const pushBytes = (bytes: Uint8Array) => {
    chunks.push(bytes);
    byteLength += bytes.length;
  };

  const pushText = (text: string) => pushBytes(encoder.encode(text));

  const addObject = (id: number, body: string | Uint8Array) => {
    offsets[id] = byteLength;
    pushText(`${id} 0 obj\n`);
    if (typeof body === 'string') {
      pushText(body);
    } else {
      pushBytes(body);
    }
    pushText('\nendobj\n');
  };

  pushText('%PDF-1.4\n');

  const pageIds = images.map((_, index) => 3 + index * 3);
  addObject(1, '<< /Type /Catalog /Pages 2 0 R >>');
  addObject(2, `<< /Type /Pages /Kids [${pageIds.map(id => `${id} 0 R`).join(' ')}] /Count ${images.length} >>`);

  images.forEach((image, index) => {
    const pageId = 3 + index * 3;
    const contentId = pageId + 1;
    const imageId = pageId + 2;
    const scale = Math.min(PDF_PAGE_WIDTH / image.width, PDF_PAGE_HEIGHT / image.height);
    const drawWidth = image.width * scale;
    const drawHeight = image.height * scale;
    const drawX = (PDF_PAGE_WIDTH - drawWidth) / 2;
    const drawY = (PDF_PAGE_HEIGHT - drawHeight) / 2;
    const content = `q\n${drawWidth.toFixed(2)} 0 0 ${drawHeight.toFixed(2)} ${drawX.toFixed(2)} ${drawY.toFixed(2)} cm\n/Im${index} Do\nQ`;

    addObject(
      pageId,
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PDF_PAGE_WIDTH} ${PDF_PAGE_HEIGHT}] /Resources << /XObject << /Im${index} ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`
    );
    addObject(contentId, `<< /Length ${content.length} >>\nstream\n${content}\nendstream`);

    offsets[imageId] = byteLength;
    pushText(`${imageId} 0 obj\n<< /Type /XObject /Subtype /Image /Width ${image.width} /Height ${image.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${image.bytes.length} >>\nstream\n`);
    pushBytes(image.bytes);
    pushText('\nendstream\nendobj\n');
  });

  const xrefOffset = byteLength;
  pushText(`xref\n0 ${offsets.length}\n0000000000 65535 f \n`);
  for (let id = 1; id < offsets.length; id += 1) {
    pushText(`${String(offsets[id]).padStart(10, '0')} 00000 n \n`);
  }
  pushText(`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`);

  return new Blob(
    chunks.map(chunk => chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength) as ArrayBuffer),
    { type: 'application/pdf' }
  );
};

const Whiteboard: React.FC<WhiteboardProps> = ({ loading = false, onQuizAnswer }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const touchStartXRef = useRef<number | null>(null);
  const wheelLockedRef = useRef(false);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const { whiteboardBlocks, currentWhiteboard, clearWhiteboard } = useLearningStore();

  const hasCurrentContent = Boolean(
    currentWhiteboard.title ||
    currentWhiteboard.key_points.length > 0 ||
    currentWhiteboard.formulas.length > 0 ||
    currentWhiteboard.examples.length > 0 ||
    currentWhiteboard.notes.length > 0 ||
    currentWhiteboard.image ||
    currentWhiteboard.html
  );

  const slides = useMemo(() => {
    return hasCurrentContent
      ? [...whiteboardBlocks, currentWhiteboard as WhiteboardContent]
      : whiteboardBlocks;
  }, [currentWhiteboard, hasCurrentContent, whiteboardBlocks]);

  const hasAnyContent = slides.length > 0;
  const currentSlideIndex = hasAnyContent
    ? Math.min(activeSlideIndex, slides.length - 1)
    : 0;

  useEffect(() => {
    if (slides.length > 0) {
      setActiveSlideIndex(slides.length - 1);
    }
  }, [slides.length]);

  const goToPrevSlide = () => {
    setActiveSlideIndex(prev => Math.max(0, prev - 1));
  };

  const goToNextSlide = () => {
    setActiveSlideIndex(prev => Math.min(slides.length - 1, prev + 1));
  };

  const handleTouchStart = (event: React.TouchEvent<HTMLDivElement>) => {
    touchStartXRef.current = event.touches[0]?.clientX ?? null;
  };

  const handleTouchEnd = (event: React.TouchEvent<HTMLDivElement>) => {
    if (touchStartXRef.current === null) return;

    const endX = event.changedTouches[0]?.clientX ?? touchStartXRef.current;
    const deltaX = endX - touchStartXRef.current;
    touchStartXRef.current = null;

    if (Math.abs(deltaX) < 48) return;

    if (deltaX < 0) {
      goToNextSlide();
    } else {
      goToPrevSlide();
    }
  };

  const handleWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    const horizontalDelta = Math.abs(event.deltaX) > Math.abs(event.deltaY)
      ? event.deltaX
      : event.shiftKey
        ? event.deltaY
        : 0;

    if (Math.abs(horizontalDelta) < 36 || wheelLockedRef.current) return;

    event.preventDefault();
    wheelLockedRef.current = true;

    if (horizontalDelta > 0) {
      goToNextSlide();
    } else {
      goToPrevSlide();
    }

    window.setTimeout(() => {
      wheelLockedRef.current = false;
    }, 420);
  };

  const getSlideElements = () => Array.from(
    contentRef.current?.querySelectorAll<HTMLElement>('.courseware-slide') || []
  );

  const captureSlide = async (slideElement: HTMLElement) => {
    const rect = slideElement.getBoundingClientRect();
    const exportRoot = document.createElement('div');
    exportRoot.className = 'whiteboard-export-sandbox';
    exportRoot.style.width = `${Math.max(rect.width, 960)}px`;
    exportRoot.style.minHeight = `${Math.max(rect.height, 540)}px`;
    exportRoot.appendChild(slideElement.cloneNode(true));

    document.body.classList.add('whiteboard-exporting');
    document.body.appendChild(exportRoot);

    try {
      return await html2canvas(exportRoot, {
        backgroundColor: '#ffffff',
        logging: false,
        scale: 2,
        useCORS: true,
        onclone: clonedDocument => {
          clonedDocument.body.classList.add('whiteboard-exporting');
        },
      });
    } finally {
      exportRoot.remove();
      document.body.classList.remove('whiteboard-exporting');
    }
  };

  // 下载当前课件页
  const handleDownload = async () => {
    const slideElement = getSlideElements()[currentSlideIndex];
    if (!slideElement) return;
    
    try {
      const canvas = await captureSlide(slideElement);
      
      const link = document.createElement('a');
      link.download = `白板笔记_${getFileDate()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // 下载全部课件页为 PDF
  const handleDownloadPdf = async () => {
    const slideElements = getSlideElements();
    if (slideElements.length === 0) return;

    try {
      const images: PdfImage[] = [];

      for (const slideElement of slideElements) {
        const canvas = await captureSlide(slideElement);
        images.push({
          bytes: dataUrlToBytes(canvas.toDataURL('image/jpeg', 0.92)),
          width: canvas.width,
          height: canvas.height,
        });
      }

      downloadBlob(buildPdfFromImages(images), `全部白板笔记_${getFileDate()}.pdf`);
    } catch (error) {
      console.error('PDF download failed:', error);
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

  const renderBlockImage = (image: WhiteboardContent['image']) => {
    if (!image) return null;

    const caption = image.title || '';

    return (
      <div className="whiteboard-generated-media">
        <div className="whiteboard-generated-media-frame">
          {image.svg_code ? (
            <div
              className="whiteboard-generated-svg"
              dangerouslySetInnerHTML={{ __html: image.svg_code }}
            />
          ) : image.url ? (
            <img
              src={image.url}
              alt={image.description || image.title || '教学图片'}
              className="whiteboard-image"
              loading="lazy"
            />
          ) : null}
        </div>
        {caption && (
          <div className="image-caption">{caption}</div>
        )}
      </div>
    );
  };

  // 渲染单个内容块
  const renderBlock = (block: WhiteboardContent, index: number, variant: 'active' | 'history' = 'history') => {
    if (block.html) {
      return (
        <div
          key={index}
          className={`whiteboard-block html-block ${block.image ? 'has-generated-media' : ''} ${variant === 'active' ? 'active-slide' : 'history-slide'}`}
        >
          <div className="whiteboard-html-media-layout">
            <div className="whiteboard-html-media-main">
              <WhiteboardHTML
                html={block.html}
                title={block.title}
                onQuizAnswer={onQuizAnswer}
              />
            </div>
            {renderBlockImage(block.image)}
          </div>
        </div>
      );
    }

    return (
      <div key={index} className={`whiteboard-block ${variant === 'active' ? 'active-slide' : 'history-slide'}`}>
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
        
        {block.image && (
          <div className="block-section">
            <div className="section-label">图片</div>
            {renderBlockImage(block.image)}
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
            title="下载笔记"
            aria-label="下载笔记"
            disabled={!hasAnyContent}
          />
        </Tooltip>
        <Tooltip title="下载全部为 PDF">
          <Button
            type="text"
            icon={<FilePdfOutlined />}
            onClick={handleDownloadPdf}
            className="toolbar-btn"
            title="下载全部为 PDF"
            aria-label="下载全部白板为 PDF"
            disabled={!hasAnyContent}
          />
        </Tooltip>
        <Tooltip title="清空笔记">
          <Button 
            type="text" 
            icon={<ClearOutlined />} 
            onClick={clearWhiteboard}
            className="toolbar-btn"
            title="清空笔记"
            aria-label="清空笔记"
          />
        </Tooltip>
      </div>

      {/* 画布容器 */}
      <div className="whiteboard-canvas-container" ref={containerRef}>
        <div className="whiteboard-canvas" ref={contentRef}>
          {/* 装饰性网格 */}
          <div className="canvas-grid" />
          
          {whiteboardBlocks.length === 0 &&
            !currentWhiteboard.title &&
            currentWhiteboard.key_points.length === 0 &&
            currentWhiteboard.formulas.length === 0 &&
            currentWhiteboard.examples.length === 0 &&
            currentWhiteboard.notes.length === 0 &&
            !currentWhiteboard.image &&
            !currentWhiteboard.html &&
            !loading && (
            <div className="whiteboard-empty">
              <div className="empty-icon">📝</div>
              <div className="empty-text">等待讲解开始</div>
              <div className="empty-hint">知识点要点将在这里展示</div>
            </div>
          )}

          {hasAnyContent && (
            <section className="courseware-slide-deck" aria-label="课件页">
              <div className="courseware-slide-topline">
                <span>课件页</span>
                <strong>{currentSlideIndex + 1} / {slides.length}</strong>
                {loading && <span className="courseware-live-dot">生成中</span>}
              </div>

              <div className="courseware-slider">
                <button
                  type="button"
                  className="courseware-nav-btn prev"
                  onClick={goToPrevSlide}
                  disabled={currentSlideIndex === 0}
                  title="上一页"
                  aria-label="上一页"
                >
                  <LeftOutlined />
                </button>

                <div
                  className="courseware-viewport"
                  onTouchStart={handleTouchStart}
                  onTouchEnd={handleTouchEnd}
                  onWheel={handleWheel}
                >
                  <div
                    className="courseware-track"
                    style={{ transform: `translateX(-${currentSlideIndex * 100}%)` }}
                  >
                    {slides.map((block, index) => (
                      <div className="courseware-slide" key={`slide-${index}`}>
                        {renderBlock(block, index, 'active')}
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  className="courseware-nav-btn next"
                  onClick={goToNextSlide}
                  disabled={currentSlideIndex >= slides.length - 1}
                  title="下一页"
                  aria-label="下一页"
                >
                  <RightOutlined />
                </button>
              </div>

              {slides.length > 1 && (
                <div className="courseware-pagination" aria-label="课件页码">
                  {slides.map((_, index) => (
                    <button
                      key={`dot-${index}`}
                      type="button"
                      className={`courseware-page-dot ${index === currentSlideIndex ? 'active' : ''}`}
                      onClick={() => setActiveSlideIndex(index)}
                      title={`第 ${index + 1} 页`}
                      aria-label={`切换到第 ${index + 1} 页`}
                    />
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default Whiteboard;
