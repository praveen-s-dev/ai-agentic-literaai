"""
Baseline Comparisons for Research Assistant Evaluation

Implements baseline systems for comparison against the full multi-stage
evidence-grounded workflow.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import json

from agents.search_agent import PaperSearchAgent
from agents.paper_analysis_agent import PaperAnalysisAgent
from agents.cross_paper_agent import CrossPaperAgent
from agents.research_gap_agent import ResearchGapAgent
from reports.report_generator import ReportGenerator
from rag.rag_pipeline import RAGPipeline
from rag.retriever import Retriever
from rag.embeddings import get_embedding_model
from rag.vector_store import VectorStore


class Baseline(ABC):
    """Abstract base class for baseline systems."""
    
    @abstractmethod
    def answer_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Answer a research question."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return baseline name."""
        pass


@dataclass
class StandardLLMBaseline(Baseline):
    """Baseline: Standard LLM without retrieval (no external knowledge)."""
    
    model_name: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    
    def get_name(self) -> str:
        return f"Standard LLM ({self.model_name})"
    
    def answer_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Answer using only the LLM's parametric knowledge."""
        import ollama
        
        client = ollama.Client(host=self.base_url)
        
        prompt = f"""You are a research assistant. Answer the following question based on your knowledge.

Question: {question}

Provide a comprehensive answer with specific details, citations where possible, and acknowledge uncertainty where appropriate."""
        
        try:
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "top_p": 0.9, "num_predict": 2048}
            )
            answer = response.get("response", "")
        except Exception as e:
            answer = f"Error: {str(e)}"
        
        return {
            "answer": answer,
            "method": "standard_llm",
            "model": self.model_name,
            "citations": [],
            "evidence_chunks": [],
            "papers_used": []
        }


@dataclass
class SingleDocRAGBaseline(Baseline):
    """Baseline: Traditional single-document RAG (retrieve top-1, then generate)."""
    
    model_name: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    vector_db_path: str = "data/vector_db"
    top_k: int = 1
    
    def __post_init__(self):
        self.embedding_model = get_embedding_model()
        self.vector_store = VectorStore()
        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            top_k=self.top_k
        )
    
    def get_name(self) -> str:
        return f"Single-Doc RAG (top-{self.top_k})"
    
    def answer_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Answer using single-document RAG."""
        # Retrieve top-1 chunk
        chunks = self.retriever.retrieve(question, top_k=self.top_k)
        
        if not chunks:
            return {
                "answer": "No relevant documents found.",
                "method": "single_doc_rag",
                "model": self.model_name,
                "citations": [],
                "evidence_chunks": [],
                "papers_used": []
            }
        
        # Use only the top chunk
        top_chunk = chunks[0]
        
        # Build context from top chunk
        context_text = f"Source: {top_chunk.title} (Paper ID: {top_chunk.paper_id}, Page: {top_chunk.page_number})\n{top_chunk.text}"
        
        # Generate answer
        import ollama
        client = ollama.Client(host=self.base_url)
        
        prompt = f"""You are a research assistant. Answer the question using ONLY the provided context.

Question: {question}

Context:
{context_text}

Instructions:
- Use ONLY the provided context
- Cite the source using [CHUNK_ID] format
- If the context doesn't contain the answer, say so
- Be precise and concise

Answer:"""
        
        try:
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "top_p": 0.9, "num_predict": 2048}
            )
            answer = response.get("response", "")
        except Exception as e:
            answer = f"Error: {str(e)}"
        
        return {
            "answer": answer,
            "method": "single_doc_rag",
            "model": self.model_name,
            "citations": [top_chunk.chunk_id],
            "evidence_chunks": [top_chunk.chunk_id],
            "papers_used": [top_chunk.paper_id]
        }


class MultiStageWorkflow:
    """The proposed multi-stage evidence-grounded workflow."""
    
    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        vector_db_path: str = "data/vector_db",
        top_k: int = 10
    ):
        self.embedding_model = get_embedding_model()
        self.vector_store = VectorStore(persist_directory=vector_db_path)
        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            top_k=top_k
        )
        self.rag_pipeline = RAGPipeline(
            retriever=self.retriever,
            model_name=model_name,
            base_url=base_url
        )
        self.search_agent = PaperSearchAgent()
        self.cross_paper_agent = CrossPaperAgent()
        self.paper_analysis_agent = PaperAnalysisAgent()
        self.research_gap_agent = ResearchGapAgent()
        self.report_generator = ReportGenerator()
    
    def run_full_workflow(self, research_question: str, session_id: int) -> Dict:
        """Run the complete multi-stage workflow."""
        # Stage 1: Search
        search_results = self.search_agent.search(
            query=research_question,
            limit=20,
            open_access_only=True
        )
        
        # Stage 2: Save papers to session
        # (Implementation would save to session)
        
        # Stage 3: Analyze papers
        analyses = {}
        # Would analyze each paper
        
        # Stage 4: Cross-paper comparison
        comparison = None
        if len(search_results.papers) >= 2:
            paper_ids = [p.paper_id for p in search_results.papers]
            comparison = self.cross_paper_agent.compare_papers(
                session_id=session_id,
                paper_ids=paper_ids
            )
        
        # Stage 5: Evidence verification
        # ...
        
        # Stage 6: Gap discovery
        gaps = []
        if search_results.papers:
            gaps = self.research_gap_agent.discover_gaps(session_id=1)
        
        # Stage 7: Report generation
        report = self.report_generator.generate_full_report(session_id=1)
        
        return {
            "research_question": research_question,
            "papers_found": len(search_results.papers) if search_results else 0,
            "papers_analyzed": len(analyses),
            "comparison": comparison,
            "gaps_found": len(gaps) if gaps else 0,
            "report": report
        }


@dataclass
class BaselineRunner:
    """Runs baseline comparisons and evaluates them."""
    
    baselines: List[Baseline] = field(default_factory=list)
    workflow: Optional[MultiStageWorkflow] = None
    
    def __post_init__(self):
        if not self.baselines:
            self.baselines = [
                StandardLLMBaseline(),
                SingleDocRAGBaseline(),
            ]
        if not self.workflow:
            self.workflow = MultiStageWorkflow()
    
    def add_baseline(self, baseline: Baseline):
        self.baselines.append(baseline)
    
    def run_all_baselines(self, questions: List[str]) -> Dict[str, List[Dict]]:
        """Run all baselines on a set of questions."""
        results = {}
        
        for baseline in self.baselines:
            baseline_results = []
            for question in questions:
                result = baseline.answer_question(question)
                result["question"] = question
                result["baseline"] = baseline.get_name()
                baseline_results.append(result)
            results[baseline.get_name()] = baseline_results
        
        return results
    
    def run_workflow(self, question: str) -> Dict:
        """Run the full multi-stage workflow."""
        if self.workflow:
            return self.workflow.run_full_workflow(question, session_id=1)
        return {"error": "Workflow not initialized"}
    
    def compare_against_baselines(self, question: str, ground_truth: Optional[Dict] = None) -> Dict:
        """Compare workflow against baselines."""
        workflow_result = self.run_workflow(question)
        baseline_results = self.run_all_baselines([question])
        
        return {
            "workflow": workflow_result,
            "baselines": baseline_results,
            "ground_truth": ground_truth
        }
    
    def run_evaluation(self, benchmark_items: List) -> Dict:
        """Run full evaluation on benchmark dataset."""
        from evaluation.metrics import (
            RetrievalMetrics, CitationMetrics, EvidenceMetrics,
            ExtractionMetrics, ComparisonMetrics, GapMetrics,
            HallucinationMetrics
        )
        
        all_results = {
            "baseline_results": {},
            "workflow_results": [],
            "metrics": {}
        }
        
        # Run baselines
        questions = [item.question for item in benchmark_items]
        all_results["baseline_results"] = self.run_all_baselines(questions)
        
        # Run workflow for each item
        for item in benchmark_items:
            workflow_result = self.run_workflow(item.question)
            all_results["workflow_results"].append({
                "question": item.question,
                "result": workflow_result
            })
        
        return all_results