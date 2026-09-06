FROM ghcr.io/astral-sh/uv:0.11.32 AS uv

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
RUN useradd --create-home --uid 10001 appuser && chown appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
COPY --chown=appuser:appuser llamaindex-chroma-rag/pyproject.toml llamaindex-chroma-rag/pyproject.toml
RUN uv sync --frozen --no-dev --no-install-workspace

COPY --chown=appuser:appuser main.py web_app.py web_chat_service.py rag_chat.py stock_terms.py ./
COPY --chown=appuser:appuser chroma_connection.py term_documents.py stock_terms.json ./
COPY --chown=appuser:appuser static/ static/

EXPOSE 8000
CMD ["sh", "-c", "exec .venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
