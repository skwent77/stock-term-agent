"""주식 용어 MCP 서버.

실행:
    fastmcp run mcp_server.py
또는:
    python mcp_server.py
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from terms_service import TermsService

mcp = FastMCP(
    "Korean Stock Terms",
    instructions=(
        "한국어 주식 용어 데이터베이스입니다. "
        "용어를 정확히 알면 get_term을, 개념을 탐색하려면 search_terms를 사용하세요."
    ),
)
service = TermsService()


@mcp.tool()
def search_terms(
    query: str,
    limit: int = 5,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """질문이나 키워드와 관련된 주식 용어를 찾습니다.

    Args:
        query: 예) '기업 가치 평가 지표', '배당', 'market cap'
        limit: 반환할 결과 수(1~20)
        category: 선택적인 정확한 카테고리명
    """
    return service.search(query=query, limit=limit, category=category)


@mcp.tool()
def get_term(name: str) -> dict[str, str]:
    """한국어 또는 영어 이름이 정확히 일치하는 주식 용어를 조회합니다."""
    term = service.get_term(name)
    if term is None:
        return {
            "error": f"'{name}' 용어를 찾지 못했습니다.",
            "hint": "search_terms 도구로 비슷한 용어를 검색하세요.",
        }
    return term


@mcp.tool()
def list_categories() -> list[dict[str, Any]]:
    """사용 가능한 주식 용어 카테고리와 각 용어 수를 반환합니다."""
    return service.categories()


@mcp.tool()
def database_info() -> dict[str, Any]:
    """이 MCP 서버가 제공하는 데이터베이스의 요약을 반환합니다."""
    return {
        "name": "한국어 주식 용어 설명집",
        "term_count": service.count,
        "source": service.terms_file.name,
        "rag_used": False,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

