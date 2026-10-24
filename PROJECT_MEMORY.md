# Project Memory

## Current Stage
Stage 8 - ChatGPT-Style UI Redesign Complete (Enhanced with Phase 2 Improvements)

## Project Goal
Build an evidence-grounded autonomous research assistant that can:
Research Question -> Research Planning -> Academic Paper Retrieval -> Paper Processing -> RAG-based Analysis -> Cross-Paper Comparison -> Evidence Verification -> Research Gap Discovery -> Structured Research Report

## Architecture
- app/ - Main application entry point, configuration, logging, and Streamlit pages (chat_app.py for ChatGPT-style conversational UI - primary entry point; streamlit_app.py, search_page.py, analysis_page.py, comparison_page.py, report_page.py deprecated legacy pages)
- frontend/ - React + TypeScript + Vite frontend (ChatWorkspace, Sidebar, MessageList, MessageComposer, WelcomeScreen components)
- agents/ - Autonomous research agents
- academic/ - Academic API integrations
- papers/ - Paper processing and management
- rag/ - Retrieval-augmented generation pipeline
- evidence/ - Evidence extraction and verification
- reports/ - Research report generation
- database/ - SQLite database with SQLAlchemy ORM models
- evaluation/ - Evaluation framework
- reproducibility/ - Experiment tracking
- tests/ - Pytest configuration and test suites
- data/ - Data storage
- logs/ - Application logs

## Implemented Features (All Stages Complete)
1. Clean Python project structure with modular design
2. Environment management using .env file with pydantic-settings
3. Configuration validation for all settings
4. SQLite database with SQLAlchemy 2.0 ORM
5. Database models: ResearchSession, Paper, Author, PaperAuthor, Evidence, ResearchGap, PaperChunk, PaperAnalysis, EvidenceRecord
6. Database connection management with session context manager
9. Basic pytest configuration with fixtures
10. Common paper schema (Paper, Author, SearchResult Pydantic models)
11. Four academic API clients: OpenAlex, Semantic Scholar, Crossref, arXiv
12. Rate limiting (configurable per source)
13. Caching (file-based with TTL)
14. Retry logic with exponential backoff
15. Search agent with multi-source search, DOI/title deduplication, relevance ranking
16. Open access detection and filtering
17. Paper metadata storage in SQLite with author relationships
18. Streamlit search interface with source selection, open access filter, session saving
19. PDF Downloader - Validates PDF URLs, handles timeouts/errors, validates file type, safe filenames, prevents duplicate downloads
20. PDF Processor - Extracts text with PyMuPDF preserving page numbers, document metadata, detects extraction failures, safe text cleaning
21. Text Chunker - Chunks text with configurable size/overlap, preserves page numbers, generates unique chunk IDs for traceability
22. Chunk Storage - Stores chunks in database with paper_id, page_number, chunk_id, text, char positions, word/char counts
24. Embedding Generation - sentence-transformers (BGE-small-en-v1.5), configurable model, batch processing
25. Vector Database - ChromaDB with cosine similarity, persistent storage, metadata filtering
26. Semantic Retrieval - Top-k retrieval, paper filtering, similarity thresholding
27. RAG Pipeline - NVIDIA Nemotron-3-Ultra LLM integration (configurable model), structured prompt engineering
28. Paper Analysis Agent - Extracts 10 structured fields with evidence citations, distinguishes FACT/INFERENCE/UNKNOWN
29. Analysis Storage - Stores analysis results in SQLite with structured fields
30. Streamlit Analysis UI - Full paper analysis, Q&A over papers, evidence display, vector index rebuild
31. EvidenceRecord Model - Stores verified claims with status (SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, INSUFFICIENT_EVIDENCE, CONFLICTING)
32. Citation Tracker - Manages evidence records with CRUD operations, conflict detection, session statistics
33. Evidence Verifier - Verifies claims against paper corpus using RAG, assigns evidence status
34. Cross-Paper Agent - Compares papers across 10 fields, detects conflicts, finds commonalities
35. Conflict Detection - Identifies contradictions, methodological differences, metric disagreements
36. Streamlit Comparison UI - Multi-paper comparison, claim verification, citation tracking, statistics
37. ResearchGap Model - Enhanced with gap_statement, supporting_papers, supporting_evidence, repeated_limitation, why_existing_work_insufficient, potential_research_direction, confidence_evidence_strength, gap_status, evidence_strength
38. Research Gap Agent - Discovers candidate gaps from repeated limitations, missing evaluations, contradictions, methodological weaknesses, missing validation, future work suggestions
39. Evidence-Grounded Gap Discovery - Every gap has supporting papers, evidence, and traceable reasoning
40. Report Generator - Generates structured Markdown reports with all sections
41. Streamlit Report UI - Gap discovery, report generation, stored gaps view, gap validation, report download
42. Evaluation Framework - Retrieval, citation, evidence, extraction, comparison, gap, hallucination metrics
43. Benchmark Dataset - 8 manually curated benchmark items with expected answers/evidence
44. Baseline Comparisons - Standard LLM, Single-Doc RAG, Multi-Stage Workflow
45. Custom Exception Classes - Academic, paper processing, evidence, chunking exceptions
46. Reproducibility Tracker - Experiment config tracking, run logging, export/import
47. Enhanced Logging - Structured JSONL logs for experiments, reproducibility tracking
48. Unified Streamlit App - 9-page unified application (Home, Research, Papers, Analysis, Evidence, Comparison, Gaps, Report, Status)
49. Error Handling - Custom exceptions for academic APIs, PDF processing, evidence, chunking
48. Comprehensive Test Suite - 102 tests (99 passed, 3 skipped)
49. ChatGPT-Style Conversational UI - Collapsible sidebar with conversation history, welcome screen with suggestion cards, chat interface with markdown rendering, progress indicators, citation display, paper explorer, report download actions
49. NVIDIA Nemotron-3-Ultra LLM Integration - Replaced Ollama with NVIDIA API for cloud-based inference
50. Abstract-based Chunk Fallback - Creates vector store chunks from paper abstracts when PDFs unavailable
51. Vector Store Integration - Fixed save_chunks_to_paper to also populate ChromaDB with embeddings
52. Fixed Paper ID Mapping - Resolved source-specific ID to database ID mapping for analysis workflow
53. Fixed Detached Instance Errors - Resolved SQLAlchemy detached instance issues in analysis agents
54. Fixed Report Generator Author Handling - Properly accesses author names through PaperAuthor relationship

## Directory Structure
E:\aiml\researchagent\
app/
  main.py, search_page.py, analysis_page.py, comparison_page.py, report_page.py, streamlit_app.py, config.py, logging_config.py, chat_app.py
frontend/
  src/
    components/ - ChatWorkspace.tsx, Sidebar.tsx, MessageList.tsx, MessageComposer.tsx, WelcomeScreen.tsx, UserMessage.tsx, AssistantMessage.tsx, TypingIndicator.tsx, ResearchStatus.tsx
    hooks/ - useApi.ts
    services/ - api.ts
    types/ - index.ts, researchStages.ts
    styles/ - ChatWorkspace.css
    main.tsx, App.tsx
  package.json, vite.config.ts, tsconfig.json
agents/ - search_agent.py, paper_analysis_agent.py, cross_paper_agent.py, research_gap_agent.py
academic/ - schemas.py, base_client.py, openalex_client.py, semantic_scholar_client.py, crossref_client.py, arxiv_client.py
papers/ - storage.py, downloader.py, pdf_processor.py, chunker.py, exceptions.py
rag/ - embeddings.py, vector_store.py, retriever.py, rag_pipeline.py
evidence/ - citation_tracker.py, verifier.py, exceptions.py
reports/ - report_generator.py
database/ - connection.py, models.py
evaluation/ - metrics.py, benchmark.py, baselines.py
reproducibility/ - reproducibility.py
tests/ - test_config.py, test_database.py, test_academic_clients.py, test_paper_processing.py, test_rag.py, test_evidence.py, test_research_gap.py, test_evaluation.py
data/ - papers/, processed/, cache/, vector_db/, research.db
logs/ - app.log, error.log, experiments.jsonl, reproducibility.jsonl
venv/, .env.example, .gitignore, requirements.txt, pytest.ini, README.md, PROJECT_MEMORY.md

## Dependencies
### Backend (Python)
Core: streamlit, python-dotenv, pydantic, pydantic-settings
Database: sqlalchemy, alembic
LLM: ollama, openai (for NVIDIA API)
Academic APIs: httpx
Data Processing: pandas, numpy
PDF Processing: pymupdf
RAG/Vector Database: chromadb, sentence-transformers
Logging: loguru
Testing: pytest, pytest-asyncio, pytest-cov
Type Checking: mypy, types-requests
Utilities: rich, typer

### Frontend (React + TypeScript)
Core: react, react-dom, typescript, vite
UI: Custom CSS (ChatGPT-style design system)
HTTP: Custom API client (fetch-based)
State: React hooks (useState, useEffect, custom hooks)

## Environment Variables
LLM_PROVIDER=nvidia, OLLAMA_BASE_URL=http://localhost:11434, OLLAMA_MODEL=llama3.2, NVIDIA_API_KEY=..., NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1, NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b, OPENALEX_API_KEY=qV6Ljrj1BbUgs3frCFPq5n, SEMANTIC_SCHOLAR_API_KEY=, DATABASE_URL=sqlite:///data/research.db, VECTOR_DB_PATH=data/vector_db, APP_HOST=0.0.0.0, APP_PORT=8501, LOG_LEVEL=INFO, EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

## Database Schema
research_sessions, papers, authors, paper_authors, evidence, research_gaps, paper_chunks, paper_analyses, evidence_records

## Evidence Verification Statuses
SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, INSUFFICIENT_EVIDENCE, CONFLICTING

## Cross-Paper Comparison Fields (10)
research_objective, problem_addressed, methodology, algorithms_models, datasets, features, experimental_setup, results, limitations, future_work

## Conflict Types
contradiction, metric_contradiction, methodological_difference, dataset_difference, approach_difference

## Phase 2 Files Modified
### Backend (Streamlit)
- app/chat_app.py (major UI overhaul)
- rag/rag_pipeline.py (streaming support)
- README.md (updated entry point)
- PROJECT_MEMORY.md (updated documentation)

### Frontend (React + TypeScript)
- frontend/src/components/ChatWorkspace.tsx
- frontend/src/components/WelcomeScreen.tsx
- frontend/src/components/MessageComposer.tsx
- frontend/src/components/MessageList.tsx
- frontend/src/components/ResearchStatus.tsx
- frontend/src/components/Sidebar.tsx
- frontend/src/components/TypingIndicator.tsx
- frontend/src/components/UserMessage.tsx
- frontend/src/components/AssistantMessage.tsx
- frontend/src/hooks/useApi.ts
- frontend/src/services/api.ts
- frontend/src/types/index.ts
- frontend/src/types/researchStages.ts
- frontend/src/styles/ChatWorkspace.css

## Phase 2 Improvements (UI Enhancement)
### Streamlit Backend (chat_app.py)
- Fixed welcome screen suggestion prompts to match specification
- Fixed missing TextChunk import in chat_app.py
- Replaced broken HTML onclick handlers with native Streamlit components
- Rewrote paper explorer panel with native st.tabs for Papers, Evidence, Gaps, Report
- Rewrote settings panel with native Streamlit components
- Added message actions: Copy (clipboard), Retry (regenerate), Export (JSON/Markdown)
- Fixed conversation history persistence and session management
- Updated documentation to use chat_app.py as primary entry point
- Implemented live research progress updates using st.status with 8-stage tracking
- Added token streaming support for NVIDIA (OpenAI) and Ollama providers in RAG pipeline
- Added user-friendly error handling for missing API keys, network errors, rate limits
- Improved settings panel with API key validation warnings and search defaults display
- Added missing API key warnings in message composer

### React Frontend (frontend/src/)
- Implemented ChatGPT-style conversational UI with collapsible sidebar
- Welcome screen with 4 suggestion cards (Literature Review, Paper Comparison, Evidence Investigation, Gap Discovery)
- Message list with markdown rendering, citations, progress indicators
- Message composer with Shift+Enter for new line, Enter to send
- Sidebar with conversation history (Today, Previous 7 Days, Older sections)
- Conversation management: New, Rename, Delete with confirmation
- Research status indicator showing LLM provider/model
- Paper explorer panel with tabs (Papers, Evidence, Gaps, Report)
- Settings panel with model config, API status, search defaults
- TypeScript types for Citation, Paper, ResearchStage
- API service layer with fetch-based communication
- Custom hooks for conversations and research polling
- CSS design system with CSS custom properties (light/dark theme support)

## Tests
99 passed, 3 skipped (embedding tests require model download)

## Commands
### Backend (Streamlit)
```bash
cd E:\aiml\researchagent
# Activate venv
venv\Scripts\activate
# Run tests
pytest
# Run Streamlit app
streamlit run app/chat_app.py --server.fileWatcherType=none
```

### Frontend (React + Vite)
```bash
cd E:\aiml\researchagent\frontend
# Install dependencies
npm install
# Development server
npm run dev
# Build for production
npm run build
# Preview production build
npm run preview
```

## Known Issues
- NVIDIA API requires valid API key and internet connection
- Vector DB needs rebuild after adding papers (use save_chunks_to_paper)
- Semantic Scholar API key optional (rate limited without)
- Crossref open access detection limited
- Cache directory in data/cache/
- PDF downloads only for open-access papers
- Large PDFs limited to 50MB
- Embedding tests skipped by default (require model download)
- LLM analysis requires NVIDIA API key and internet
- Cross-paper comparison needs 2+ analyzed papers
- Report generation needs NVIDIA API
- Unicode in reports may cause encoding issues on Windows
- Semantic Scholar and arXiv rate limiting may cause timeouts
- First run downloads embedding model (~130MB)

## Important Decisions
SQLite for initial database, Pydantic Settings for config, Loguru for logging, Modular package structure, No hardcoded secrets, UUID-based test databases, Common paper schema, DOI-first deduplication, Relevance ranking, Rate limiting per source, File-based caching, Never bypass paywalls, Page-level traceability, PyMuPDF for extraction, Configurable chunking, BGE-small for embeddings, ChromaDB for vectors, NVIDIA Nemotron-3-Ultra for LLM, Structured analysis output, FACT/INFERENCE/UNKNOWN distinction, Evidence status classification, Citation traceability, Conflict detection over resolution, Evidence-grounded gap discovery, Gap validation workflow, Structured report generation, Baseline comparisons, Reproducibility tracking, Structured logging, ChatGPT-style conversational UI pattern, Abstract fallback for vector store, Live progress updates with st.status, Token streaming for NVIDIA/Ollama, Native Streamlit components over HTML onclick handlers.

## Next Stage
Project Complete - All 8 Stages Implemented Successfully

Potential Future Enhancements: Research Planning Agent, Systematic Literature Review Workflow, Export Formats (PDF, LaTeX, Markdown), Research Question Refinement Agent, Cross-Paper Synthesis, Project Management, PDF Export, Multi-user Support, Cloud Deployment, Real-time streaming responses, Conversation export/import, Multi-modal paper analysis (figures/tables), Collaborative research sessions.