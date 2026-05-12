import { create } from 'zustand';
import type { WhiteboardMode, DrawingTool, DrawingStroke, DrawingTemplate, AIFeedback } from './types';

interface InteractiveState {
  mode: WhiteboardMode;
  setMode: (mode: WhiteboardMode) => void;

  strokes: DrawingStroke[];
  addStroke: (stroke: DrawingStroke) => void;
  clearStrokes: () => void;
  undo: () => void;
  redo: () => void;

  currentTool: DrawingTool;
  setCurrentTool: (tool: DrawingTool) => void;

  penColor: string;
  penWidth: number;
  setPenColor: (color: string) => void;
  setPenWidth: (width: number) => void;

  currentTemplate: DrawingTemplate | null;
  setTemplate: (template: DrawingTemplate | null) => void;

  aiFeedback: AIFeedback | null;
  setAIFeedback: (feedback: AIFeedback | null) => void;

  isSubmitting: boolean;
  setSubmitting: (submitting: boolean) => void;

  historyStack: DrawingStroke[][];
  historyIndex: number;
  pushHistory: (strokes: DrawingStroke[]) => void;
}

export const useInteractiveStore = create<InteractiveState>((set, get) => ({
  mode: 'display',
  setMode: (mode) => set({ mode }),

  strokes: [],
  addStroke: (stroke) => {
    const { strokes, historyStack, historyIndex } = get();
    const newStrokes = [...strokes, stroke];
    const newHistory = historyStack.slice(0, historyIndex + 1);
    newHistory.push([...newStrokes]);
    set({
      strokes: newStrokes,
      historyStack: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },
  clearStrokes: () => {
    const { historyStack, historyIndex } = get();
    const newHistory = historyStack.slice(0, historyIndex + 1);
    newHistory.push([]);
    set({
      strokes: [],
      historyStack: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },

  undo: () => {
    const { historyIndex, historyStack } = get();
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      set({
        strokes: historyStack[newIndex] || [],
        historyIndex: newIndex,
      });
    }
  },
  redo: () => {
    const { historyIndex, historyStack } = get();
    if (historyIndex < historyStack.length - 1) {
      const newIndex = historyIndex + 1;
      set({
        strokes: historyStack[newIndex],
        historyIndex: newIndex,
      });
    }
  },

  currentTool: 'pen',
  setCurrentTool: (tool) => set({ currentTool: tool }),

  penColor: '#000000',
  penWidth: 2,
  setPenColor: (color) => set({ penColor: color }),
  setPenWidth: (width) => set({ penWidth: width }),

  currentTemplate: null,
  setTemplate: (template) => set({ currentTemplate: template }),

  aiFeedback: null,
  setAIFeedback: (feedback) => set({ aiFeedback: feedback }),

  isSubmitting: false,
  setSubmitting: (submitting) => set({ isSubmitting: submitting }),

  historyStack: [[]],
  historyIndex: 0,
  pushHistory: (strokes) => {
    const { historyStack, historyIndex } = get();
    const newHistory = historyStack.slice(0, historyIndex + 1);
    newHistory.push([...strokes]);
    set({
      historyStack: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },
}));
