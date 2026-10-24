"""
Benchmark Dataset for Research Assistant Evaluation

Provides a curated dataset of manually verified questions, expected answers,
and evidence for evaluating the research assistant.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class BenchmarkItem:
    """Single benchmark item with question, expected answer, and evidence."""
    id: str
    question: str
    expected_answer: str
    evidence_papers: List[str]
    evidence_chunks: List[str]
    expected_citations: List[str]
    categories: List[str]
    difficulty: str
    expected_gaps: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified_by: str = "manual"
    metadata: Dict = field(default_factory=dict)


class BenchmarkDataset:
    """Collection of benchmark items for evaluation."""
    
    def __init__(self, items: List[BenchmarkItem] = None):
        self.items = items or []
    
    def add_item(self, item: BenchmarkItem):
        """Add a benchmark item."""
        self.items.append(item)
    
    def get_by_category(self, category: str) -> List[BenchmarkItem]:
        """Get items by category."""
        return [item for item in self.items if category in item.categories]
    
    def get_by_difficulty(self, difficulty: str) -> List[BenchmarkItem]:
        """Get items by difficulty."""
        return [item for item in self.items if item.difficulty == difficulty]
    
    def to_json(self, filepath: str):
        """Save dataset to JSON file."""
        data = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "items": [
                {
                    "id": item.id,
                    "question": item.question,
                    "expected_answer": item.expected_answer,
                    "evidence_papers": item.evidence_papers,
                    "evidence_chunks": item.evidence_chunks,
                    "expected_citations": item.expected_citations,
                    "categories": item.categories,
                    "difficulty": item.difficulty,
                    "expected_gaps": item.expected_gaps,
                    "created_at": item.created_at,
                    "verified_by": item.verified_by,
                    "metadata": item.metadata
                }
                for item in self.items
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, filepath: str) -> "BenchmarkDataset":
        """Load dataset from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = []
        for item_data in data.get("items", []):
            item = BenchmarkItem(**item_data)
            items.append(item)
        
        return cls(items)


def create_default_benchmark() -> BenchmarkDataset:
    """Create a default benchmark dataset with sample questions."""
    
    dataset = BenchmarkDataset()
    
    dataset.add_item(BenchmarkItem(
        id="bench_001",
        question="What are the main limitations of transformer models for long sequence modeling?",
        expected_answer="Transformer models face quadratic complexity with sequence length, making them inefficient for long sequences. They also struggle with positional encoding generalization beyond training length.",
        evidence_papers=["paper_001", "paper_002"],
        evidence_chunks=["chunk_001", "chunk_005", "chunk_012"],
        expected_citations=["paper_001", "paper_002"],
        categories=["limitations", "methodology"],
        difficulty="medium",
        expected_gaps=["Efficient long-sequence attention mechanisms", "Better positional encodings for extrapolation"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_002",
        question="Which datasets are commonly used for evaluating language model reasoning capabilities?",
        expected_answer="Common datasets include GSM8K for mathematical reasoning, MMLU for multi-task language understanding, Big-Bench for diverse reasoning tasks, and HumanEval for code generation.",
        evidence_papers=["paper_003", "paper_004", "paper_005"],
        evidence_chunks=["chunk_020", "chunk_021", "chunk_022"],
        expected_citations=["paper_003", "paper_004", "paper_005"],
        categories=["datasets", "evaluation"],
        difficulty="easy",
        expected_gaps=["Need for more diverse reasoning benchmarks", "Real-world deployment evaluation"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_003",
        question="How do retrieval-augmented generation systems compare to standard LLMs on factual accuracy?",
        expected_answer="RAG systems generally achieve higher factual accuracy by grounding responses in retrieved documents, reducing hallucination rates. However, they depend on retrieval quality and can propagate retrieval errors.",
        evidence_papers=["paper_006", "paper_007"],
        evidence_chunks=["chunk_030", "chunk_031"],
        expected_citations=["paper_006", "paper_007"],
        categories=["results", "comparison"],
        difficulty="hard",
        expected_gaps=["Systematic evaluation of RAG vs LLM across diverse domains", "Error propagation analysis in RAG pipelines"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_004",
        question="What are the common evaluation metrics for machine translation quality?",
        expected_answer="Common metrics include BLEU, METEOR, TER, chrF, and COMET. Neural metrics like COMET and BLEURT correlate better with human judgments than n-gram overlap metrics.",
        evidence_papers=["paper_008", "paper_009"],
        evidence_chunks=["chunk_040", "chunk_041"],
        expected_citations=["paper_008", "paper_009"],
        categories=["evaluation", "metrics"],
        difficulty="easy",
        expected_gaps=[]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_005",
        question="What are the key differences between supervised and self-supervised learning for representation learning?",
        expected_answer="Supervised learning requires labeled data and optimizes for specific tasks. Self-supervised learning uses unlabeled data with pretext tasks (masked prediction, contrastive learning) to learn general representations that transfer to downstream tasks.",
        evidence_papers=["paper_010", "paper_011"],
        evidence_chunks=["chunk_050", "chunk_051"],
        expected_citations=["paper_010", "paper_011"],
        categories=["methodology", "learning_paradigms"],
        difficulty="medium",
        expected_gaps=["Theoretical understanding of why SSL works", "Unified framework for SSL objectives"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_006",
        question="What are the main challenges in evaluating language model factuality?",
        expected_answer="Key challenges include: lack of reliable ground truth for open-ended generation, difficulty distinguishing hallucination from creative generation, static benchmarks becoming contaminated, and metrics not correlating well with human judgments of factuality.",
        evidence_papers=["paper_012", "paper_013"],
        evidence_chunks=["chunk_060", "chunk_061"],
        expected_citations=["paper_012", "paper_013"],
        categories=["evaluation", "factuality"],
        difficulty="hard",
        expected_gaps=["Reliable automated factuality metrics", "Dynamic benchmark generation", "Human evaluation protocol standardization"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_007",
        question="How do contrastive learning and masked language modeling differ as self-supervised objectives?",
        expected_answer="MLM (like BERT) predicts masked tokens from context, learning bidirectional representations. Contrastive learning (like SimCLR, CLIP) pulls positive pairs together and pushes negatives apart in embedding space, learning invariant representations.",
        evidence_papers=["paper_014", "paper_015"],
        evidence_chunks=["chunk_070", "chunk_071"],
        expected_citations=["paper_014", "paper_015"],
        categories=["methodology", "self-supervised-learning"],
        difficulty="medium",
        expected_gaps=["Unified framework for SSL objectives", "Theoretical analysis of SSL transferability"]
    ))
    
    dataset.add_item(BenchmarkItem(
        id="bench_008",
        question="What are the limitations of current language model evaluation benchmarks?",
        expected_answer="Current benchmarks suffer from: data contamination (training on test data), static nature (no updates), narrow scope (mostly English, specific domains), metric-gameability (overfitting to metrics), and poor correlation with real-world performance.",
        evidence_papers=["paper_016", "paper_017"],
        evidence_chunks=["chunk_080", "chunk_081"],
        expected_citations=["paper_016", "paper_017"],
        categories=["evaluation", "benchmarks"],
        difficulty="medium",
        expected_gaps=["Dynamic benchmark generation", "Contamination detection", "Real-world utility correlation"]
    ))
    
    return dataset


if __name__ == "__main__":
    dataset = create_default_benchmark()
    dataset.to_json("data/benchmark/default_benchmark.json")
    print(f"Created benchmark with {len(dataset.items)} items")