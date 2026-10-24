import re
import xml.etree.ElementTree as ET
from typing import Any, Optional

from academic.base_client import BaseAcademicClient
from academic.schemas import Author, Paper, PaperSource


class ArxivClient(BaseAcademicClient):
    BASE_URL = "https://export.arxiv.org/api"
    RATE_LIMIT = 1.0

    def _add_auth(self, headers: dict) -> dict:
        return headers

    async def search_papers(self, query: str, limit: int = 20) -> list[Paper]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 100),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        data = await self._request("GET", "/query", params=params, use_cache=False)
        return self._parse_feed(data)

    async def get_by_id(self, arxiv_id: str) -> Optional[Paper]:
        params = {"id_list": arxiv_id}
        data = await self._request("GET", "/query", params=params, use_cache=False)
        papers = self._parse_feed(data)
        return papers[0] if papers else None

    def _parse_feed(self, xml_text: str) -> list[Paper]:
        papers = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

            for entry in root.findall("atom:entry", ns):
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
        except Exception as e:
            pass
        return papers

    def _parse_entry(self, entry: ET.Element, ns: dict) -> Optional[Paper]:
        try:
            arxiv_id_elem = entry.find("atom:id", ns)
            arxiv_id = arxiv_id_elem.text if arxiv_id_elem is not None else ""
            arxiv_id_short = arxiv_id.split("/abs/")[-1] if arxiv_id else ""

            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None else ""

            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else None

            authors = []
            for author_elem in entry.findall("atom:author", ns):
                name_elem = author_elem.find("atom:name", ns)
                if name_elem is not None:
                    authors.append(Author(name=name_elem.text.strip()))

            published_elem = entry.find("atom:published", ns)
            year = None
            if published_elem is not None and published_elem.text:
                year = int(published_elem.text[:4])

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id_short}.pdf"
            abs_url = f"https://arxiv.org/abs/{arxiv_id_short}"

            return Paper(
                paper_id=arxiv_id_short,
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                doi=None,
                url=abs_url,
                pdf_url=pdf_url,
                source=PaperSource.ARXIV,
                citation_count=0,
                is_open_access=True,
                venue="arXiv",
                source_specific_id=arxiv_id_short,
            )
        except Exception:
            return None