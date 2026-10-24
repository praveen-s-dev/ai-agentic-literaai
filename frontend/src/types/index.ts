export type ResearchStage = 
  | 'planning'
  | 'searching'
  | 'filtering'
  | 'retrieving'
  | 'processing'
  | 'analyzing'
  | 'comparing'
  | 'verifying'
  | 'gap_discovery'
  | 'report_generation'
  | 'completed'
  | 'failed';

export interface ResearchSettings {
  sources: string[];
  max_papers: number;
  open_access_only: boolean;
  min_year: number;
  llm_provider?: string;
  llm_model?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}

export interface ResearchRequest {
  query: string;
  settings?: ResearchSettings;
  conversation_id?: number;
}

export interface ResearchTaskResponse {
  task_id: string;
  conversation_id: number;
  status: ResearchStage;
  message: string;
}

export interface ResearchProgress {
  task_id: string;
  current_stage: ResearchStage;
  stages: ResearchStage[];
  completed_stages: ResearchStage[];
  message: string;
  progress_percent: number;
  failed_sources: string[];
}

export interface Citation {
  title: string;
  authors: string[];
  year?: number;
  doi?: string;
  url?: string;
  source: string;
  citations: number;
}

export interface Author {
  id: number;
  name: string;
  affiliation?: string;
  orcid?: string;
}

export interface Paper {
  id: number;
  session_id: number;
  title: string;
  abstract?: string;
  source: string;
  source_id?: string;
  doi?: string;
  url?: string;
  publication_year?: number;
  venue?: string;
  citation_count: number;
  downloaded: number;
  processed: number;
  created_at: string;
  updated_at: string;
  authors: Author[];
}

export interface PaperListResponse {
  papers: Paper[];
  total: number;
}

export interface PaperAnalysis {
  id: number;
  paper_id: number;
  session_id: number;
  research_objective?: string;
  problem_addressed?: string;
  methodology?: string;
  algorithms_models?: string;
  datasets?: string;
  features?: string;
  experimental_setup?: string;
  results?: string;
  limitations?: string;
  future_work?: string;
  analysis_json: string;
  created_at: string;
  updated_at: string;
}

export interface PaperAnalysisListResponse {
  analyses: PaperAnalysis[];
  total: number;
}

export type GapStatus = 'candidate' | 'validated' | 'rejected';

export interface ResearchGap {
  id: number;
  session_id: number;
  title: string;
  description: string;
  gap_type?: string;
  confidence_score: number;
  supporting_evidence_ids?: string;
  created_at: string;
  updated_at: string;
  gap_statement?: string;
  supporting_papers?: string;
  supporting_evidence?: string;
  repeated_limitation?: string;
  why_existing_work_insufficient?: string;
  potential_research_direction?: string;
  confidence_evidence_strength: number;
  gap_status: GapStatus;
  evidence_strength: number;
}

export interface ResearchGapListResponse {
  gaps: ResearchGap[];
  total: number;
}

export interface ResearchGapUpdate {
  gap_status?: GapStatus;
  title?: string;
  description?: string;
  gap_statement?: string;
  potential_research_direction?: string;
}

export type EvidenceStatus = 
  | 'supported' 
  | 'partially_supported' 
  | 'not_supported' 
  | 'insufficient_evidence' 
  | 'conflicting';

export interface EvidenceRecord {
  id: number;
  session_id: number;
  paper_id: number;
  claim: string;
  evidence_text?: string;
  page_number?: number;
  chunk_id?: string;
  status: EvidenceStatus;
  confidence_score: number;
  relevance_score: number;
  verified_by?: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceRecordListResponse {
  records: EvidenceRecord[];
  total: number;
}

export interface ReportResponse {
  session_id: number;
  report: string;
  generated_at: string;
  metadata: Record<string, any>;
}

export interface SessionDetail {
  id: number;
  research_question: string;
  status: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
  papers: Paper[];
  analyses: PaperAnalysis[];
  gaps: ResearchGap[];
  evidence_records: EvidenceRecord[];
  report?: string;
}

export interface ResearchResult {
  task_id: string;
  conversation_id: number;
  status: ResearchStage;
  content: string;
  citations: Citation[];
  papers: Paper[];
  report?: string;
  metadata: Record<string, any>;
  error?: string;
  completed_at?: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  session_id?: number;
  message_count: number;
}

export interface ConversationCreate {
  title: string;
}

export interface ConversationUpdate {
  title?: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

export interface Message {
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
}

export interface ErrorResponse {
  detail: string;
  code?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  vector_db: string;
  llm_provider: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
  paper_ids?: number[];
  use_rag?: boolean;
  temperature?: number;
}

export interface ChatResponse {
  response: string;
  evidence: Array<{
    chunk_id: string;
    paper_id: number;
    title: string;
    page: number;
    similarity: number;
  }>;
  conversation_id?: number;
}