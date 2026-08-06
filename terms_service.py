"""stock_terms.json을 조회하는 순수 Python 서비스.

MCP나 LLM에 의존하지 않으므로 별도로 테스트할 수 있다.
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

DEFAULT_TERMS_FILE = Path(__file__).with_name("stock_terms.json")


class TermsService:
    def __init__(self, terms_file: Path = DEFAULT_TERMS_FILE) -> None:
        self.terms_file = terms_file
        self._terms = self._load_terms()

    def _load_terms(self) -> list[dict[str, str]]:
        with self.terms_file.open(encoding="utf-8") as file:
            data = json.load(file)

        terms = data.get("terms")
        if not isinstance(terms, list):
            raise ValueError("stock_terms.json에 'terms' 배열이 필요합니다.")
        return terms

    @property
    def count(self) -> int:
        return len(self._terms)

    def categories(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for item in self._terms:
            category = item["category"]
            counts[category] = counts.get(category, 0) + 1
        return [
            {"category": category, "count": count}
            for category, count in sorted(counts.items())
        ]

    def get_term(self, name: str) -> dict[str, str] | None:
        needle = self._normalize(name)
        for item in self._terms:
            aliases = (item["term"], item["english"])
            if any(self._normalize(alias) == needle for alias in aliases):
                return dict(item)
        return None

    def search(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("query는 비어 있을 수 없습니다.")
        if not 1 <= limit <= 20:
            raise ValueError("limit은 1~20 사이여야 합니다.")

        normalized_query = self._normalize(query)
        query_tokens = set(self._tokens(query))
        matches: list[tuple[float, dict[str, str]]] = []

        for item in self._terms:
            if category and item["category"] != category:
                continue

            searchable = " ".join(
                [
                    item["term"],
                    item["english"],
                    item["category"],
                    item["definition"],
                    item["example"],
                ]
            )
            normalized_text = self._normalize(searchable)
            text_tokens = set(self._tokens(searchable))

            score = SequenceMatcher(None, normalized_query, self._normalize(item["term"])).ratio()
            score = max(
                score,
                SequenceMatcher(
                    None, normalized_query, self._normalize(item["english"])
                ).ratio(),
            )
            if normalized_query in normalized_text:
                score += 1.0
            if query_tokens:
                score += len(query_tokens & text_tokens) / len(query_tokens)
            # 한국어 조사/어미 차이("회사" vs "회사의", "가치" vs "가치입니다")를
            # 임베딩 없이도 어느 정도 흡수한다.
            query_bigrams = self._bigrams(normalized_query)
            text_bigrams = self._bigrams(normalized_text)
            if query_bigrams:
                score += len(query_bigrams & text_bigrams) / len(query_bigrams)

            if score >= 0.25:
                matches.append((score, item))

        matches.sort(key=lambda match: (-match[0], match[1]["term"]))
        return [
            {**dict(item), "score": round(score, 3)}
            for score, item in matches[:limit]
        ]

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^0-9a-z가-힣]+", "", value.casefold())

    @staticmethod
    def _tokens(value: str) -> list[str]:
        return re.findall(r"[0-9a-z가-힣]+", value.casefold())

    @staticmethod
    def _bigrams(value: str) -> set[str]:
        return {value[index : index + 2] for index in range(len(value) - 1)}
