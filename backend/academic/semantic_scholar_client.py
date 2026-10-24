from typing import Any, Optional

from academic.base_client import BaseAcademicClient
from academic.schemas import Author, Paper, PaperSource


class SemanticScholarClient(BaseAcademicClient):
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT = 1.0

    def _add_auth(self, headers: dict) -> dict:
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search_papers(self, query: str, limit: int = 20) -> list[Paper]:
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": "paperId,title,abstract,authors,year,doi,url,citationCount,isOpenAccess,openAccessPdf,venue",
        }
        data = await self._request("GET", "/paper/search", params=params)
        return [self._parse_paper(item) for item in data.get("data", [])]

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        params = {
            "fields": "paperId,title,abstract,authors,year,doi,url,citationCount,isOpenAccess,openAccessPdf,venue"
        }
        data = await self._request("GET", f"/paper/{paper_id}", params=params)
        if data:
            return self._parse_paper(data)
        return None

    def _parse_paper(self, item: dict[str, Any]) -> Paper:
        authors = []
        for author in item.get("authors", []):
            authors.append(
                Author(
                    name=author.get("name", ""),
                    affiliation=None,
                    orcid=None,
                )
            )

        pdf_url = None
        if item.get("isOpenAccess") and item.get("openAccessPdf"):
            pdf_url = item["openAccessPdf"].get("url")

        return Paper(
            paper_id=item.get("paperId", ""),
            title=item.get("title", ""),
            abstract=item.get("abstract"),
            authors=authors,
            year=item.get("year"),
            doi=item.get("doi"),
            url=item.get("url"),
            pdf_url=pdf_url,
            source=PaperSource.SEMANTIC_SCHOLAR,
            citation_count=item.get("citationCount", 0),
            is_open_access=item.get("isOpenAccess", False),
            venue=item.get("venue"),
            source_specific_id=item.get("paperId", ""),
        )