import { create } from 'zustand';

interface RagMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface AppState {
  // Document Context
  pdfFile: File | null;
  pdfText: string | null;
  pdfName: string | null;
  pdfPages: number;
  pdfSizeKb: number;
  
  // RAG Context
  ragHistory: RagMessage[];
  ragSteps: string[];
  
  // Trend Context
  trendResults: any | null;
  trendInsights: string | null;
  
  // Navigation
  currentPage: 'upload' | 'rag' | 'trend';

  // Actions
  setPdfData: (data: Partial<AppState>) => void;
  addRagMessage: (msg: RagMessage) => void;
  setPage: (page: 'upload' | 'rag' | 'trend') => void;
  resetApp: () => void;
}

const initialState = {
  pdfFile: null,
  pdfText: null,
  pdfName: null,
  pdfPages: 0,
  pdfSizeKb: 0,
  ragHistory: [],
  ragSteps: [],
  trendResults: null,
  trendInsights: null,
  currentPage: 'upload' as const,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,
  
  setPdfData: (data) => set((state) => ({ ...state, ...data })),
  
  addRagMessage: (msg) => set((state) => ({ 
    ragHistory: [...state.ragHistory, msg] 
  })),
  
  setPage: (page) => set({ currentPage: page }),
  
  resetApp: () => set(initialState),
}));
