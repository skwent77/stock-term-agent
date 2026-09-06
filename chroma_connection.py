"""Chroma 서버 연결 설정과 HTTP 클라이언트 생성 경계."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

import chromadb
from chromadb.api import ClientAPI


@dataclass(frozen=True)
class ChromaServerConfig:
    host: str = "localhost"
    port: int = 8000
    ssl: bool = False
    collection_name: str = "stock-terms"

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> ChromaServerConfig:
        """환경변수를 검증해 Chroma 서버 연결 설정을 만든다."""
        values = os.environ if environ is None else environ
        host = values.get("CHROMA_HOST", "localhost").strip()
        collection_name = values.get("CHROMA_COLLECTION", "stock-terms").strip()

        if not host:
            raise ValueError("CHROMA_HOST는 비어 있을 수 없습니다.")
        if not collection_name:
            raise ValueError("CHROMA_COLLECTION은 비어 있을 수 없습니다.")

        raw_port = values.get("CHROMA_PORT", "8000")
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("CHROMA_PORT는 정수여야 합니다.") from error
        if not 1 <= port <= 65535:
            raise ValueError("CHROMA_PORT는 1~65535 사이여야 합니다.")

        raw_ssl = values.get("CHROMA_SSL", "false").strip().lower()
        if raw_ssl not in {"true", "false"}:
            raise ValueError("CHROMA_SSL은 true 또는 false여야 합니다.")

        return cls(
            host=host,
            port=port,
            ssl=raw_ssl == "true",
            collection_name=collection_name,
        )


def create_chroma_http_client(config: ChromaServerConfig) -> ClientAPI:
    """검증된 설정으로 원격 Chroma 서버 클라이언트를 만든다."""
    return chromadb.HttpClient(
        host=config.host,
        port=config.port,
        ssl=config.ssl,
    )
