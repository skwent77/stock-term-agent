"""주식 용어 원천 데이터를 LangChain Document로 변환한다.

용어 레코드는 이미 의미적으로 완결된 짧은 단위이므로 별도 청킹을 하지 않는다.
본문에는 의미 검색에 필요한 내용을, 메타데이터에는 필터링과 출처 추적에
필요한 스칼라 값만 저장한다.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from typing import Any

from langchain_core.documents import Document

REQUIRED_FIELDS = ("term", "english", "category", "definition", "example")


def normalize_text(value: Any, *, field_name: str) -> str:
    """문자열의 앞뒤 및 연속 공백을 정규화하고 빈 값을 거부한다."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name}은 문자열이어야 합니다.")
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized:
        raise ValueError(f"{field_name}은 비어 있을 수 없습니다.")
    return normalized


def create_term_id(term: str, english: str) -> str:
    """표시 내용이 수정되어도 유지되는 용어 식별자를 만든다."""
    identity = f"{term.casefold()}\x1f{english.casefold()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"stock-term-{digest}"


def term_to_document(
    raw_term: Mapping[str, Any],
    *,
    source_name: str,
    data_version: str,
) -> Document:
    """단일 용어 레코드를 추적 가능한 LangChain Document로 변환한다."""
    normalized_source = normalize_text(source_name, field_name="source_name")
    normalized_version = normalize_text(data_version, field_name="data_version")

    fields: dict[str, str] = {}
    for field_name in REQUIRED_FIELDS:
        if field_name not in raw_term:
            raise ValueError(f"필수 필드가 없습니다: {field_name}")
        fields[field_name] = normalize_text(
            raw_term[field_name], field_name=field_name
        )

    aliases_value = raw_term.get("aliases", [])
    if isinstance(aliases_value, str):
        aliases_source: Iterable[Any] = [aliases_value]
    elif isinstance(aliases_value, (list, tuple)):
        aliases_source = aliases_value
    else:
        raise ValueError("aliases는 문자열 또는 문자열 배열이어야 합니다.")
    aliases = [
        normalize_text(alias, field_name="aliases") for alias in aliases_source
    ]

    term_id = create_term_id(fields["term"], fields["english"])
    content_lines = [
        f"용어: {fields['term']}",
        f"영문: {fields['english']}",
    ]
    if aliases:
        content_lines.append(f"별칭: {' | '.join(aliases)}")
    content_lines.extend(
        [
            f"카테고리: {fields['category']}",
            f"정의: {fields['definition']}",
            f"예시: {fields['example']}",
        ]
    )

    metadata: dict[str, str] = {
        "term_id": term_id,
        "term": fields["term"],
        "english": fields["english"],
        "category": fields["category"],
        "aliases": " | ".join(aliases),
        "source_name": normalized_source,
        "data_version": normalized_version,
    }
    return Document(
        id=term_id,
        page_content="\n".join(content_lines),
        metadata=metadata,
    )


def preprocess_terms(
    raw_terms: Iterable[Mapping[str, Any]],
    *,
    source_name: str,
    data_version: str,
) -> list[Document]:
    """용어 하나를 Document 하나로 변환하며 입력 순서를 보존한다."""
    return [
        term_to_document(
            raw_term,
            source_name=source_name,
            data_version=data_version,
        )
        for raw_term in raw_terms
    ]
