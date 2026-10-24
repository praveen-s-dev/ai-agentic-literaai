from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
import asyncio

from app.api.dependencies import get_db
from app.api.schemas.research import (
    ResearchRequest, ResearchTaskResponse, ResearchProgress, ResearchResult, ResearchStage
)
from app.api.schemas.conversation import ConversationCreate
from app.api.schemas.common import ErrorResponse
from database.models import ResearchSession
from database.connection import get_session

router = APIRouter(prefix="/research", tags=["research"])

# In-memory task storage (in production, use Redis or database)
research_tasks = {}


def _check_cancelled(task_id: str) -> bool:
    """Check if task has been cancelled."""
    task = research_tasks.get(task_id)
    return task is not None and task.get("status") == "cancelled"


async def run_research_workflow(task_id: str, query: str, conversation_id: int, settings_dict: dict):
    """Background task to run the research workflow."""
    # Import agents here to avoid circular imports
    from agents.search_agent import PaperSearchAgent
    from agents.paper_analysis_agent import PaperAnalysisAgent
    from agents.cross_paper_agent import CrossPaperAgent
    from agents.research_gap_agent import ResearchGapAgent
    from reports.report_generator import ReportGenerator
    from academic.schemas import PaperSource
    from papers.storage import save_papers_to_session, save_chunks_to_paper
    from papers.downloader import PDFDownloader
    from papers.pdf_processor import PDFProcessor
    from papers.chunker import TextChunker, TextChunk

    try:
        with get_session() as db:
            stages = list(ResearchStage)
            research_tasks[task_id]["stages"] = [s.value for s in stages]
            research_tasks[task_id]["completed_stages"] = []
            research_tasks[task_id]["current_stage"] = ResearchStage.PLANNING.value
            research_tasks[task_id]["message"] = "Planning research strategy..."
            research_tasks[task_id]["progress_percent"] = 5

            # Get conversation
            conv = db.query(ResearchSession).filter(ResearchSession.id == conversation_id).first()
            if not conv:
                raise ValueError("Conversation not found")

            all_papers = []
            analysis_results = {}
            comparison_results = None
            discovered_gaps = []
            generated_report = None
            citations = []
            paper_id_map = {}

            # Stage 1: Planning (already set)
            await asyncio.sleep(0.1)

            # Stage 2: Searching
            research_tasks[task_id]["current_stage"] = ResearchStage.SEARCHING.value
            research_tasks[task_id]["message"] = "Searching academic sources..."
            research_tasks[task_id]["progress_percent"] = 10
            research_tasks[task_id]["completed_stages"].append(ResearchStage.PLANNING.value)
            research_tasks[task_id]["failed_sources"] = []

            agent = PaperSearchAgent()
            source_enums = [PaperSource[s.upper().replace(" ", "_")] for s in settings_dict.get("sources", ["OpenAlex", "Crossref", "arXiv"])]

            papers_result = await agent.search(
                query=query,
                limit=settings_dict.get("max_papers", 20),
                sources=source_enums,
                open_access_only=settings_dict.get("open_access_only", True)
            )
            all_papers = papers_result.papers
            
            # Track failed sources
            requested_sources = [s.value for s in source_enums]
            successful_sources = papers_result.sources_searched
            failed_sources = [s for s in requested_sources if s not in successful_sources]
            research_tasks[task_id]["failed_sources"] = failed_sources
            
            await agent.close()

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            if not all_papers:
                research_tasks[task_id]["status"] = ResearchStage.COMPLETED.value
                research_tasks[task_id]["result"] = ResearchResult(
                    task_id=task_id,
                    conversation_id=conversation_id,
                    status=ResearchStage.COMPLETED,
                    content="I couldn't find any relevant papers for your query. Try broadening your search terms or removing the open-access filter.",
                    metadata={"papers_found": 0}
                )
                return

            # Filter by year
            min_year = settings_dict.get("min_year", 2015)
            if min_year:
                all_papers = [p for p in all_papers if p.year and p.year >= min_year]

            if not all_papers:
                research_tasks[task_id]["status"] = ResearchStage.COMPLETED.value
                research_tasks[task_id]["result"] = ResearchResult(
                    task_id=task_id,
                    conversation_id=conversation_id,
                    status=ResearchStage.COMPLETED,
                    content=f"No papers found from {min_year} onwards. Try adjusting the year filter.",
                    metadata={"papers_found": 0}
                )
                return

            # Save papers
            saved_paper_models, paper_id_map = save_papers_to_session(all_papers, conversation_id)

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 3: Processing
            research_tasks[task_id]["current_stage"] = ResearchStage.PROCESSING.value
            research_tasks[task_id]["message"] = "Processing paper content..."
            research_tasks[task_id]["progress_percent"] = 20
            research_tasks[task_id]["completed_stages"].append(ResearchStage.SEARCHING.value)
            research_tasks[task_id]["completed_stages"].append(ResearchStage.FILTERING.value)
            research_tasks[task_id]["completed_stages"].append(ResearchStage.RETRIEVING.value)

            papers_to_analyze = all_papers[:5]

            for paper in papers_to_analyze:
                # Check for cancellation
                if _check_cancelled(task_id):
                    return
                
                db_pid = paper_id_map.get(paper.source_specific_id, paper.paper_id)
                pdf_processed = False

                if paper.pdf_url:
                    try:
                        downloader = PDFDownloader()
                        path = await downloader.download(str(paper.pdf_url), str(paper.paper_id))
                        await downloader.close()

                        processor = PDFProcessor()
                        pdf_doc = processor.extract_text(str(path))

                        if pdf_doc.extraction_success:
                            chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
                            chunks = chunker.chunk_document(pdf_doc, db_pid)
                            save_chunks_to_paper(db_pid, conversation_id, chunks)
                            pdf_processed = True
                    except Exception as e:
                        print(f"Error processing PDF for {paper.paper_id}: {e}")

                # Fallback: use abstract if PDF not available or failed
                if not pdf_processed and paper.abstract:
                    try:
                        chunk = TextChunk(
                            paper_id=db_pid,
                            chunk_id=f"{db_pid}_abstract",
                            page_number=1,
                            text=paper.abstract,
                            char_start=0,
                            char_end=len(paper.abstract),
                            word_count=len(paper.abstract.split()),
                            char_count=len(paper.abstract),
                        )
                        save_chunks_to_paper(db_pid, conversation_id, [chunk])
                        print(f"Saved abstract chunk for paper {db_pid}")
                    except Exception as e:
                        print(f"Error saving abstract chunk for {paper.paper_id}: {e}")

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 4: Analyzing (Parallel)
            research_tasks[task_id]["current_stage"] = ResearchStage.ANALYZING.value
            research_tasks[task_id]["message"] = "Analyzing papers in parallel..."
            research_tasks[task_id]["progress_percent"] = 40
            research_tasks[task_id]["completed_stages"].append(ResearchStage.PROCESSING.value)

            analysis_agent = PaperAnalysisAgent()
            db_paper_ids = [paper_id_map.get(p.source_specific_id, p.paper_id) for p in papers_to_analyze[:3]]

            # Analyze papers in parallel
            async def analyze_paper_async(db_pid: int):
                try:
                    result = analysis_agent.analyze_paper(
                        paper_id=db_pid,
                        session_id=conversation_id,
                        query="Extract research objective, methodology, datasets, results, and limitations"
                    )
                    return db_pid, result
                except Exception as e:
                    print(f"Error analyzing paper {db_pid}: {e}")
                    return db_pid, None

            # Run analyses in parallel
            analysis_tasks = [analyze_paper_async(pid) for pid in db_paper_ids]
            analysis_results_list = await asyncio.gather(*analysis_tasks)
            
            for db_pid, result in analysis_results_list:
                if result:
                    analysis_results[db_pid] = result

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 5: Comparing
            research_tasks[task_id]["current_stage"] = ResearchStage.COMPARING.value
            research_tasks[task_id]["message"] = "Comparing findings..."
            research_tasks[task_id]["progress_percent"] = 55
            research_tasks[task_id]["completed_stages"].append(ResearchStage.ANALYZING.value)

            if len(db_paper_ids) >= 2:
                try:
                    cross_agent = CrossPaperAgent()
                    comparison_results = cross_agent.compare_papers(
                        session_id=conversation_id,
                        paper_ids=db_paper_ids
                    )
                except Exception as e:
                    print(f"Error comparing papers: {e}")

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 6: Verifying
            research_tasks[task_id]["current_stage"] = ResearchStage.VERIFYING.value
            research_tasks[task_id]["message"] = "Verifying evidence..."
            research_tasks[task_id]["progress_percent"] = 65
            research_tasks[task_id]["completed_stages"].append(ResearchStage.COMPARING.value)

            await asyncio.sleep(0.1)

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 7: Gap Discovery
            research_tasks[task_id]["current_stage"] = ResearchStage.GAP_DISCOVERY.value
            research_tasks[task_id]["message"] = "Discovering research gaps..."
            research_tasks[task_id]["progress_percent"] = 75
            research_tasks[task_id]["completed_stages"].append(ResearchStage.VERIFYING.value)

            try:
                gap_agent = ResearchGapAgent()
                discovered_gaps = gap_agent.discover_gaps(
                    session_id=conversation_id,
                    min_evidence_strength=50,
                    max_gaps=5
                )
            except Exception as e:
                print(f"Error discovering gaps: {e}")

            # Check for cancellation
            if _check_cancelled(task_id):
                return

            # Stage 8: Report Generation
            research_tasks[task_id]["current_stage"] = ResearchStage.REPORT_GENERATION.value
            research_tasks[task_id]["message"] = "Generating final report..."
            research_tasks[task_id]["progress_percent"] = 85
            research_tasks[task_id]["completed_stages"].append(ResearchStage.GAP_DISCOVERY.value)

            try:
                generator = ReportGenerator()
                generated_report = generator.generate_full_report(
                    session_id=conversation_id,
                    include_gaps=True,
                    min_gap_evidence=50,
                    max_gaps=5
                )
            except Exception as e:
                print(f"Error generating report: {e}")

            # Build response
            response_parts = [
                f"## Research Summary\n",
                f"I found **{len(all_papers)} papers** related to your query. "
                f"Analyzed **{len(analysis_results)} papers** in detail.\n"
            ]

            if all_papers:
                response_parts.append("### 📚 Relevant Papers\n")
                for i, paper in enumerate(all_papers[:5], 1):
                    authors = ", ".join(a.name for a in paper.authors[:3])
                    if len(paper.authors) > 3:
                        authors += " et al."
                    response_parts.append(
                        f"{i}. **{paper.title}** ({paper.year or 'N/A'})  \n"
                        f"   *{authors}* • {paper.citation_count} citations • {paper.source.value}\n"
                    )
                    if paper.doi:
                        response_parts.append(f"   DOI: {paper.doi}\n")
                    response_parts.append("\n")

            if analysis_results:
                response_parts.append("### 🔬 Key Findings\n")
                for db_pid, analysis in list(analysis_results.items())[:3]:
                    paper = next((p for p in all_papers if paper_id_map.get(p.source_specific_id) == db_pid), None)
                    if paper:
                        response_parts.append(f"**{paper.title[:60]}...**\n")
                        for field, label in [
                            ("research_objective", "Objective"),
                            ("methodology", "Methodology"),
                            ("datasets", "Datasets"),
                            ("results", "Results"),
                            ("limitations", "Limitations"),
                        ]:
                            if field in analysis and analysis[field].get("claim"):
                                claim = analysis[field]["claim"]
                                if claim != "NOT MENTIONED IN PROVIDED TEXT":
                                    response_parts.append(f"- **{label}:** {claim[:200]}...\n")
                        response_parts.append("\n")

            if comparison_results and comparison_results.conflicts:
                response_parts.append("### ⚠️ Conflicts Detected\n")
                for conflict in comparison_results.conflicts[:3]:
                    response_parts.append(
                        f"- **{conflict.field}:** {conflict.paper1_title[:40]}... vs "
                        f"{conflict.paper2_title[:40]}... ({conflict.conflict_type}, {conflict.severity})\n"
                    )
                response_parts.append("\n")

            if discovered_gaps:
                response_parts.append("### 💡 Candidate Research Gaps\n")
                for i, gap in enumerate(discovered_gaps[:3], 1):
                    response_parts.append(
                        f"{i}. **{gap.gap_statement}** (Evidence: {gap.evidence_strength}/100)\n"
                        f"   *Direction:* {gap.potential_research_direction[:150]}...\n\n"
                    )

            if generated_report:
                response_parts.append("### 📄 Full Report\n")
                response_parts.append("A comprehensive research report has been generated with full evidence traceability. ")
                response_parts.append("Use the actions below to view or download it.\n")

            # Build citations
            for paper in all_papers[:10]:
                citations.append({
                    "title": paper.title,
                    "authors": [a.name for a in paper.authors],
                    "year": paper.year,
                    "doi": paper.doi,
                    "url": str(paper.url) if paper.url else None,
                    "source": paper.source.value,
                    "citations": paper.citation_count,
                })

            research_tasks[task_id]["status"] = ResearchStage.COMPLETED.value
            research_tasks[task_id]["result"] = ResearchResult(
                task_id=task_id,
                conversation_id=conversation_id,
                status=ResearchStage.COMPLETED,
                content="".join(response_parts),
                citations=citations,
                papers=[{
                    "id": p.paper_id,
                    "title": p.title,
                    "authors": [a.name for a in p.authors],
                    "year": p.year,
                    "source": p.source.value,
                    "citations": p.citation_count,
                    "doi": p.doi
                } for p in all_papers[:10]],
                report=generated_report,
                metadata={
                    "papers_found": len(all_papers),
                    "papers_analyzed": len(analysis_results),
                    "gaps_found": len(discovered_gaps),
                    "has_report": generated_report is not None,
                },
                completed_at=datetime.utcnow()
            )
            research_tasks[task_id]["current_stage"] = ResearchStage.COMPLETED.value
            research_tasks[task_id]["message"] = "Research complete!"
            research_tasks[task_id]["progress_percent"] = 100
            research_tasks[task_id]["completed_stages"] = [s.value for s in stages]

    except Exception as e:
        research_tasks[task_id]["status"] = ResearchStage.FAILED.value
        research_tasks[task_id]["error"] = str(e)
        research_tasks[task_id]["result"] = ResearchResult(
            task_id=task_id,
            conversation_id=conversation_id,
            status=ResearchStage.FAILED,
            content=f"Research failed: {str(e)}",
            error=str(e),
            metadata={"papers_found": 0}
        )


@router.post("", response_model=ResearchTaskResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Create or get conversation
    if request.conversation_id:
        conv = db.query(ResearchSession).filter(ResearchSession.id == request.conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = conv.id
    else:
        # Create new conversation
        title = request.query[:60] + ("…" if len(request.query) > 60 else "")
        conv = ResearchSession(research_question=title, status="in_progress")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id

    # Create task
    task_id = str(uuid.uuid4())
    settings_dict = {
        "sources": request.settings.sources if request.settings else ["OpenAlex", "Crossref", "arXiv"],
        "max_papers": request.settings.max_papers if request.settings else 20,
        "open_access_only": request.settings.open_access_only if request.settings else True,
        "min_year": request.settings.min_year if request.settings else 2015,
    }

    research_tasks[task_id] = {
        "task_id": task_id,
        "conversation_id": conversation_id,
        "status": ResearchStage.PLANNING.value,
        "stages": [],
        "completed_stages": [],
        "current_stage": ResearchStage.PLANNING.value,
        "message": "Starting research...",
        "progress_percent": 0,
        "settings": settings_dict,
        "query": request.query,
    }

    # Start background task
    background_tasks.add_task(run_research_workflow, task_id, request.query, conversation_id, settings_dict)

    return ResearchTaskResponse(
        task_id=task_id,
        conversation_id=conversation_id,
        status=ResearchStage.PLANNING,
        message="Research started"
    )


@router.get("/{task_id}/status", response_model=ResearchProgress)
async def get_research_status(task_id: str):
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = research_tasks[task_id]
    return ResearchProgress(
        task_id=task_id,
        current_stage=ResearchStage(task["current_stage"]),
        stages=[ResearchStage(s) for s in task.get("stages", [])],
        completed_stages=[ResearchStage(s) for s in task.get("completed_stages", [])],
        message=task.get("message", ""),
        progress_percent=task.get("progress_percent", 0),
        failed_sources=task.get("failed_sources", [])
    )


@router.get("/{task_id}/result", response_model=ResearchResult)
async def get_research_result(task_id: str):
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = research_tasks[task_id]
    if "result" not in task:
        raise HTTPException(status_code=400, detail="Research not yet completed")

    return task["result"]


@router.delete("/{task_id}")
async def cancel_research(task_id: str):
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = research_tasks[task_id]
    task["status"] = "cancelled"
    task["error"] = "Cancelled by user"
    task["current_stage"] = ResearchStage.FAILED.value
    task["message"] = "Research cancelled by user"
    
    # Clear interval if still running
    if "interval_id" in task:
        try:
            import asyncio
            asyncio.get_event_loop().call_later(0, lambda: None)
        except:
            pass

    return {"status": "cancelled", "message": "Research cancelled by user"}