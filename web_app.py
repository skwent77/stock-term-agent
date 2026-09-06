"""면접관이 브라우저에서 사용할 수 있는 FastAPI 웹 진입점."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator


STATIC_DIR = Path(__file__).parent / "static"


class ChatService(Protocol):
    def answer(self, question: str) -> dict: ...


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("질문은 비어 있을 수 없습니다.")
        return normalized


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    term: str
    english: str
    category: str
    content: str
    source_name: str
    data_version: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


def create_app(chat_service: ChatService | None = None) -> FastAPI:
    app = FastAPI(
        title="한국어 주식 용어 AI",
        description="검색 근거를 함께 보여주는 투자교육용 RAG 서비스",
        version="0.1.0",
    )

    if chat_service is None:
        from web_chat_service import StockTermChatService

        chat_service = StockTermChatService()

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> dict:
        try:
            return chat_service.answer(request.question)
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    return app


app = create_app()
