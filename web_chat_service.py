"""웹 요청과 기존 RAG 함수 사이의 애플리케이션 서비스."""

from __future__ import annotations

import os
from threading import Lock
from typing import Any

import anthropic

from rag_chat import ask_claude, build_context, retrieve
from stock_terms import build_vectorstore, load_terms, load_vectorstore


class StockTermChatService:
    """Chroma 연결과 모델 클라이언트를 지연 초기화해 질문에 답한다."""

    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k
        self._vectorstore: Any | None = None
        self._lock = Lock()

    def _get_vectorstore(self) -> Any:
        if self._vectorstore is not None:
            return self._vectorstore

        with self._lock:
            if self._vectorstore is None:
                vectorstore = load_vectorstore()
                if not vectorstore.get(limit=1)["ids"]:
                    vectorstore = build_vectorstore(load_terms())
                self._vectorstore = vectorstore
        return self._vectorstore

    def answer(self, question: str) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        vectorstore = self._get_vectorstore()
        sources = retrieve(vectorstore, question, top_k=self.top_k)
        if not sources:
            return {
                "answer": "확인할 수 있는 근거가 없어 답변하기 어렵습니다.",
                "sources": [],
            }

        client = anthropic.Anthropic(api_key=api_key)
        answer = ask_claude(client, question, build_context(sources))
        return {"answer": answer, "sources": sources}
