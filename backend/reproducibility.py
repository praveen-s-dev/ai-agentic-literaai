"""
Reproducibility Tracker for Research Assistant

Provides utilities for tracking experiment configurations, parameters,
and results for reproducibility.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import uuid
from contextlib import contextmanager
import os


@dataclass
class ExperimentConfig:
    """Configuration for a research experiment."""
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    research_question: str = ""
    
    # Model configuration
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    
    # Retrieval parameters
    search_sources: List[str] = field(default_factory=lambda: ["openalex", "semantic_scholar", "crossref", "arxiv"])
    top_k: int = 10
    open_access_only: bool = True
    
    # Retrieval parameters
    similarity_threshold: float = 0.0
    max_papers: int = 20
    
    # RAG parameters
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    
    # LLM parameters
    llm_temperature: float = 0.1
    llm_top_p: float = 0.9
    max_tokens: int = 2048
    
    # Gap discovery parameters
    min_gap_evidence: int = 30
    max_gaps: int = 10
    
    # Database
    database_url: str = "sqlite:///data/research.db"
    vector_db_path: str = "data/vector_db"
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExperimentConfig":
        return cls(**data)


@dataclass
class ExperimentRun:
    """Record of an experiment execution."""
    run_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    experiment_id: str = ""
    config: Optional[ExperimentConfig] = None
    
    # Timing
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    # Status
    status: str = "running"  # running, completed, failed
    error_message: Optional[str] = None
    
    # Results
    papers_found: int = 0
    papers_processed: int = 0
    chunks_created: int = 0
    gaps_discovered: int = 0
    report_generated: bool = False
    
    # Artifacts
    report_path: Optional[str] = None
    log_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.config:
            result["config"] = self.config.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExperimentRun":
        config_data = data.pop("config", None)
        config = ExperimentConfig.from_dict(config_data) if config_data else None
        run = cls(**data)
        run.config = config
        return run


class ReproducibilityTracker:
    """Tracks experiment configurations and runs for reproducibility."""
    
    def __init__(self, log_dir: str = "logs/experiments"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_run: Optional[ExperimentRun] = None
    
    @contextmanager
    def track_experiment(self, config: ExperimentConfig) -> ExperimentRun:
        """Context manager for tracking an experiment run."""
        run = ExperimentRun(
            experiment_id=config.experiment_id,
            config=config
        )
        self.current_run = run
        
        # Save initial config
        self._save_run(run)
        
        try:
            yield run
            run.status = "completed"
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            raise
        finally:
            run.completed_at = datetime.now().isoformat()
            if run.started_at:
                start = datetime.fromisoformat(run.started_at)
                end = datetime.fromisoformat(run.completed_at)
                run.duration_seconds = (end - start).total_seconds()
            self._save_run(run)
            self.current_run = None
    
    def _save_run(self, run: ExperimentRun):
        """Save run to JSON file."""
        run_dir = self.log_dir / run.experiment_id
        run_dir.mkdir(parents=True, exist_ok=True)
        filepath = run_dir / f"run_{run.run_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(run.to_dict(), f, indent=2, ensure_ascii=False)
    
    def log_search(self, query: str, sources: List[str], results_count: int, 
                   top_k: int, open_access_only: bool):
        """Log a search operation."""
        if self.current_run:
            self.current_run.papers_found = max(
                self.current_run.papers_found, results_count
            )
            self._save_run(self.current_run)
    
    def log_paper_processing(self, paper_id: int, success: bool, 
                            chunks_created: int = 0):
        """Log paper processing result."""
        if self.current_run:
            if success:
                self.current_run.papers_processed += 1
                self.current_run.chunks_created += chunks_created
            self._save_run(self.current_run)
    
    def log_gap_discovery(self, gaps_found: int):
        """Log gap discovery results."""
        if self.current_run:
            self.current_run.gaps_discovered = max(
                self.current_run.gaps_discovered, gaps_found
            )
            self._save_run(self.current_run)
    
    def log_report_generation(self, report_path: str):
        """Log report generation."""
        if self.current_run:
            self.current_run.report_generated = True
            self.current_run.report_path = report_path
            self._save_run(self.current_run)
    
    def get_experiment_history(self, experiment_id: str = None) -> List[ExperimentRun]:
        """Get history of experiment runs."""
        if experiment_id:
            run_dir = self.log_dir / experiment_id
        else:
            # Get all experiment directories
            runs = []
            for exp_dir in self.log_dir.iterdir():
                if exp_dir.is_dir():
                    for run_file in exp_dir.glob("run_*.json"):
                        with open(run_file, 'r') as f:
                            data = json.load(f)
                            runs.append(ExperimentRun.from_dict(data))
            return sorted(runs, key=lambda r: r.started_at, reverse=True)
        
        if not run_dir.exists():
            return []
        
        runs = []
        for run_file in run_dir.glob("run_*.json"):
            with open(run_file, 'r') as f:
                data = json.load(f)
                runs.append(ExperimentRun.from_dict(data))
        
        return sorted(runs, key=lambda r: r.started_at, reverse=True)
    
    def export_experiment(self, experiment_id: str, output_path: str):
        """Export experiment data to a portable format."""
        runs = self.get_experiment_history(experiment_id)
        data = {
            "experiment_id": experiment_id,
            "exported_at": datetime.now().isoformat(),
            "runs": [run.to_dict() for run in runs]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def create_config_from_env() -> ExperimentConfig:
        """Create config from environment variables."""
        return ExperimentConfig(
            llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
            llm_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/research.db"),
            vector_db_path=os.getenv("VECTOR_DB_PATH", "data/vector_db"),
        )


# Global tracker instance
_tracker: Optional[ReproducibilityTracker] = None


def get_tracker() -> ReproducibilityTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ReproducibilityTracker()
    return _tracker