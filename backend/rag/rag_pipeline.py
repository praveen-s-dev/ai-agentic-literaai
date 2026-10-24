import json
from typing import Optional, Generator

import ollama
from openai import OpenAI
from loguru import logger

from rag.retriever import Retriever, RetrievedChunk
from app.config import settings


SYSTEM_PROMPT = """You are an expert academic researcher analyzing scientific papers. 
Your task is to extract structured information from the provided text chunks with strict evidence grounding.

CRITICAL RULES:
1. Only state facts that are EXPLICITLY supported by the provided text chunks
2. Every claim MUST include evidence references (page number, chunk_id, paper_id)
3. Distinguish clearly between:
   - FACT FROM PAPER: Directly stated in the text
   - INFERENCE: Reasonable deduction from the text (mark as such)
   - UNKNOWN: Information not present in the provided chunks
4. Never invent or hallucinate information
5. If information is not in the chunks, state "UNKNOWN" or "NOT MENTIONED IN PROVIDED TEXT"

Output format must be valid JSON matching the specified schema exactly."""


class RAGPipeline:
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
    ):
        self.retriever = retriever or Retriever()
        self.temperature = temperature
        
        provider = settings.llm_provider
        
        if provider == "nvidia":
            if not settings.nvidia_api_key:
                raise ValueError("NVIDIA_API_KEY is required when using nvidia provider")
            self.model_name = model_name or settings.nvidia_model
            self.client = OpenAI(
                api_key=settings.nvidia_api_key,
                base_url=settings.nvidia_base_url,
            )
            self.provider = "nvidia"
        elif provider == "ollama":
            self.model_name = model_name or settings.ollama_model
            self.base_url = base_url or settings.ollama_base_url
            self.client = ollama.Client(host=self.base_url)
            self.provider = "ollama"
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def analyze_paper(
        self,
        paper_id: int,
        query: str = "Extract the research objective, methodology, datasets, results, and limitations from this paper",
        top_k: int = 15,
    ) -> dict:
        chunks = self.retriever.retrieve_by_paper(query, paper_id, top_k=top_k)
        
        if not chunks:
            return {"error": "No chunks found for paper", "paper_id": paper_id}

        context = self._build_context(chunks)
        analysis = self._extract_structured_analysis(context, paper_id)
        
        return {
            "paper_id": paper_id,
            "query": query,
            "chunks_used": len(chunks),
            "analysis": analysis,
        }

    def answer_question(
        self,
        question: str,
        paper_ids: Optional[list[int]] = None,
        top_k: int = 10,
    ) -> dict:
        chunks = self.retriever.retrieve(question, top_k=top_k, paper_ids=paper_ids)
        
        if not chunks:
            return {"answer": "No relevant information found in the provided papers.", "evidence": []}

        context = self._build_context(chunks)
        answer = self._generate_answer(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "evidence": [
                {
                    "chunk_id": c.chunk_id,
                    "paper_id": c.paper_id,
                    "title": c.title,
                    "page": c.page_number,
                    "similarity": c.similarity_score,
                }
                for c in chunks[:5]
            ],
        }

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[CHUNK {i+1}] Paper: {chunk.title} (ID: {chunk.paper_id}, Page: {chunk.page_number}, Chunk: {chunk.chunk_id})\n"
                f"{chunk.text}\n"
            )
        return "\n".join(context_parts)

    def _extract_structured_analysis(self, context: str, paper_id: int) -> dict:
        prompt = f"""{SYSTEM_PROMPT}

CONTEXT FROM PAPER (ID: {paper_id}):
{context}

TASK: Extract structured analysis of this paper. For each field, provide the claim and evidence references.
If a field is not addressed in the provided text, use "NOT MENTIONED IN PROVIDED TEXT".

OUTPUT JSON SCHEMA:
{{
    "research_objective": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "problem_addressed": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "methodology": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "algorithms_models": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "datasets": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "features": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "experimental_setup": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "results": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "limitations": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}},
    "future_work": {{"claim": "string", "evidence": [{{"page": int, "chunk_id": "string", "paper_id": int}}]}}
}}

Respond with ONLY the JSON object, no additional text."""

        response = self._call_llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {"error": "Failed to parse structured analysis", "raw_response": response}

    def _generate_answer(self, question: str, context: str) -> str:
        prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

QUESTION: {question}

Provide a concise, evidence-grounded answer. Cite sources using [CHUNK X] format.
If the answer cannot be determined from the context, state "Cannot be determined from provided text."

ANSWER:"""

        return self._call_llm(prompt).strip()

    def _call_llm(self, prompt: str) -> str:
        """Non-streaming LLM call (existing behavior)."""
        try:
            if self.provider == "nvidia":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    top_p=0.9,
                    max_tokens=2048,
                )
                return response.choices[0].message.content or ""
            else:  # ollama
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        "temperature": self.temperature,
                        "top_p": 0.9,
                        "num_predict": 2048,
                    },
                )
                return response.get("response", "")
        except Exception as e:
            logger.error(f"LLM call failed ({self.provider}): {e}")
            return f"ERROR: {str(e)}"

    def _call_llm_stream(self, prompt: str) -> Generator[str, None, None]:
        """Streaming LLM call - yields tokens as they arrive."""
        try:
            if self.provider == "nvidia":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    top_p=0.9,
                    max_tokens=2048,
                    stream=True,
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:  # ollama
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        "temperature": self.temperature,
                        "top_p": 0.9,
                        "num_predict": 2048,
                    },
                    stream=True,
                )
                for chunk in response:
                    if "response" in chunk:
                        yield chunk["response"]
        except Exception as e:
            logger.error(f"LLM streaming call failed ({self.provider}): {e}")
            yield f"ERROR: {str(e)}"

    def answer_question_stream(
        self,
        question: str,
        paper_ids: Optional[list[int]] = None,
        top_k: int = 10,
    ) -> Generator[str, None, None]:
        """Stream answer to a question with evidence."""
        chunks = self.retriever.retrieve(question, top_k=top_k, paper_ids=paper_ids)
        
        if not chunks:
            yield "No relevant information found in the provided papers."
            return

        context = self._build_context(chunks)
        prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

QUESTION: {question}

Provide a concise, evidence-grounded answer. Cite sources using [CHUNK X] format.
If the answer cannot be determined from the context, state "Cannot be determined from provided text."

ANSWER:"""

        for token in self._call_llm_stream(prompt):
            yield token