"""
Evaluation Framework for Evidence-Grounded Research Assistant

Provides metrics and evaluation utilities for assessing the quality of 
the research assistant's outputs across all pipeline stages.
"""

from evaluation.metrics import (
    RetrievalMetrics,
    CitationMetrics,
    EvidenceMetrics,
    ExtractionMetrics,
    ComparisonMetrics,
    GapMetrics,
    EvaluationResult,
)
from evaluation.benchmark import BenchmarkDataset, BenchmarkItem
from evaluation.baselines import BaselineRunner, StandardLLMBaseline, SingleDocRAGBaseline

__all__ = [
    "RetrievalMetrics",
    "CitationMetrics", 
    "EvidenceMetrics",
    "ExtractionMetrics",
    "ComparisonMetrics",
    "GapMetrics",
    "EvaluationResult",
    "BenchmarkDataset",
    "BenchmarkItem",
    "BaselineRunner",
    "StandardLLMBaseline",
    "SingleDocRAGBaseline",
]