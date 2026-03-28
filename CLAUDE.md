# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI虚拟教师系统 (AI Virtual Teacher System) - K12智能教学平台，MVP阶段聚焦初一数学"一次函数"单元（32个知识点）。系统通过预设知识图谱结合LLM讲解，提供自适应学习路径和回溯补救机制。

**Tech Stack:**
- Backend: Python 3.11 + FastAPI + Uvicorn
- Frontend: React 18 + TypeScript + Vite + Ant Design
- LLM: 智谱AI GLM-4 (primary)
- Data: In-memory database with JSON persistence (MVP)

## Development Commands

### Backend (FastAPI)

```bash
cd ai-teacher-backend

# Install dependencies
pip install -r requirements.txt

# Run development server (port 8008)
python run.py

# Alternative: run with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload

# Code quality
black app/                    # Format code
ruff check app/              # Lint
mypy app/                    # Type check
```

**Environment Setup:**
- Copy `.env` and set `ZHIPU_API_KEY` for LLM access
- Backend runs on `http://localhost:8008`
- API docs: `http://localhost:8008/docs`

### Frontend (React + Vite)

```bash
cd ai-teacher-frontend

# Install dependencies
npm install

# Run development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

**Frontend runs on:** `http://localhost:3000`
**API proxy:** `/api` → `http://localhost:8008`

## Architecture

### Backend Structure (Layered Architecture)

```
ai-teacher-backend/app/
├── main.py                    # FastAPI app entry, CORS, exception handlers
├── api/                       # API endpoints (auth, students, courses, learning)
├── services/                  # Business logic layer
│   ├── llm_service.py        # LLM provider abstraction
│   ├── llm_providers/        # Provider implementations (zhipu, factory)
│   ├── learning_service.py   # Session management, teaching content generation
│   ├── course_service.py     # Knowledge graph traversal
│   ├── backtrack_service.py  # Backtrack decision logic
│   └── student_service.py    # Student auth & management
├── repositories/              # Data access layer
│   ├── memory_db.py          # In-memory DB (simulates PostgreSQL/MongoDB/Redis)
│   └── *_repository.py       # Repository pattern implementations
├── models/                    # Domain models (dataclasses)
├── schemas/                   # Pydantic DTOs for API requests/responses
├── prompts/                   # LLM prompt templates
│   ├── system_prompt.py
│   ├── teaching_prompt.py
│   ├── question_prompt.py
│   └── backtrack_prompt.py
├── core/                      # Core utilities
│   ├── config.py             # Pydantic settings (env vars)
│   ├── security.py           # JWT auth, password hashing
│   └── exceptions.py         # Custom exception hierarchy
└── utils/
    └── data_loader.py        # Load course/assessment data on startup
```

**Data Flow:**
1. API layer validates requests (Pydantic schemas)
2. Service layer executes business logic, calls LLM
3. Repository layer accesses in-memory DB
4. Domain models contain business rules

**Key Design Patterns:**
- Repository pattern for data access
- Dependency injection via FastAPI `Depends()`
- Domain model ↔ DTO separation
- LLM provider abstraction (factory pattern)

### Frontend Structure

```
ai-teacher-frontend/src/
├── main.tsx                   # React entry point
├── App.tsx                    # Router setup, auth guard
├── pages/
│   ├── Login.tsx             # Login page
│   └── Learning.tsx          # Main learning interface
├── components/
│   ├── chat/                 # ChatList, ChatMessage, ChatInput
│   ├── whiteboard/           # Whiteboard (KaTeX formula rendering)
│   ├── progress/             # ProgressPanel (knowledge point tracking)
│   └── layout/               # Header
├── store/                     # Zustand state management
│   └── index.ts              # Auth, Course, Learning stores
├── api/
│   ├── client.ts             # Axios instance with interceptors
│   └── index.ts              # API method definitions
└── types/
    └── index.ts              # TypeScript type definitions
```

**State Management (Zustand):**
- `useAuthStore`: Token, user, login/logout
- `useCourseStore`: Current course, knowledge points
- `useLearningStore`: Session, messages, assessment mode, whiteboard

### Data Persistence

**MVP uses in-memory database with file persistence:**
- `ai-teacher-backend/data/students.json` - Student accounts & learning profiles
- `评估题库_一次函数.json` - Assessment questions (loaded on startup)
- Knowledge graph defined in `repositories/memory_db.py` (32 knowledge points, dependencies)

**On startup:** `app/main.py` lifespan handler loads course data and assessment questions.

## Key Workflows

### Learning Session Flow

1. **Start Session** → `POST /api/v1/learning/start`
   - Creates/resumes session for student + course
   - Determines current knowledge point (from profile or first KP)

2. **Get Teaching Content** → `POST /api/v1/learning/session/{id}/teach`
   - Calls `learning_service.generate_teaching_content()`
   - Builds prompt with KP info, attempt history, teaching requirements
   - LLM returns structured JSON: `{response_type, content, whiteboard, next_action}`

3. **Student Interaction** → `POST /api/v1/learning/session/{id}/chat`
   - Processes student messages (questions, answers)
   - Intent detection for "跳过", "开始测试"
   - LLM generates contextual responses

4. **Assessment** → `GET/POST /api/v1/learning/session/{id}/assessment`
   - Fetches questions for current KP
   - Evaluates answers against pass threshold
   - Updates learning record, student profile

5. **Backtrack** → `POST /api/v1/learning/session/{id}/backtrack`
   - Triggered on assessment failure
   - `backtrack_service.analyze_and_decide()` uses LLM to identify prerequisite gaps
   - Generates remedial content for target KP

### Knowledge Graph Traversal

- **Dependencies:** Each KP has `dependencies` list (prerequisite KPs)
- **Next KP Selection:** `course_service.get_next_knowledge_point()` finds first unmastered KP where all dependencies are satisfied
- **Levels:** KPs organized in 7 levels (0-6), but traversal respects dependency graph, not just level order

## Important Notes

### Backend Development

- **Follow rules.md:** SOLID principles, type annotations, Google-style docstrings, dependency injection
- **Layered architecture:** API → Service → Repository → Domain
- **Error handling:** Use custom exceptions from `core/exceptions.py`, global handler in `main.py`
- **LLM calls:** Always use `llm_service` abstraction, never call provider directly
- **Prompt engineering:** Prompts in `app/prompts/`, use structured JSON output from LLM

### Frontend Development

- **State management:** Use Zustand stores, avoid prop drilling
- **API calls:** Use typed API methods from `api/index.ts`
- **Formula rendering:** Use KaTeX for math formulas in whiteboard
- **Message deduplication:** Learning store prevents duplicate messages (React StrictMode issue)

### LLM Integration

- **Provider:** Zhipu AI GLM-4 (configurable via `LLM_PROVIDER` env var)
- **Structured output:** LLM returns JSON with specific schema (response_type, content, whiteboard, next_action)
- **Prompt templates:** Located in `app/prompts/`, use `.format()` for variable substitution
- **Fallback:** Service layer has fallback responses if LLM call fails

### Data Files

- **Student data:** Auto-saved to `ai-teacher-backend/data/students.json` on changes
- **Assessment questions:** Must exist at project root: `评估题库_一次函数.json`
- **Course data:** Hardcoded in `repositories/memory_db.py` and `utils/data_loader.py`

## Testing

No test suite currently exists. When adding tests:
- Backend: Use `pytest`, create fixtures for in-memory DB
- Frontend: Use Vitest + React Testing Library
- Follow test structure in `rules.md`

## API Documentation

Interactive API docs available at `http://localhost:8008/docs` when backend is running.

**Key endpoints:**
- `POST /api/v1/auth/register` - Register student
- `POST /api/v1/auth/login` - Login (returns JWT)
- `POST /api/v1/learning/start` - Start learning session
- `POST /api/v1/learning/session/{id}/teach` - Get teaching content
- `POST /api/v1/learning/session/{id}/chat` - Send message
- `GET /api/v1/learning/session/{id}/assessment` - Get assessment questions
- `POST /api/v1/learning/session/{id}/assessment` - Submit answers
- `GET /api/v1/learning/progress/{course_id}` - Get student progress
