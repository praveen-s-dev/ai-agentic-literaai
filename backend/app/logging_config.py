import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings
from reproducibility import get_tracker, ExperimentConfig


def setup_logging(experiment_config: Optional[ExperimentConfig] = None) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Console output with color
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        filter=lambda record: "experiment" not in record["extra"] or record["extra"].get("experiment") is True
    )

    # Main application log
    logger.add(
        log_dir / "app.log",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    # Error log
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    # Experiment tracking log (structured JSON)
    logger.add(
        log_dir / "experiments.jsonl",
        level="INFO",
        format="{message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
        filter=lambda record: "experiment" in record["extra"] and record["extra"].get("experiment") is True
    )

    # Reproducibility tracking log
    logger.add(
        log_dir / "reproducibility.jsonl",
        level="INFO",
        format="{message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
        filter=lambda record: "reproducibility" in record["extra"]
    )


def get_logger(name: str, experiment_id: str = None):
    """Get a logger bound with experiment context."""
    extra = {}
    if experiment_id:
        extra["experiment_id"] = experiment_id
    return logger.bind(name=name, experiment=True, **{"experiment_id": experiment_id} if experiment_id else {})


def log_experiment_start(config: "ExperimentConfig"):
    """Log experiment start with full configuration."""
    from reproducibility import get_tracker
    tracker = get_tracker()
    tracker.tracker.log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(
        "Experiment started",
        extra={
            "reproducibility": True,
            "event": "experiment_start",
            "experiment_id": config.experiment_id,
            "config": config.to_dict()
        }
    )


def log_experiment_end(experiment_id: str, status: str, duration: float = None, error: str = None):
    """Log experiment completion."""
    logger.info(
        "Experiment completed",
        extra={
            "reproducibility": True,
            "event": "experiment_end",
            "experiment_id": experiment_id,
            "status": status,
            "duration_seconds": duration,
            "error": error
        }
    )


def log_search(query: str, sources: list, results_count: int, top_k: int, 
               experiment_id: str = None):
    """Log a search operation."""
    logger.info(
        "Search executed",
        extra={
            "reproducibility": True,
            "event": "search",
            "experiment_id": experiment_id,
            "query": query,
            "sources": sources,
            "results_count": results_count,
            "top_k": top_k
        }
    )


def log_paper_processing(paper_id: int, success: bool, chunks_created: int = 0, 
                         experiment_id: str = None):
    """Log paper processing result."""
    logger.info(
        "Paper processed",
        extra={
            "reproducibility": True,
            "event": "paper_processed",
            "experiment_id": experiment_id,
            "paper_id": paper_id,
            "success": success,
            "chunks_created": chunks_created
        }
    )


def log_gap_discovery(gaps_found: int, experiment_id: str = None):
    """Log gap discovery results."""
    logger.info(
        "Gaps discovered",
        extra={
            "reproducibility": True,
            "event": "gaps_discovered",
            "experiment_id": experiment_id,
            "gaps_found": gaps_found
        }
    )


def log_report_generation(report_path: str, experiment_id: str = None):
    """Log report generation."""
    logger.info(
        "Report generated",
        extra={
            "reproducibility": True,
            "event": "report_generated",
            "experiment_id": experiment_id,
            "report_path": report_path
        }
    )


def log_error(error: Exception, context: dict = None, experiment_id: str = None):
    """Log an error with full context."""
    logger.error(
        f"Error: {str(error)}",
        extra={
            "reproducibility": True,
            "event": "error",
            "experiment_id": experiment_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
    )


def get_logger(name: str, experiment_id: str = None):
    """Get a logger bound with experiment context."""
    extra = {"experiment": True}
    if experiment_id:
        extra["experiment_id"] = experiment_id
    return logger.bind(name=name, **extra)