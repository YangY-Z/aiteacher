import React, { useEffect, useRef, useCallback, forwardRef, useImperativeHandle } from 'react';
import * as fabric from 'fabric';
import { useInteractiveStore } from './interactiveStore';
import type { DrawingTool, DrawingTemplate } from './types';
import './DrawingCanvas.css';

interface DrawingCanvasProps {
  width?: number;
  height?: number;
  template?: DrawingTemplate | null;
  disabled?: boolean;
  onCanvasReady?: (canvas: fabric.Canvas) => void;
}

export interface DrawingCanvasRef {
  exportImage: () => string;
  clearCanvas: () => void;
  undo: () => void;
  redo: () => void;
  getCanvas: () => fabric.Canvas | null;
}

const DrawingCanvas = forwardRef<DrawingCanvasRef, DrawingCanvasProps>(
  ({ width = 800, height = 600, template, disabled = false, onCanvasReady }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const fabricRef = useRef<fabric.Canvas | null>(null);
    const isDrawing = useRef(false);
    const startPoint = useRef({ x: 0, y: 0 });

    const {
      currentTool,
      penColor,
      penWidth,
      addStroke,
      clearStrokes,
    } = useInteractiveStore();

    const saveStroke = useCallback(
      (type: DrawingTool, data: Record<string, unknown>) => {
        const stroke = {
          id: `stroke-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          type,
          color: penColor,
          lineWidth: penWidth,
          ...data,
        };
        addStroke(stroke as any);
      },
      [penColor, penWidth, addStroke]
    );

    const redrawStroke = useCallback((stroke: any) => {
      if (!fabricRef.current) return;
      const canvas = fabricRef.current;

      if (stroke.type === 'pen' && stroke.points) {
        const pathString = stroke.points
          .map((p: any, i: number) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
          .join(' ');
        const path = new fabric.Path(pathString, {
          stroke: stroke.color,
          strokeWidth: stroke.lineWidth,
          fill: '',
        });
        canvas.add(path);
      } else if (stroke.type === 'line' && stroke.start && stroke.end) {
        const line = new fabric.Line(
          [stroke.start.x, stroke.start.y, stroke.end.x, stroke.end.y],
          {
            stroke: stroke.color,
            strokeWidth: stroke.lineWidth,
          }
        );
        canvas.add(line);
      } else if (stroke.type === 'circle' && stroke.start && stroke.radius !== undefined) {
        const circle = new fabric.Circle({
          left: stroke.start.x - stroke.radius,
          top: stroke.start.y - stroke.radius,
          radius: stroke.radius,
          fill: 'transparent',
          stroke: stroke.color,
          strokeWidth: stroke.lineWidth,
        });
        canvas.add(circle);
      } else if (stroke.type === 'rectangle' && stroke.start && stroke.end) {
        const rect = new fabric.Rect({
          left: stroke.start.x,
          top: stroke.start.y,
          width: stroke.end.x - stroke.start.x,
          height: stroke.end.y - stroke.start.y,
          fill: 'transparent',
          stroke: stroke.color,
          strokeWidth: stroke.lineWidth,
        });
        canvas.add(rect);
      }
    }, []);

    const initCanvas = useCallback(() => {
      if (!canvasRef.current) return;

      if (fabricRef.current) {
        fabricRef.current.dispose();
      }

      const canvas = new fabric.Canvas(canvasRef.current, {
        width,
        height,
        backgroundColor: '#fff',
        selection: currentTool === 'select',
        isDrawingMode: currentTool === 'pen' || currentTool === 'eraser',
      });

      fabricRef.current = canvas;

      if (currentTool === 'pen') {
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = penColor;
        canvas.freeDrawingBrush.width = penWidth;
      } else if (currentTool === 'eraser') {
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = '#fff';
        canvas.freeDrawingBrush.width = penWidth * 3;
      }

      canvas.on('mouse:down', (e: fabric.TEvent) => {
        if (disabled) return;
        const pointer = canvas.getViewportPoint(e.e);
        startPoint.current = { x: pointer.x, y: pointer.y };
        isDrawing.current = true;

        if (currentTool === 'line' || currentTool === 'circle' || currentTool === 'rectangle') {
          canvas.selection = false;
        }
      });

      canvas.on('mouse:move', (e: fabric.TEvent) => {
        if (disabled || !isDrawing.current) return;
        const pointer = canvas.getViewportPoint(e.e);

        if (currentTool === 'line') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const line = new fabric.Line(
            [startPoint.current.x, startPoint.current.y, pointer.x, pointer.y],
            {
              stroke: penColor,
              strokeWidth: penWidth,
              data: { isTemp: true },
            }
          );
          canvas.add(line);
        } else if (currentTool === 'circle') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const radius = Math.sqrt(
            Math.pow(pointer.x - startPoint.current.x, 2) +
              Math.pow(pointer.y - startPoint.current.y, 2)
          );
          const circle = new fabric.Circle({
            left: startPoint.current.x - radius,
            top: startPoint.current.y - radius,
            radius,
            fill: 'transparent',
            stroke: penColor,
            strokeWidth: penWidth,
            data: { isTemp: true },
          });
          canvas.add(circle);
        } else if (currentTool === 'rectangle') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const rect = new fabric.Rect({
            left: Math.min(startPoint.current.x, pointer.x),
            top: Math.min(startPoint.current.y, pointer.y),
            width: Math.abs(pointer.x - startPoint.current.x),
            height: Math.abs(pointer.y - startPoint.current.y),
            fill: 'transparent',
            stroke: penColor,
            strokeWidth: penWidth,
            data: { isTemp: true },
          });
          canvas.add(rect);
        }
      });

      canvas.on('mouse:up', (e: fabric.TEvent) => {
        if (disabled) return;
        isDrawing.current = false;
        const pointer = canvas.getViewportPoint(e.e);

        if (currentTool === 'line') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const line = new fabric.Line(
            [startPoint.current.x, startPoint.current.y, pointer.x, pointer.y],
            {
              stroke: penColor,
              strokeWidth: penWidth,
            }
          );
          canvas.add(line);
          canvas.renderAll();
          saveStroke('line', {
            start: startPoint.current,
            end: { x: pointer.x, y: pointer.y },
          });
        } else if (currentTool === 'circle') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const radius = Math.sqrt(
            Math.pow(pointer.x - startPoint.current.x, 2) +
              Math.pow(pointer.y - startPoint.current.y, 2)
          );
          const circle = new fabric.Circle({
            left: startPoint.current.x - radius,
            top: startPoint.current.y - radius,
            radius,
            fill: 'transparent',
            stroke: penColor,
            strokeWidth: penWidth,
          });
          canvas.add(circle);
          canvas.renderAll();
          saveStroke('circle', {
            start: startPoint.current,
            radius,
          });
        } else if (currentTool === 'rectangle') {
          canvas.getObjects().forEach((obj: any) => {
            if (obj.data?.isTemp) {
              canvas.remove(obj);
            }
          });
          const rect = new fabric.Rect({
            left: Math.min(startPoint.current.x, pointer.x),
            top: Math.min(startPoint.current.y, pointer.y),
            width: Math.abs(pointer.x - startPoint.current.x),
            height: Math.abs(pointer.y - startPoint.current.y),
            fill: 'transparent',
            stroke: penColor,
            strokeWidth: penWidth,
          });
          canvas.add(rect);
          canvas.renderAll();
          saveStroke('rectangle', {
            start: {
              x: Math.min(startPoint.current.x, pointer.x),
              y: Math.min(startPoint.current.y, pointer.y),
            },
            end: {
              x: Math.max(startPoint.current.x, pointer.x),
              y: Math.max(startPoint.current.y, pointer.y),
            },
          });
        }

        canvas.selection = currentTool === 'select';
      });

      canvas.on('path:created', (e: any) => {
        if (disabled) return;
        const path = e.path;
        if (path && (currentTool === 'pen' || currentTool === 'eraser')) {
          const pathData = path.path;
          const points: { x: number; y: number }[] = [];
          pathData.forEach((cmd: any[]) => {
            if (cmd[0] === 'M' || cmd[0] === 'L' || cmd[0] === 'Q') {
              points.push({ x: cmd[1], y: cmd[2] });
            }
          });
          saveStroke('pen', { points });
        }
      });

      if (onCanvasReady) {
        onCanvasReady(canvas);
      }
    }, [width, height, currentTool, penColor, penWidth, disabled, onCanvasReady, saveStroke]);

    useEffect(() => {
      initCanvas();
      return () => {
        if (fabricRef.current) {
          fabricRef.current.dispose();
        }
      };
    }, [initCanvas]);

    useEffect(() => {
      if (!fabricRef.current) return;
      const canvas = fabricRef.current;

      canvas.isDrawingMode = currentTool === 'pen' || currentTool === 'eraser';
      canvas.selection = currentTool === 'select';

      if (currentTool === 'pen') {
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = penColor;
        canvas.freeDrawingBrush.width = penWidth;
      } else if (currentTool === 'eraser') {
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = '#fff';
        canvas.freeDrawingBrush.width = penWidth * 3;
      }
    }, [currentTool, penColor, penWidth]);

    useEffect(() => {
      if (!fabricRef.current || !template?.background) return;
      const canvas = fabricRef.current;

      fabric.loadSVGFromString(template.background).then(({ objects, options }) => {
        const filteredObjects = objects.filter((obj): obj is fabric.FabricObject => obj !== null);
        const svg = fabric.util.groupSVGElements(filteredObjects, options);
        svg.set({
          selectable: false,
          evented: false,
        });
        svg.scaleToWidth(width);
        canvas.backgroundImage = svg;
        canvas.renderAll();
      });
    }, [template, width]);

    const exportImage = useCallback((): string => {
      if (!fabricRef.current) return '';
      return fabricRef.current.toDataURL({
        format: 'png',
        quality: 1,
        multiplier: 1,
      });
    }, []);

    const clearCanvas = useCallback(() => {
      if (!fabricRef.current) return;
      fabricRef.current.clear();
      fabricRef.current.backgroundColor = '#fff';
      fabricRef.current.renderAll();
      clearStrokes();
    }, [clearStrokes]);

    const undoAction = useCallback(() => {
      if (!fabricRef.current) return;
      const objects = fabricRef.current.getObjects();
      if (objects.length > 0) {
        const lastObject = objects[objects.length - 1];
        fabricRef.current.remove(lastObject);
        fabricRef.current.renderAll();
      }
      useInteractiveStore.getState().undo();
    }, []);

    const redoAction = useCallback(() => {
      if (!fabricRef.current) return;
      useInteractiveStore.getState().redo();
      const { strokes } = useInteractiveStore.getState();
      fabricRef.current.clear();
      strokes.forEach((stroke) => {
        redrawStroke(stroke);
      });
      fabricRef.current.renderAll();
    }, [redrawStroke]);

    useImperativeHandle(ref, () => ({
      exportImage,
      clearCanvas,
      undo: undoAction,
      redo: redoAction,
      getCanvas: () => fabricRef.current,
    }));

    return (
      <div className="drawing-canvas-container">
        <canvas ref={canvasRef} />
        {template?.guide && (
          <div className="template-guide">{template.guide}</div>
        )}
      </div>
    );
  }
);

DrawingCanvas.displayName = 'DrawingCanvas';

export default DrawingCanvas;
