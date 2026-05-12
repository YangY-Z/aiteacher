export type WhiteboardMode = 'display' | 'interactive' | 'annotate';

export type DrawingTool = 'pen' | 'eraser' | 'line' | 'circle' | 'rectangle' | 'text' | 'select';

export interface Point {
  x: number;
  y: number;
}

export interface DrawingStroke {
  id: string;
  type: 'pen' | 'line' | 'circle' | 'rectangle' | 'text';
  points?: Point[];
  color: string;
  lineWidth: number;
  start?: Point;
  end?: Point;
  radius?: number;
  text?: string;
  position?: Point;
}

export interface DrawingTemplate {
  id: string;
  name: string;
  subject: 'math' | 'physics' | 'chemistry' | 'general';
  background: string;
  guide?: string;
}

export interface AIFeedback {
  score?: number;
  correct: boolean;
  feedback: string;
  corrections?: Correction[];
}

export interface Correction {
  type: 'highlight' | 'cross' | 'add';
  position: Point;
  content: string;
}

export interface InteractiveTask {
  id: string;
  type: 'draw' | 'annotate' | 'solve';
  instruction: string;
  template?: DrawingTemplate;
  deadline?: number;
}
