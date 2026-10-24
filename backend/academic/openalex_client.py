import asyncio
from typing import Any, Optional

from academic.base_client import BaseAcademicClient
from academic.schemas import Author, Paper, PaperSource
from app.config import settings


class OpenAlexClient(BaseAcademicClient):
    BASE_URL = "https://api.openalex.org"
    RATE_LIMIT = 10.0  # 10 req/s without API key, 100 req/s with key

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        # Use higher rate limit if API key is provided
        if api_key:
            self.RATE_LIMIT = 100.0
            self.rate_limiter = RateLimiter(self.RATE_LIMIT)

    def _add_auth(self, headers: dict) -> dict:
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def search_papers(self, query: str, limit: int = 20) -> list[Paper]:
        params = {
            "filter": f"title.search:{query}",
            "per-page": min(limit, 200),
            "sort": "cited_by_count:desc",
        }
        data = await self._request("GET", "/works", params=params)
        return [self._parse_paper(item) for item in data.get("results", [])]

    async def search_by_doi(self, doi: str) -> Optional[Paper]:
        data = await self._request("GET", f"/works/https://doi.org/{doi}")
        if data:
            return self._parse_paper(data)
        return None

    def _parse_paper(self, item: dict[str, Any]) -> Paper:
        authors = []
        for authorship in item.get("authorships", []):
            author_info = authorship.get("author", {})
            authors.append(
                Author(
                    name=author_info.get("display_name", ""),
                    affiliation=(
                        authorship.get("institutions", [{}])[0].get("display_name")
                        if authorship.get("institutions")
                        else None
                    ),
                    orcid=author_info.get("orcid"),
                )
            )

        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")

        is_oa = item.get("open_access", {}).get("is_oa", False)
        pdf_url = None
        if is_oa:
            oa_location = item.get("open_access", {}).get("oa_url")
            if oa_location:
                pdf_url = oa_location

        return Paper(
            paper_id=item.get("id", "").replace("https://openalex.org/", ""),
            title=item.get("display_name", ""),
            abstract=self._reconstruct_abstract(item.get("abstract_inverted_index")),
            authors=authors,
            year=item.get("publication_year"),
            doi=doi,
            url=item.get("id"),
            pdf_url=pdf_url,
            source=PaperSource.OPENALEX,
            citation_count=item.get("cited_by_count", 0),
            is_open_access=is_oa,
            venue=item.get("host_venue", {}).get("display_name"),
            source_specific_id=item.get("id", "").replace("https://openalex.org/", ""),
        )

    def _reconstruct_abstract(self, inverted_index: Optional[dict]) -> Optional[str]:
        if not inverted_index:
            return None
        try:
            max_pos = max(pos for positions in inverted_index.values() for pos in positions)
            words = [""] * (max_pos + 1)
            for word, positions in inverted_index.items():
                for pos in positions:
                    words[pos] = word
            return " ".join(words)
        except Exception:
            return None