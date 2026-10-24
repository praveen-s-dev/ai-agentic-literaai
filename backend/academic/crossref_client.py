import re
from typing import Any, Optional

from academic.base_client import BaseAcademicClient
from academic.schemas import Author, Paper, PaperSource


class CrossrefClient(BaseAcademicClient):
    BASE_URL = "https://api.crossref.org"
    RATE_LIMIT = 10.0

    def _add_auth(self, headers: dict) -> dict:
        headers["User-Agent"] = "ResearchAssistant/1.0 (mailto:research@example.com)"
        return headers

    async def search_papers(self, query: str, limit: int = 20) -> list[Paper]:
        params = {
            "query": query,
            "rows": min(limit, 1000),
            "sort": "relevance",
            "select": "DOI,title,author,issued,abstract,URL,container-title,is-referenced-by-count,type",
        }
        data = await self._request("GET", "/works", params=params)
        return [self._parse_paper(item) for item in data.get("message", {}).get("items", [])]

    async def get_by_doi(self, doi: str) -> Optional[Paper]:
        data = await self._request("GET", f"/works/{doi}")
        if data:
            return self._parse_paper(data.get("message", {}))
        return None

    def _parse_paper(self, item: dict[str, Any]) -> Paper:
        authors = []
        for author in item.get("author", []):
            name_parts = []
            if author.get("given"):
                name_parts.append(author["given"])
            if author.get("family"):
                name_parts.append(author["family"])
            authors.append(
                Author(
                    name=" ".join(name_parts) if name_parts else author.get("name", ""),
                    affiliation=(
                        author.get("affiliation", [{}])[0].get("name")
                        if author.get("affiliation")
                        else None
                    ),
                    orcid=author.get("ORCID", "").replace("https://orcid.org/", "")
                    if author.get("ORCID")
                    else None,
                )
            )

        year = None
        if item.get("issued", {}).get("date-parts"):
            year = item["issued"]["date-parts"][0][0]

        abstract = item.get("abstract")
        if abstract:
            abstract = re.sub(r"<[^>]+>", "", abstract)

        return Paper(
            paper_id=item.get("DOI", ""),
            title=item.get("title", [""])[0] if item.get("title") else "",
            abstract=abstract,
            authors=authors,
            year=year,
            doi=item.get("DOI"),
            url=item.get("URL"),
            pdf_url=None,
            source=PaperSource.CROSSREF,
            citation_count=item.get("is-referenced-by-count", 0),
            is_open_access=False,
            venue=item.get("container-title", [""])[0] if item.get("container-title") else None,
            source_specific_id=item.get("DOI", ""),
        )