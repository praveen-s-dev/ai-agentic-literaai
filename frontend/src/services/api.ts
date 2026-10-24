import type { 
  Conversation, 
  ConversationCreate, 
  ConversationUpdate, 
  ResearchRequest, 
  ResearchTaskResponse, 
  ResearchProgress, 
  ResearchResult, 
  ResearchSettings, 
  ResearchStage, 
  Citation, 
  Paper, 
  PaperListResponse,
  PaperAnalysis,
  PaperAnalysisListResponse,
  ResearchGap,
  ResearchGapListResponse,
  ResearchGapUpdate,
  EvidenceRecord,
  EvidenceRecordListResponse,
  ReportResponse,
  SessionDetail,
  HealthResponse,
  ConversationListResponse,
  ChatRequest,
  ChatResponse,
} from '../types';

const API_BASE = '/api';

type RequestOptions = {
  method: string;
  body: string;
  headers: Record<string, string>;
  params: Record<string, string>;
};

class ApiError extends Error {
  status: number;
  detail: string;
  code?: string;
  
  constructor(status: number, detail: string, code?: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
    this.code = code;
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  const optionsWithDefaults: RequestOptions = options || { method: 'GET', body: '', headers: {}, params: {} };
  const { params, method, body, headers } = optionsWithDefaults;
  
  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    url += `?${searchParams.toString()}`;
  }

  const isGetOrHead = method === 'GET' || method === 'HEAD';
  
  const response = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: isGetOrHead ? undefined : body,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP error ${response.status}`,
      errorData.code
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  conversations: {
    list: () => request<ConversationListResponse>('/conversations', {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
    create: (data: ConversationCreate) => request<Conversation>('/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {},
      params: {},
    }),
    get: (id: number) => request<Conversation>(`/conversations/${id}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
    update: (id: number, data: ConversationUpdate) => request<Conversation>(`/conversations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: {},
      params: {},
    }),
    delete: (id: number) => request<void>(`/conversations/${id}`, {
      method: 'DELETE',
      body: '',
      headers: {},
      params: {},
    }),
  },

  research: {
    start: (data: ResearchRequest) => request<ResearchTaskResponse>('/research', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {},
      params: {},
    }),
    status: (taskId: string) => request<ResearchProgress>(`/research/${taskId}/status`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
    result: (taskId: string) => request<ResearchResult>(`/research/${taskId}/result`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
  },

  sessions: {
    // Full session detail with all related data
    getDetail: (sessionId: number) => request<SessionDetail>(`/sessions/${sessionId}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),

    // Papers
    getPapers: (sessionId: number, skip = 0, limit = 50) => request<PaperListResponse>(`/sessions/${sessionId}/papers`, {
      method: 'GET',
      body: '',
      headers: {},
      params: { skip: String(skip), limit: String(limit) },
    }),
    getPaper: (sessionId: number, paperId: number) => request<Paper>(`/sessions/${sessionId}/papers/${paperId}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),

    // Analyses
    getAnalyses: (sessionId: number, skip = 0, limit = 50) => request<PaperAnalysisListResponse>(`/sessions/${sessionId}/analyses`, {
      method: 'GET',
      body: '',
      headers: {},
      params: { skip: String(skip), limit: String(limit) },
    }),
    getAnalysis: (sessionId: number, analysisId: number) => request<PaperAnalysis>(`/sessions/${sessionId}/analyses/${analysisId}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),

    // Research Gaps
    getGaps: (sessionId: number, skip = 0, limit = 50, status?: string) => request<ResearchGapListResponse>(`/sessions/${sessionId}/gaps`, {
      method: 'GET',
      body: '',
      headers: {},
      params: { skip: String(skip), limit: String(limit), ...(status ? { status } : {}) },
    }),
    getGap: (sessionId: number, gapId: number) => request<ResearchGap>(`/sessions/${sessionId}/gaps/${gapId}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
    updateGap: (sessionId: number, gapId: number, data: ResearchGapUpdate) => request<ResearchGap>(`/sessions/${sessionId}/gaps/${gapId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: {},
      params: {},
    }),

    // Evidence Records
    getEvidence: (sessionId: number, skip = 0, limit = 50, status?: string) => request<EvidenceRecordListResponse>(`/sessions/${sessionId}/evidence`, {
      method: 'GET',
      body: '',
      headers: {},
      params: { skip: String(skip), limit: String(limit), ...(status ? { status } : {}) },
    }),
    getEvidenceRecord: (sessionId: number, evidenceId: number) => request<EvidenceRecord>(`/sessions/${sessionId}/evidence/${evidenceId}`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),

    // Report
    getReport: (sessionId: number) => request<ReportResponse>(`/sessions/${sessionId}/report`, {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
  },

  chat: {
    send: (data: ChatRequest) => request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: {},
      params: {},
    }),
  },

  health: {
    check: () => request<HealthResponse>('/health', {
      method: 'GET',
      body: '',
      headers: {},
      params: {},
    }),
  },
};

export { ApiError };

// Re-export types for convenience
export type {
  Conversation,
  ConversationCreate,
  ConversationUpdate,
  ResearchRequest,
  ResearchTaskResponse,
  ResearchProgress,
  ResearchResult,
  ResearchSettings,
  ResearchStage,
  Citation,
  Paper,
  PaperListResponse,
  PaperAnalysis,
  PaperAnalysisListResponse,
  ResearchGap,
  ResearchGapListResponse,
  ResearchGapUpdate,
  EvidenceRecord,
  EvidenceRecordListResponse,
  ReportResponse,
  SessionDetail,
  HealthResponse,
  ConversationListResponse,
  ChatRequest,
  ChatResponse,
};