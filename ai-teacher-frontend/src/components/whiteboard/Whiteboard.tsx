import React, { useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { Spin } from 'antd';
import { useLearningStore } from '../../store';
import './Whiteboard.css';

interface WhiteboardProps {
  loading?: boolean;
}

const Whiteboard: React.FC<WhiteboardProps> = ({ loading = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const formulaRef = useRef<HTMLDivElement>(null);
  const { whiteboardContent } = useLearningStore();

  // 渲染公式
  useEffect(() => {
    if (formulaRef.current && whiteboardContent.formulas.length > 0) {
      const formula = whiteboardContent.formulas[0];
      try {
        katex.render(formula, formulaRef.current, {
          throwOnError: false,
          displayMode: true,
        });
      } catch (e) {
        formulaRef.current.textContent = formula;
      }
    }
  }, [whiteboardContent.formulas]);

  // 绘制坐标系和直线
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布尺寸
    const rect = canvas.parentElement?.getBoundingClientRect();
    if (rect) {
      canvas.width = rect.width;
      canvas.height = rect.height;
    }

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 绘制坐标系
    drawCoordinateSystem(ctx, canvas.width, canvas.height);

    // 如果有图形需要绘制
    if (whiteboardContent.diagrams.length > 0) {
      // 解析并绘制直线
      whiteboardContent.diagrams.forEach((diagram) => {
        drawLine(ctx, canvas.width, canvas.height, diagram);
      });
    }
  }, [whiteboardContent.diagrams]);

  const drawCoordinateSystem = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number
  ) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const arrowSize = 10;
    const gridSize = 40;

    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;

    // 绘制网格
    for (let x = centerX % gridSize; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = centerY % gridSize; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // 绘制坐标轴
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2;

    // X轴
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();

    // X轴箭头
    ctx.beginPath();
    ctx.moveTo(width - arrowSize, centerY - arrowSize / 2);
    ctx.lineTo(width, centerY);
    ctx.lineTo(width - arrowSize, centerY + arrowSize / 2);
    ctx.stroke();

    // Y轴
    ctx.beginPath();
    ctx.moveTo(centerX, height);
    ctx.lineTo(centerX, 0);
    ctx.stroke();

    // Y轴箭头
    ctx.beginPath();
    ctx.moveTo(centerX - arrowSize / 2, arrowSize);
    ctx.lineTo(centerX, 0);
    ctx.lineTo(centerX + arrowSize / 2, arrowSize);
    ctx.stroke();

    // 标注原点
    ctx.fillStyle = '#666';
    ctx.font = '14px sans-serif';
    ctx.fillText('O', centerX + 8, centerY + 18);
    ctx.fillText('x', width - 15, centerY - 10);
    ctx.fillText('y', centerX + 10, 15);
  };

  const drawLine = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    diagram: string
  ) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const scale = 40;

    // 解析直线方程 y = kx + b
    const match = diagram.match(/y\s*=\s*(-?\d*\.?\d*)x\s*([+-]\s*\d*\.?\d*)?/);
    if (!match) return;

    const k = parseFloat(match[1] || '1');
    const b = parseFloat((match[2] || '0').replace(/\s/g, ''));

    ctx.strokeStyle = '#4A90D9';
    ctx.lineWidth = 3;
    ctx.beginPath();

    // 绘制直线
    for (let px = 0; px < width; px++) {
      const x = (px - centerX) / scale;
      const y = k * x + b;
      const py = centerY - y * scale;

      if (px === 0) {
        ctx.moveTo(px, py);
      } else {
        ctx.lineTo(px, py);
      }
    }

    ctx.stroke();

    // 标注k和b
    ctx.fillStyle = '#4A90D9';
    ctx.font = '14px sans-serif';
    ctx.fillText(`k = ${k}`, 20, 30);
    ctx.fillText(`b = ${b}`, 20, 50);
  };

  return (
    <div className="whiteboard">
      {loading && (
        <div className="whiteboard-loading">
          <Spin size="large" tip="正在生成教学内容..." />
        </div>
      )}
      
      {!loading && whiteboardContent.formulas.length === 0 && 
       whiteboardContent.diagrams.length === 0 && (
        <div className="whiteboard-empty">
          <span className="empty-icon">📝</span>
          <span className="empty-text">等待讲解开始</span>
        </div>
      )}

      <canvas ref={canvasRef} className="whiteboard-canvas" />
      
      {whiteboardContent.formulas.length > 0 && (
        <div ref={formulaRef} className="whiteboard-formula" />
      )}
    </div>
  );
};

export default Whiteboard;
