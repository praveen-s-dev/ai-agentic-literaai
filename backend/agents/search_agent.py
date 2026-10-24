import asyncio
from difflib import SequenceMatcher
from typing import Optional

from academic.schemas import Paper, PaperSource, SearchResult
from academic.openalex_client import OpenAlexClient
from academic.semantic_scholar_client import SemanticScholarClient
from academic.crossref_client import CrossrefClient
from academic.arxiv_client import ArxivClient
from app.config import settings
from loguru import logger


class PaperSearchAgent:
    def __init__(self):
        self.openalex = OpenAlexClient(api_key=settings.openalex_api_key)
        self.semantic_scholar = SemanticScholarClient(api_key=settings.semantic_scholar_api_key)
        self.crossref = CrossrefClient()
        self.arxiv = ArxivClient()

    async def search(
        self,
        query: str,
        limit: int = 20,
        sources: Optional[list[PaperSource]] = None,
        open_access_only: bool = False,
    ) -> SearchResult:
        sources = sources or [
            PaperSource.OPENALEX,
            PaperSource.SEMANTIC_SCHOLAR,
            PaperSource.CROSSREF,
            PaperSource.ARXIV,
        ]

        all_papers = []
        sources_searched = []

        # Search each source with a timeout to avoid hanging on rate limits
        source_clients = {
            PaperSource.OPENALEX: self.openalex,
            PaperSource.SEMANTIC_SCHOLAR: self.semantic_scholar,
            PaperSource.CROSSREF: self.crossref,
            PaperSource.ARXIV: self.arxiv,
        }

        for source in sources:
            if source not in source_clients:
                continue
            client = source_clients[source]
            try:
                # Timeout per source: OpenAlex needs more time due to rate limits
                timeout = 30.0 if source == PaperSource.OPENALEX else 15.0
                papers = await asyncio.wait_for(client.search_papers(query, limit), timeout=timeout)
                all_papers.extend(papers)
                sources_searched.append(source)
            except asyncio.TimeoutError:
                logger.warning(f"{source.value} search timed out after {timeout}s")
            except Exception as e:
                logger.warning(f"{source.value} search failed: {e}")

        if open_access_only:
            all_papers = [p for p in all_papers if p.is_open_access]

        deduplicated = self._deduplicate(all_papers)
        ranked = self._rank_by_relevance(deduplicated, query)
        final_papers = ranked[:limit]

        await self.close()

        return SearchResult(
            papers=final_papers,
            total_results=len(final_papers),
            query=query,
            sources_searched=sources_searched,
        )

    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        seen = {}
        for paper in papers:
            key = paper.dedup_key()
            if key not in seen:
                seen[key] = paper
            else:
                existing = seen[key]
                if paper.citation_count > existing.citation_count:
                    seen[key] = paper
                elif paper.is_open_access and not existing.is_open_access:
                    seen[key] = paper
        return list(seen.values())

    def _rank_by_relevance(self, papers: list[Paper], query: str) -> list[Paper]:
        query_lower = query.lower()
        for paper in papers:
            score = 0
            title_lower = paper.title.lower()
            if query_lower in title_lower:
                score += 100
            score += SequenceMatcher(None, query_lower, title_lower).ratio() * 50
            if paper.abstract and query_lower in paper.abstract.lower():
                score += 20
            score += min(paper.citation_count / 100, 50)
            if paper.is_open_access:
                score += 10
            paper._relevance_score = score
        return sorted(papers, key=lambda p: p._relevance_score, reverse=True)

    async def close(self):
        await asyncio.gather(
            self.openalex.close(),
            self.semantic_scholar.close(),
            self.crossref.close(),
            self.arxiv.close(),
            return_exceptions=True,
        )