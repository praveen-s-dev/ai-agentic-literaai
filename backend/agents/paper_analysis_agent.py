import json
from typing import Optional

from rag.rag_pipeline import RAGPipeline
from rag.retriever import Retriever
from database.connection import get_session
from database.models import PaperAnalysis, Paper as PaperModel, ResearchSession
from sqlalchemy.orm import Session
from loguru import logger


class PaperAnalysisAgent:
    def __init__(self):
        self.retriever = Retriever()
        self.rag_pipeline = RAGPipeline(retriever=self.retriever)

    def analyze_paper(
        self,
        paper_id: int,
        session_id: int,
        query: str = "Extract the research objective, methodology, datasets, results, and limitations from this paper",
    ) -> dict:
        logger.info(f"Analyzing paper {paper_id} in session {session_id}")

        # Check if paper exists and get title
        paper_title = None
        with get_session() as session:
            paper = session.get(PaperModel, paper_id)
            if not paper:
                return {"error": f"Paper {paper_id} not found", "paper_id": paper_id}
            
            research_session = session.get(ResearchSession, session_id)
            if not research_session:
                return {"error": f"Research session {session_id} not found", "session_id": session_id}
            
            # Get title while session is open
            paper_title = paper.title

        # Run analysis
        result = self.rag_pipeline.analyze_paper(paper_id, query=query)
        
        if "error" in result:
            return result

        analysis_data = result.get("analysis", {})
        
        # Store in database
        self._store_analysis(paper_id, session_id, analysis_data, result)

        return {
            "paper_id": paper_id,
            "session_id": session_id,
            "title": paper_title,
            "analysis": analysis_data,
            "chunks_used": result.get("chunks_used", 0),
        }

    def answer_question(
        self,
        question: str,
        paper_ids: Optional[list[int]] = None,
        session_id: Optional[int] = None,
    ) -> dict:
        if session_id:
            with get_session() as session:
                papers = session.query(PaperModel).filter(
                    PaperModel.session_id == session_id
                ).all()
                if paper_ids is None:
                    paper_ids = [p.id for p in papers]

        result = self.rag_pipeline.answer_question(question, paper_ids=paper_ids)
        return result

    def _store_analysis(
        self,
        paper_id: int,
        session_id: int,
        analysis_data: dict,
        full_result: dict,
    ):
        with get_session() as session:
            existing = session.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.session_id == session_id,
            ).first()

            analysis_json = json.dumps(analysis_data)

            if existing:
                existing.analysis_json = analysis_json
                existing.research_objective = analysis_data.get("research_objective", {}).get("claim")
                existing.problem_addressed = analysis_data.get("problem_addressed", {}).get("claim")
                existing.methodology = analysis_data.get("methodology", {}).get("claim")
                existing.algorithms_models = analysis_data.get("algorithms_models", {}).get("claim")
                existing.datasets = analysis_data.get("datasets", {}).get("claim")
                existing.features = analysis_data.get("features", {}).get("claim")
                existing.experimental_setup = analysis_data.get("experimental_setup", {}).get("claim")
                existing.results = analysis_data.get("results", {}).get("claim")
                existing.limitations = analysis_data.get("limitations", {}).get("claim")
                existing.future_work = analysis_data.get("future_work", {}).get("claim")
            else:
                new_analysis = PaperAnalysis(
                    paper_id=paper_id,
                    session_id=session_id,
                    analysis_json=analysis_json,
                    research_objective=analysis_data.get("research_objective", {}).get("claim"),
                    problem_addressed=analysis_data.get("problem_addressed", {}).get("claim"),
                    methodology=analysis_data.get("methodology", {}).get("claim"),
                    algorithms_models=analysis_data.get("algorithms_models", {}).get("claim"),
                    datasets=analysis_data.get("datasets", {}).get("claim"),
                    features=analysis_data.get("features", {}).get("claim"),
                    experimental_setup=analysis_data.get("experimental_setup", {}).get("claim"),
                    results=analysis_data.get("results", {}).get("claim"),
                    limitations=analysis_data.get("limitations", {}).get("claim"),
                    future_work=analysis_data.get("future_work", {}).get("claim"),
                )
                session.add(new_analysis)

            session.commit()
            logger.info(f"Stored analysis for paper {paper_id} in session {session_id}")

    def get_analysis(self, paper_id: int, session_id: int) -> Optional[dict]:
        with get_session() as session:
            analysis = session.query(PaperAnalysis).filter(
                PaperAnalysis.paper_id == paper_id,
                PaperAnalysis.session_id == session_id,
            ).first()

            if not analysis:
                return None

            return {
                "id": analysis.id,
                "paper_id": analysis.paper_id,
                "session_id": analysis.session_id,
                "research_objective": analysis.research_objective,
                "problem_addressed": analysis.problem_addressed,
                "methodology": analysis.methodology,
                "algorithms_models": analysis.algorithms_models,
                "datasets": analysis.datasets,
                "features": analysis.features,
                "experimental_setup": analysis.experimental_setup,
                "results": analysis.results,
                "limitations": analysis.limitations,
                "future_work": analysis.future_work,
                "created_at": analysis.created_at,
                "updated_at": analysis.updated_at,
            }

    def get_session_analyses(self, session_id: int) -> list[dict]:
        with get_session() as session:
            analyses = session.query(PaperAnalysis).filter(
                PaperAnalysis.session_id == session_id
            ).all()

            return [
                {
                    "id": a.id,
                    "paper_id": a.paper_id,
                    "research_objective": a.research_objective,
                    "methodology": a.methodology,
                    "results": a.results,
                    "limitations": a.limitations,
                    "created_at": a.created_at,
                }
                for a in analyses
            ]

    def close(self):
        pass