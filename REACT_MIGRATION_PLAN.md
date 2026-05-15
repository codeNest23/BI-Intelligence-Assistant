# React Migration Plan: PDF Intelligence Hub

This document outlines the step-by-step implementation plan to migrate the existing Streamlit frontend to a modern React architecture. It focuses on clean component separation, layout and UI improvements, and integrating `recharts` for data visualization.

## 1. Architectural Overview

Since Streamlit tightly couples the frontend and backend, the migration requires splitting the app into a discrete frontend and backend:
*   **Frontend:** React 18+ (using Vite or Next.js), TypeScript, CSS Modules or Tailwind CSS.
*   **Backend:** Refactor the existing Python codebase (agents, pinecone integrations) into a FastAPI application that serves REST endpoints.
*   **State Management:** Context API or Zustand to replace Streamlit's `st.session_state`.
*   **Routing:** React Router v6.
*   **Charting:** Recharts.

---

## 2. Component Module Separation

The frontend will be broken down into atomic, reusable components housed in the `src/` directory.

### Directory Structure
```text
src/
├── assets/                 # Images, icons, custom fonts (Outfit, JetBrains Mono)
├── components/
│   ├── layout/             # Shell components (Sidebar, TopNav, AppLayout)
│   ├── ui/                 # Reusable dumb components (Button, Card, Input, ChatBubble, Spinner)
│   ├── charts/             # Recharts wrapper components
│   └── domain/             # Feature-specific components (PdfUploader, RagChat, TrendDashboard)
├── context/                # Global state (PdfContext, ThemeContext)
├── hooks/                  # Custom hooks (usePdfUpload, useRagChat, useTrendAnalysis)
├── pages/                  # Page-level components
│   ├── UploadPage.tsx
│   ├── RagPage.tsx
│   └── TrendPage.tsx
├── services/               # Axios/Fetch API clients communicating with FastAPI
└── App.tsx                 # App router & context providers
```

### Key Component Modules

1.  **Layout Components (`src/components/layout/`)**
    *   `AppLayout`: The main wrapper containing the Sidebar and the dynamic page content area.
    *   `Sidebar`: Navigation menu replacing `render_sidebar()`. Includes active state highlights, hover animations, and the "Active Document" status widget.

2.  **UI Components (`src/components/ui/`)**
    *   `GlassCard`: A wrapper component applying the `backdrop-filter` and card shadows seen in the Streamlit CSS.
    *   `ChatBubble`: Dedicated components for `UserBubble` and `BotBubble` with distinct gradients and typography.
    *   `MetricCard`: Reusable component to display metrics (e.g., PDF size, total pages, sentiment score).

3.  **Chart Components (`src/components/charts/`)**
    *   *Wrappers around `recharts` to standardize styling, tooltips, and responsiveness.*
    *   `KeywordTrendChart`: Uses `<LineChart>` to display multi-keyword frequency.
    *   `SentimentArcChart`: Uses `<AreaChart>` or `<LineChart>` to show document sentiment progression.
    *   `TopicBarChart`: Uses `<BarChart>` (horizontal layout) to show TF-IDF topics.

---

## 3. UI/UX and Layout Improvements

*   **Responsive Grid/Flexbox Layouts:**
    Replace Streamlit's implicit layout with explicit CSS Grid/Flexbox. The main content area will center cards and restrict maximum width (e.g., `max-w-7xl`) for better readability on ultra-wide monitors.
*   **Smooth Transitions:**
    Add CSS transitions for routing, hover states on sidebar items, and dynamic loading states (skeleton loaders) instead of Streamlit's full-page re-runs.
*   **Design System Fidelity:**
    Extract the `--primary`, `--secondary`, `--bg-main`, and `--sidebar-bg` CSS variables directly into Tailwind config or a global CSS file. Ensure the *Outfit* and *JetBrains Mono* fonts are applied correctly across all text elements.

---

## 4. Recharts Implementation Details

The current Python `trend_agent.py` returns generic JSON charting definitions. The React frontend will map these payloads to `recharts` components.

### Example: Transforming the Keyword Frequency Chart
```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export function KeywordTrendChart({ data, keywords }) {
  // data format: [ { page: 'P1', risk: 2, growth: 5 }, { page: 'P2', risk: 0, growth: 3 } ]
  return (
    <div className="glass-card h-96 w-full">
      <h3 className="text-xl font-bold mb-4">Keyword Frequency Over Pages</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
          <XAxis dataKey="page" />
          <YAxis />
          <Tooltip contentStyle={{ borderRadius: '12px', background: 'var(--card-bg)' }} />
          <Legend />
          {keywords.map((kw, index) => (
            <Line 
              key={kw} 
              type="monotone" 
              dataKey={kw} 
              stroke={`var(--chart-color-${index})`} 
              strokeWidth={3} 
              dot={{ r: 4 }} 
              activeDot={{ r: 6 }} 
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

## 5. State Management Migration

Streamlit's `st.session_state` must be replaced by a React state solution. We will use **Zustand** (or Context) for lightweight global state.

```ts
import create from 'zustand';

interface AppState {
  // Document Context
  pdfFile: File | null;
  pdfText: string | null;
  pdfName: string | null;
  pdfPages: number;
  
  // RAG Context
  ragHistory: Array<{ role: 'user' | 'assistant', content: string }>;
  ragSteps: string[];
  
  // Trend Context
  trendResults: any | null;
  trendInsights: string | null;
  
  // Actions
  setPdfData: (data: Partial<AppState>) => void;
  addRagMessage: (msg: { role: 'user' | 'assistant', content: string }) => void;
}

export const useAppStore = create<AppState>((set) => ({
  pdfFile: null,
  pdfText: null,
  pdfName: null,
  pdfPages: 0,
  ragHistory: [],
  ragSteps: [],
  trendResults: null,
  trendInsights: null,
  
  setPdfData: (data) => set((state) => ({ ...state, ...data })),
  addRagMessage: (msg) => set((state) => ({ ragHistory: [...state.ragHistory, msg] })),
}));
```

---

## 6. Migration Steps & Milestones

1.  **Phase 1: Project Scaffolding & Design System (Frontend)**
    *   Initialize Vite + React + TS.
    *   Set up global CSS variables matching the Streamlit `st.markdown` block.
    *   Build base `Layout` and `Sidebar` components.
2.  **Phase 2: Backend API Creation (Python/FastAPI)**
    *   Wrap `app.py` logic into FastAPI endpoints:
        *   `POST /api/upload` (Extracts text, indexes to Pinecone)
        *   `POST /api/rag/chat` (Handles OpenRouter LLM interactions & tool calls)
        *   `POST /api/trend/analyze` (Runs the TrendAgent)
3.  **Phase 3: Building Pages & Integration**
    *   **Upload Page:** Implement Drag-and-Drop file uploader UI. Connect to `/api/upload`. Update Zustand state.
    *   **RAG Page:** Implement the chat interface (`ChatBubble`, text input). Connect to `/api/rag/chat`.
    *   **Trend Page:** Build the dashboard layout. Map API JSON responses to `recharts` components.
4.  **Phase 4: Polish & Refinement**
    *   Add loading spinners, toast notifications, and error boundary wrappers.
    *   Ensure animations and transitions are buttery smooth.
    *   Test responsive design across screen sizes.
