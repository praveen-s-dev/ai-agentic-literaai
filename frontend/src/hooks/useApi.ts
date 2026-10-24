import { useState, useEffect, useCallback, useRef } from 'react';
import { api, ApiError } from '../services/api';
import type { 
  Conversation, 
  ResearchTaskResponse, 
  ResearchProgress, 
  ResearchResult, 
  ResearchRequest, 
  Citation, 
  Paper,
  ResearchStage,
  PaperAnalysis,
  ResearchGap,
  EvidenceRecord,
  SessionDetail,
  ChatRequest,
} from '../types';

// Hook for managing conversations
export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.conversations.list();
      setConversations(data.conversations);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const createConversation = async (title: string) => {
    const conv = await api.conversations.create({ title });
    setConversations(prev => [conv, ...prev]);
    return conv;
  };

  const updateConversation = async (id: number, title: string) => {
    const conv = await api.conversations.update(id, { title });
    setConversations(prev => prev.map(c => c.id === id ? conv : c));
    return conv;
  };

  const deleteConversation = async (id: number) => {
    await api.conversations.delete(id);
    setConversations(prev => prev.filter(c => c.id !== id));
  };

  return {
    conversations,
    loading,
    error,
    refetch: fetchConversations,
    createConversation,
    updateConversation,
    deleteConversation,
  };
}

// Hook for managing session detail data
export function useSessionDetail(sessionId: number | null) {
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessionDetail = useCallback(async () => {
    if (!sessionId) {
      setSessionDetail(null);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getDetail(sessionId);
      setSessionDetail(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load session detail');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSessionDetail();
  }, [fetchSessionDetail]);

  return {
    sessionDetail,
    loading,
    error,
    refetch: fetchSessionDetail,
  };
}

// Hook for managing papers
export function usePapers(sessionId: number | null) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchPapers = useCallback(async () => {
    if (!sessionId) {
      setPapers([]);
      setTotal(0);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getPapers(sessionId);
      setPapers(data.papers);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load papers');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  return {
    papers,
    loading,
    error,
    total,
    refetch: fetchPapers,
  };
}

// Hook for managing analyses
export function useAnalyses(sessionId: number | null) {
  const [analyses, setAnalyses] = useState<PaperAnalysis[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchAnalyses = useCallback(async () => {
    if (!sessionId) {
      setAnalyses([]);
      setTotal(0);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getAnalyses(sessionId);
      setAnalyses(data.analyses);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load analyses');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchAnalyses();
  }, [fetchAnalyses]);

  return {
    analyses,
    loading,
    error,
    total,
    refetch: fetchAnalyses,
  };
}

// Hook for managing research gaps
export function useGaps(sessionId: number | null, status?: string) {
  const [gaps, setGaps] = useState<ResearchGap[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchGaps = useCallback(async () => {
    if (!sessionId) {
      setGaps([]);
      setTotal(0);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getGaps(sessionId, 0, 50, status);
      setGaps(data.gaps);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load gaps');
    } finally {
      setLoading(false);
    }
  }, [sessionId, status]);

  useEffect(() => {
    fetchGaps();
  }, [fetchGaps]);

  const updateGap = async (gapId: number, data: { gap_status?: 'candidate' | 'validated' | 'rejected'; title?: string; description?: string; gap_statement?: string; potential_research_direction?: string }) => {
    if (!sessionId) return;
    const updated = await api.sessions.updateGap(sessionId, gapId, data);
    setGaps(prev => prev.map(g => g.id === gapId ? updated : g));
    return updated;
  };

  return {
    gaps,
    loading,
    error,
    total,
    refetch: fetchGaps,
    updateGap,
  };
}

// Hook for managing evidence records
export function useEvidence(sessionId: number | null, status?: string) {
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchEvidence = useCallback(async () => {
    if (!sessionId) {
      setEvidence([]);
      setTotal(0);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getEvidence(sessionId, 0, 50, status);
      setEvidence(data.records);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load evidence');
    } finally {
      setLoading(false);
    }
  }, [sessionId, status]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  return {
    evidence,
    loading,
    error,
    total,
    refetch: fetchEvidence,
  };
}

// Hook for managing reports
export function useReport(sessionId: number | null) {
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    if (!sessionId) {
      setReport(null);
      return;
    }
    try {
      setLoading(true);
      const data = await api.sessions.getReport(sessionId);
      setReport(data.report);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Failed to load report');
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  return {
    report,
    loading,
    error,
    refetch: fetchReport,
  };
}

// Hook for managing research workflow
export function useResearch() {
  const [task, setTask] = useState<ResearchTaskResponse | null>(null);
  const [progress, setProgress] = useState<ResearchProgress | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const taskIdRef = useRef<string | null>(null);

  const startResearch = async (request: ResearchRequest): Promise<ResearchTaskResponse | null> => {
    try {
      setError(null);
      setResult(null);
      setProgress(null);
      const task = await api.research.start(request);
      setTask(task);
      return task;
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.detail : 'Failed to start research';
      setError(errorMsg);
      return null;
    }
  };

  const pollStatus = useCallback(async (taskId: string) => {
    try {
      const progress = await api.research.status(taskId);
      setProgress(progress);
      
      if (progress.current_stage === 'completed' || progress.current_stage === 'failed') {
        setPolling(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        // Only fetch result if task has a result (not cancelled)
        // Check if task has a result by trying to fetch, but handle 400 gracefully
        try {
          const result = await api.research.result(taskId);
          setResult(result);
          if (progress.current_stage === 'failed') {
            setError(result.error || 'Research failed');
          }
        } catch (resultErr: any) {
          // If 400 "not yet completed" or "no result", it might be cancelled
          if (resultErr.status === 400 && (resultErr.detail?.includes('not yet completed') || resultErr.detail?.includes('not found'))) {
            // Task was likely cancelled - don't set error, just clear result
            setResult(null);
          } else {
            console.error('Failed to fetch result:', resultErr);
            setError('Failed to retrieve research result');
          }
        }
      }
    } catch (err) {
      console.error('Polling error:', err);
      setPolling(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setError(err instanceof ApiError ? err.detail : 'Polling failed - connection lost');
    }
  }, []);

  const startPolling = useCallback((taskId: string) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    taskIdRef.current = taskId;
    setPolling(true);
    setError(null);
    intervalRef.current = setInterval(() => pollStatus(taskId), 1500);
  }, [pollStatus]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    taskIdRef.current = null;
    setPolling(false);
  }, []);

  const stopResearch = useCallback(async (onStopComplete?: () => void) => {
    const taskId = taskIdRef.current;
    if (taskId) {
      try {
        // Try to cancel on backend
        await fetch(`/api/research/${taskId}`, { method: 'DELETE' });
      } catch (e) {
        console.error('Failed to cancel research on backend:', e);
      }
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    taskIdRef.current = null;
    setPolling(false);
    setResult(null);
    setProgress(null);
    setTask(null);
    setError('Research stopped by user');
    onStopComplete?.();
  }, []);

  const reset = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    taskIdRef.current = null;
    setTask(null);
    setProgress(null);
    setResult(null);
    setPolling(false);
    setError(null);
  }, []);

  return {
    task,
    progress,
    result,
    polling,
    error,
    startResearch,
    startPolling,
    stopPolling,
    stopResearch,
    reset,
  };
}

// Hook for managing chat
export function useChat() {
  const [messages, setMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    citations?: Citation[];
    papers?: Paper[];
    report?: string;
    metadata?: Record<string, any>;
    current_stage?: ResearchStage;
    is_typing?: boolean;
    error?: string;
  }>>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversationIdRef = useRef<number | null>(null);

  // Load messages from localStorage for a conversation
  const loadMessages = useCallback((conversationId: number) => {
    try {
      const stored = localStorage.getItem(`chat_messages_${conversationId}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        setMessages(parsed);
        return true;
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
    setMessages([]);
    return false;
  }, []);

  // Save messages to localStorage for a conversation
  const saveMessages = useCallback((conversationId: number, msgs: typeof messages) => {
    try {
      localStorage.setItem(`chat_messages_${conversationId}`, JSON.stringify(msgs));
    } catch (e) {
      console.error('Failed to save chat history:', e);
    }
  }, []);

  // Save research result message specifically
  const saveResearchResult = useCallback((conversationId: number, researchResultMessage: any) => {
    try {
      const stored = localStorage.getItem(`chat_messages_${conversationId}`);
      let messages: any[] = [];
      if (stored) {
        messages = JSON.parse(stored);
      }
      // Remove any existing research result message
      messages = messages.filter((m: any) => !(m.metadata?.papers_found && m.role === 'assistant'));
      // Add the new research result message
      messages.push(researchResultMessage);
      localStorage.setItem(`chat_messages_${conversationId}`, JSON.stringify(messages));
    } catch (e) {
      console.error('Failed to save research result:', e);
    }
  }, []);

  // Get research result message for a conversation
  const getResearchResult = useCallback((conversationId: number) => {
    try {
      const stored = localStorage.getItem(`chat_messages_${conversationId}`);
      if (stored) {
        const messages = JSON.parse(stored);
        return messages.find((m: any) => m.metadata?.papers_found && m.role === 'assistant');
      }
    } catch (e) {
      console.error('Failed to get research result:', e);
    }
    return null;
  }, []);

  const sendMessage = async (content: string, isResearch: boolean = false) => {
    if (!content.trim()) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user' as const,
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => {
      const updated = [...prev, userMessage];
      if (conversationIdRef.current) {
        saveMessages(conversationIdRef.current, updated);
      }
      return updated;
    });

    if (isResearch) {
      return;
    } else {
      // Use chat API for regular chat
      try {
        setIsGenerating(true);
        setError(null);
        const request: ChatRequest = {
          message: content,
          use_rag: false,
          temperature: 0.7,
        };
        const response = await api.chat.send(request);
        
        const assistantMessage = {
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: response.response,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => {
          const updated = [...prev, assistantMessage];
          if (conversationIdRef.current) {
            saveMessages(conversationIdRef.current, updated);
          }
          return updated;
        });
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to get response';
        setError(errorMsg);
        
        const errorMessage = {
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: `Error: ${errorMsg}`,
          timestamp: new Date().toISOString(),
          error: errorMsg,
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsGenerating(false);
      }
    }
  };

  // Set the current conversation ID for persistence
  const setConversationId = useCallback((conversationId: number | null) => {
    conversationIdRef.current = conversationId;
    if (conversationId) {
      loadMessages(conversationId);
    }
  }, [loadMessages]);

  return {
    messages,
    setMessages,
    isGenerating,
    error,
    sendMessage,
    setConversationId,
    saveResearchResult,
    getResearchResult,
  };
}

// Hook for debouncing
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Hook for localStorage persistence
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue] as const;
}