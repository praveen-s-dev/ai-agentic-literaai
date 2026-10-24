# Evidence-Grounded Autonomous Research Assistant

An autonomous multi-paper literature investigation system with full evidence traceability. Built for systematic literature reviews, meta-analyses, and research gap discovery.

For the student submission format, project overview, implementation details, and screenshot checklist, see [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md).

## 🎯 Overview

The Evidence-Grounded Research Assistant is an autonomous system that conducts end-to-end literature investigations:

1. **Research Planning** → **Paper Retrieval** → **PDF Processing** → **RAG Analysis** → **Cross-Paper Comparison** → **Evidence Verification** → **Gap Discovery** → **Structured Report**

## ✨ Key Features

### 🔍 Multi-Source Paper Retrieval
- **OpenAlex** - 200M+ papers with citation data
- **Semantic Scholar** - AI-powered paper search with TLDRs
- **Crossref** - Official DOI metadata
- **arXiv** - Preprints with full-text access
- Deduplication by DOI and title matching
- Open-access filtering

### 📄 PDF Processing & Chunking
- Robust PDF download with validation
- PyMuPDF text extraction preserving page numbers
- Configurable chunking (size, overlap, min size)
- Page-level traceability for every chunk

### 🧠 RAG-Powered Analysis
- Structured extraction of 10 research fields
- Evidence citations with page/chunk references
- FACT/INFERENCE/UNKNOWN classification
- Ollama LLM integration (configurable models)

### ⚖️ Cross-Paper Comparison
- 10-field systematic comparison
- Conflict detection (5 types)
- Common method/dataset identification
- Missing evaluation detection

### 🔍 Evidence Verification
- 5-tier evidence status: SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, INSUFFICIENT_EVIDENCE, CONFLICTING
- Citation tracking with page/chunk references
- Hallucination detection via claim verification

### 🔍 Research Gap Discovery
- 6 gap discovery strategies
- Evidence-strength scoring
- Gap validation workflow
- Candidate research direction generation

### 📊 Structured Report Generation
- 12+ section markdown reports
- Full evidence traceability
- Export to Markdown/PDF
- Gap validation workflow

## 🏗️ Architecture

```
├── app/                    # Streamlit UI & configuration
│   ├── main.py            # Health/status page
│   ├── search_page.py     # Paper search UI
│   ├── analysis_page.py   # Paper analysis UI
│   ├── comparison_page.py # Cross-paper comparison
│   ├── report_page.py     # Gap discovery & reports
│   ├── config.py          # Configuration management
│   └── logging_config.py  # Structured logging
├── agents/                 # Autonomous agents
│   ├── search_agent.py    # Multi-source paper search
│   ├── paper_analysis_agent.py  # RAG-based paper analysis
│   ├── cross_paper_agent.py     # Cross-paper comparison
│   └── research_gap_agent.py    # Gap discovery
├── academic/               # Academic API clients
│   ├── openalex_client.py
│   ├── semantic_scholar_client.py
│   ├── crossref_client.py
│   └── arxiv_client.py
├── papers/                 # Paper processing
│   ├── downloader.py      # PDF download & validation
│   ├── pdf_processor.py   # Text extraction (PyMuPDF)
│   ├── chunker.py         # Text chunking with page tracking
│   └── storage.py         # Database storage
├── rag/                    # RAG pipeline
│   ├── embeddings.py      # Sentence transformers
│   ├── vector_store.py    # ChromaDB vector store
│   ├── retriever.py       # Semantic retrieval
│   └── rag_pipeline.py    # RAG + LLM integration
├── evidence/               # Evidence handling
│   ├── citation_tracker.py    # Citation management
│   └── verifier.py            # Evidence verification
├── reports/                # Report generation
│   └── report_generator.py
├── database/               # SQLite + SQLAlchemy
│   ├── models.py          # ORM models
│   └── connection.py      # Session management
├── evaluation/             # Evaluation framework
│   ├── metrics.py         # Retrieval, citation, evidence metrics
│   ├── benchmark.py       # Benchmark dataset
│   └── baselines.py       # Baseline comparisons
├── reproducibility/        # Experiment tracking
└── tests/                  # Test suite (100+ tests)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama (for LLM): `curl -fsSL https://ollama.com/install.sh | sh`
- SQLite (built-in)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd researchagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import setup_logging; from database.connection import init_db; setup_logging(); init_db()"

# Start Ollama (in separate terminal)
ollama serve
ollama pull llama3.2

# Run Streamlit app
streamlit run app/chat_app.py
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# LLM Configuration
LLM_PROVIDER=ollama          # or "nvidia" for NVIDIA Nemotron
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# NVIDIA API Configuration (when LLM_PROVIDER=nvidia)
# Get API key from https://build.nvidia.com/
NVIDIA_API_KEY=your_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-ultra

# Optional API Keys (for higher rate limits)
OPENALEX_API_KEY=your_key
SEMANTIC_SCHOLAR_API_KEY=your_key

# Database
DATABASE_URL=sqlite:///data/research.db
VECTOR_DB_PATH=data/vector_db

# Application
APP_HOST=0.0.0.0
APP_PORT=8501
LOG_LEVEL=INFO
```

## 📖 Usage Guide

### 1. Home Page
System health dashboard with database status, vector DB status, and Ollama connectivity.

### 2. Research Page
- Enter research question
- Select sources (OpenAlex, Semantic Scholar, Crossref, arXiv)
- Configure filters (year, open access, result limit)
- Search and review results with abstracts
- Save papers to session

### 3. Papers Page
- View session papers with metadata
- Download PDFs
- Process PDFs (download → extract → chunk)
- Queue for analysis

### 4. Analysis Page
- Select paper for RAG-powered analysis
- Custom analysis focus
- 10-field structured extraction with evidence citations
- FACT/INFERENCE/UNKNOWN classification

### 4. Comparison Page
- Select 2+ papers for comparison
- Field-by-field comparison across 10 dimensions
- Conflict detection with severity classification
- Common methods/datasets/limitations identification

### 5. Evidence Page
- Verify claims against paper corpus
- 5-tier evidence status classification
- Citation tracking with page/chunk references

### 6. Gaps Page
- Discover candidate research gaps
- 6 discovery strategies (limitations, contradictions, etc.)
- Evidence strength scoring
- Validation/rejection workflow

### 5. Report Page
- Generate comprehensive markdown reports
- 12+ sections with evidence traceability
- Export to Markdown/PDF
- Gap validation workflow

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_evaluation.py -v
pytest tests/test_evidence.py -v
pytest tests/test_rag.py -v

# Run with coverage
pytest --cov=agents --cov=papers --cov=rag --cov=evidence --cov=reports tests/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`ollama` or `nvidia`) | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.2` |
| `NVIDIA_API_KEY` | NVIDIA API key (required for nvidia provider) | (required if nvidia) |
| `NVIDIA_BASE_URL` | NVIDIA API base URL | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_MODEL` | NVIDIA model name | `nvidia/nemotron-3-ultra` |
| `OPENALEX_API_KEY` | OpenAlex API key | (optional) |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API key | (optional) |
| `DATABASE_URL` | SQLite database URL | `sqlite:///data/research.db` |
| `VECTOR_DB_PATH` | ChromaDB path | `data/vector_db` |
| `EMBEDDING_MODEL` | Sentence transformer model | `BAAI/bge-small-en-v1.5` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Model Configuration

**Ollama models** (when `LLM_PROVIDER=ollama`):
- `llama3.2` (default, 8B)
- `llama3.2:70b` (70B, requires more RAM)
- `mistral` (7B)
- `codellama` (code-focused)
- Any Ollama-compatible model

**NVIDIA models** (when `LLM_PROVIDER=nvidia`):
- `nvidia/nemotron-3-ultra` (default, 53B)
- `nvidia/nemotron-4-340b` (340B)
- `meta/llama-3.1-405b-instruct` (405B)
- `meta/llama-3.1-70b-instruct` (70B)
- `mistralai/mixtral-8x22b-instruct` (141B)
- Get more at https://build.nvidia.com/

## 📊 Evaluation Framework

The system includes a comprehensive evaluation framework:

- **Retrieval Metrics**: Precision@K, Recall@K, MRR, NDCG@K
- **Citation Metrics**: Precision, Recall, F1
- **Evidence Metrics**: Support rate, relevance, coverage
- **Extraction Metrics**: Field accuracy, FACT/INFERENCE classification
- **Comparison Metrics**: Conflict detection, commonality F1
- **Gap Metrics**: Evidence quality, novelty
- **Hallucination Metrics**: Claim verification, hallucination rate

### Baselines
- **Standard LLM**: Direct LLM without retrieval
- **Single-Doc RAG**: Top-1 retrieval only
- **Multi-Stage Workflow**: Full pipeline (proposed)

Run evaluation:
```bash
pytest tests/test_evaluation.py -v
pytest tests/test_evidence.py -v
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python -c "from app import setup_logging; from database.connection import init_db; setup_logging(); init_db()"

EXPOSE 8501
CMD ["streamlit", "run", "app/chat_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t research-assistant .
docker run -p 8501:8501 -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs research-assistant
```

## 📁 Data Directories

```
data/
├── papers/           # Downloaded PDFs
├── processed/        # Processed outputs
├── cache/            # API response cache
├── vector_db/        # ChromaDB vector store
└── research.db       # SQLite database

logs/
├── app.log           # Application logs
├── error.log         # Error logs
├── experiments.jsonl # Experiment tracking
└── reproducibility.jsonl # Reproducibility tracking
```

## 🔒 Security & Ethics

- **No paywall bypassing**: Only open-access papers downloaded
- **Rate limiting**: Respects API rate limits
- **Citation tracking**: Full provenance for all claims
- **No data retention**: Local SQLite only
- **Open source**: MIT license

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 📚 Citation

If you use this system in your research, please cite:

```bibtex
@software{research_assistant_2024,
  title = {Evidence-Grounded Autonomous Research Assistant},
  author = {Research Assistant Team},
  year = {2024},
  url = {https://github.com/your-org/researchagent}
}
```

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` folder
- **Discussions**: GitHub Discussions

---

*Built with ❤️ for evidence-based research*