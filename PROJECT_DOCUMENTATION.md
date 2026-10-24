# Evidence-Grounded Autonomous Research Assistant

## Project Submission

> Replace each bracketed field with the student's details before submission.

| Detail | Information |
|---|---|
| Project title | Evidence-Grounded Autonomous Research Assistant |
| Student name(s) | [Enter student name(s)] |
| Register number(s) | [Enter register number(s)] |
| Department | [Enter department] |
| College name | [Enter college name] |
| Project guide | [Enter guide name and designation] |
| Academic year | [Enter academic year] |

<div style="page-break-after: always;"></div>

## 1. Project Agent

**Agent name:** Evidence-Grounded Autonomous Research Assistant

This project is an AI-assisted literature research system. It searches academic sources, organizes papers into research sessions, retrieves relevant passages from processed papers, and helps users analyze and compare studies. Responses grounded in the paper collection can include evidence references such as paper title, page, and text-chunk identifier.

The application includes a React and TypeScript chat interface backed by a Python API. The repository also contains Streamlit pages for research and system workflows.

## 2. Purpose of the Agent

### Problem statement

Reviewing many research papers manually is time-consuming. Researchers must locate relevant work, extract comparable details, track evidence for claims, and identify common limitations or differences. General-purpose language-model answers may not be supported by the papers being reviewed.

### Objectives

- Search academic metadata sources from a research query.
- Collect and organize papers in research sessions.
- Process available PDFs into page-aware text chunks.
- Retrieve relevant passages and use them to support paper analysis and question answering.
- Compare analyzed papers and highlight differences, commonalities, and possible research gaps.
- Preserve evidence references to make results easier to check against source papers.

## 3. Source Code and Implementation

The implementation is split into a Python backend and a web frontend:

- **Backend:** Python modules for academic-source clients, agent workflows, PDF processing, retrieval-augmented generation (RAG), evidence handling, reports, persistence, and API routes.
- **Frontend:** React and TypeScript components for the chat workspace, conversation sidebar, message display, research status, and paper/research panels.
- **Persistence:** SQLAlchemy models with SQLite for application records and ChromaDB for vector search.
- **Language models:** The RAG pipeline supports the configured Ollama or NVIDIA provider. Provider credentials and model settings are read from environment configuration.

### Main source folders

```text
researchagent/
├── backend/
│   ├── agents/       # Paper search, analysis, comparison, and gap discovery
│   ├── academic/     # OpenAlex, Semantic Scholar, Crossref, and arXiv clients
│   ├── app/api/      # FastAPI application, routes, and request schemas
│   ├── database/     # SQLAlchemy models and database connection
│   ├── evidence/     # Citation tracking and evidence verification
│   ├── papers/       # PDF download, extraction, chunking, and storage
│   ├── rag/          # Embeddings, vector store, retrieval, and LLM pipeline
│   ├── reports/      # Structured research report generation
├── frontend/
│   └── src/
│       ├── components/ # Chat and research interface components
│       ├── hooks/      # Frontend API/workflow hooks
│       ├── services/   # API client
│       └── styles/     # Interface styles
├── requirements.txt
└── PROJECT_DOCUMENTATION.md
```

### Typical workflow

1. The user starts a research session and searches for papers using a query.
2. The search agent queries the selected academic sources, combines the results, removes likely duplicates, ranks them, and applies requested filters.
3. Papers are saved to the session. Available PDFs can be downloaded, their text extracted with page numbers, and the text split into chunks.
4. The embedding and vector-retrieval components find chunks relevant to an analysis request or question.
5. The configured language model analyzes retrieved context. Structured analysis prompts ask it to separate directly supported facts, inferences, and unknown information.
6. The evidence and comparison workflows can check claims against the available corpus and compare analyses across papers.
7. The research-gap workflow proposes candidates based on patterns such as repeated limitations, missing evaluations, contradictions, and missing validation. Candidates should be reviewed by a researcher; they are not established findings.

### Technologies and tools

| Component | Technologies/tools |
|---|---|
| User interface | React, TypeScript, Vite |
| API | Python, FastAPI |
| Academic metadata | OpenAlex, Semantic Scholar, Crossref, arXiv |
| PDF processing | PyMuPDF |
| Embeddings and retrieval | sentence-transformers, ChromaDB |
| Language-model providers | Ollama or NVIDIA, configured through environment settings |
| Application data | SQLite, SQLAlchemy |
| Configuration and validation | Pydantic Settings |
| Logging and tests | Loguru, pytest |

## 4. Features and Functionalities

- **Multi-source literature search:** Searches OpenAlex, Semantic Scholar, Crossref, and arXiv. Results can be deduplicated, relevance-ranked, and filtered for open access.
- **Research sessions and conversations:** Organizes research work and conversation history through the API and frontend.
- **Paper processing:** Downloads and validates PDFs, extracts text, preserves page information, and chunks text for retrieval.
- **Paper analysis:** Uses retrieved passages to extract structured fields such as research objective, methodology, datasets, results, limitations, and future work.
- **Question answering over papers:** Retrieves relevant paper passages and returns an answer with available evidence references.
- **Cross-paper comparison:** Compares analyzed fields, identifies common methods or datasets, and detects potential conflicts or differences.
- **Evidence verification and citation tracking:** Records evidence status and references associated with claims.
- **Research-gap candidates:** Finds possible gaps from patterns across analyzed papers and associates them with supporting papers/evidence where available.
- **Report generation:** Creates structured research reports from stored research information.
- **Configurable model and storage:** Supports environment-based model configuration and local database/vector-store paths.

## 5. Edge Cases and Difficulties

| Challenge or edge case | Handling in the implementation |
|---|---|
| An academic API is slow, unavailable, or rate-limited | Search calls have per-source timeouts and failures are logged so other sources can still be queried. Results may be incomplete if a source is unavailable. |
| The same paper appears in multiple catalogs | Search results are deduplicated using paper identity information, including DOI/title matching in the search workflow. |
| A paper has no accessible PDF or PDF extraction yields no useful text | The RAG workflow depends on indexed chunks. The repository includes an abstract-based chunk fallback, but answers based only on abstracts have less detail than full-text analysis. |
| The requested information is absent from retrieved passages | Prompts direct structured analysis to identify information as unknown/not mentioned; question answering can report that no relevant information was found. |
| Fewer than two analyzed papers are available for comparison or gap discovery | Comparison requires at least two analyzed papers. Gap discovery returns no candidates when the session has fewer than two analyzed papers. |
| Model service or credentials are unavailable | Provider settings and required credentials are checked during initialization. The chosen model service must be reachable for LLM operations. |
| Similarity retrieval returns relevant-looking but incomplete context | Evidence references and retrieval scores help inspection, but retrieval and model output still require human review; the system cannot guarantee that every generated claim is correct. |

## 6. Limitations

- Search coverage and metadata quality depend on the external academic services and their availability.
- Full-text analysis requires accessible PDFs and successful extraction; some papers may only have metadata or abstracts.
- The quality of generated analysis depends on retrieved passages, model capabilities, and model availability.
- Research-gap discovery produces candidates from the papers and analyses in a session. It does not prove novelty or replace a comprehensive systematic review.
- Evidence references help users verify claims, but generated content should be checked against the cited paper pages.

## 7. Future Improvements

- Add a guided review protocol with explicit inclusion/exclusion criteria and duplicate-review support.
- Improve provenance by presenting claim-level citations and clickable page excerpts consistently throughout the interface.
- Add retries, backoff, source-health feedback, and more detailed partial-result reporting for academic API outages.
- Improve PDF handling for scanned documents, tables, figures, and papers with complex layouts.
- Add stronger evaluation datasets and routine quality checks for retrieval, extraction, citations, and gap candidates.
- Support exporting a complete review package, including references, evidence tables, and report metadata.
- Add authentication, access controls, and configurable retention policies for multi-user deployments.
- Improve progress, cancellation, and recovery behavior for long-running research tasks.

## 8. Running the Application

Use the repository's configured environment and follow the setup details in [README.md](./README.md). The usual local development arrangement is:

1. Install the Python dependencies from `requirements.txt` and configure the required environment variables in a local `.env` file.
2. Start the configured language-model service and ensure its selected model is available.
3. Start the API from the `backend` directory with `uvicorn app.api.main:app --reload` in an environment where FastAPI and Uvicorn are installed.
4. Start the frontend from the `frontend` directory with `npm run dev`.
5. Open the local Vite URL shown in the terminal and run a research query to capture the application-output screenshot.

The repository also contains Streamlit workflows; their setup and launch information is documented in the README. Do not include API keys or other secrets in screenshots or submitted documentation.

## 9. Screenshots Required for Submission

Add both original screenshots to `docs/screenshots/` and replace the placeholders below with the corresponding images before exporting or submitting this document. Capture real project/application views; do not use mockups.

### 9.1 Source code or project folder structure

Capture the project tree showing the `backend` and `frontend` source folders (or a representative source-code view).

**Screenshot file:** `docs/screenshots/source-code-structure.png`

**Insert screenshot below:**

_[Insert the source-code/project-folder screenshot here.]_

### 9.2 Agent output or running application

Run the application and capture the interface showing a real agent interaction or research output. Avoid exposing API keys, private data, or unrelated personal information.

**Screenshot file:** `docs/screenshots/agent-output.png`

**Insert screenshot below:**

_[Insert the running-application/agent-output screenshot here.]_

## 10. Conclusion

The Evidence-Grounded Autonomous Research Assistant brings academic search, paper processing, evidence-oriented analysis, comparison, and research-gap exploration into one workflow. Its use of retrieved passages and traceable references is intended to make literature investigation more organized and verifiable. Generated analyses and gap suggestions remain decision support and should be validated by the researcher against the source papers.
