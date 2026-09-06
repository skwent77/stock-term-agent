"""
주식 용어 설명집 - LangChain + ChromaDB 기반 시맨틱 검색
설치: pip install langchain-chroma langchain-community sentence-transformers
"""

import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from chroma_connection import ChromaServerConfig, create_chroma_http_client
from term_documents import preprocess_terms

TERMS_FILE = Path(__file__).parent / "stock_terms.json"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DATA_VERSION = "legacy-v1"

CATEGORIES = [
    "기본 개념",
    "시장 용어",
    "주요 지표",
    "재무 개념",
    "투자 전략",
    "투자 심화",
    "기타",
]


def load_terms() -> list[dict]:
    with open(TERMS_FILE, encoding="utf-8") as f:
        return json.load(f)["terms"]


def create_embeddings() -> HuggingFaceEmbeddings:
    """문서와 질의에 공통으로 사용할 정규화된 임베딩을 생성한다."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vectorstore(terms: list[dict]) -> Chroma:
    embeddings = create_embeddings()
    config = ChromaServerConfig.from_env()
    client = create_chroma_http_client(config)
    docs = preprocess_terms(
        terms,
        source_name=TERMS_FILE.name,
        data_version=DATA_VERSION,
    )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        ids=[document.id for document in docs],
        client=client,
        collection_name=config.collection_name,
        collection_metadata={"hnsw:space": "cosine"},
    )
    return vectorstore


def load_vectorstore() -> Chroma:
    embeddings = create_embeddings()
    config = ChromaServerConfig.from_env()
    client = create_chroma_http_client(config)
    return Chroma(
        client=client,
        collection_name=config.collection_name,
        embedding_function=embeddings,
    )


def rebuild_vectorstore(vectorstore: Chroma, terms: list[dict]) -> Chroma:
    """열린 DB 폴더를 직접 지우지 않고 컬렉션 API로 안전하게 재구축한다."""
    vectorstore.delete_collection()
    return build_vectorstore(terms)


def format_term(
    meta: dict,
    page_content: str,
    score: float | None = None,
) -> str:
    lines = [
        f"\n{'='*50}",
        f"  {meta['term']}  ({meta['english']})",
        f"  [{meta['category']}]",
        f"{'='*50}",
        page_content,
    ]

    if score is not None:
        lines.append(f"  유사도: {score:.1%}")

    return "\n".join(lines)


def search(vectorstore: Chroma, query: str, top_k: int = 3) -> None:
    results = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    if not results:
        print("결과가 없습니다.")
        return
    print(f"\n['{query}' 검색 결과 — 상위 {top_k}개]")
    for doc, score in results:
        print(format_term(doc.metadata, doc.page_content, score))


def list_by_category(vectorstore: Chroma, category: str) -> None:
    results = vectorstore.get(where={"category": category})
    if not results["metadatas"]:
        print(f"'{category}' 카테고리에 해당하는 용어가 없습니다.")
        return
    print(f"\n[카테고리: {category}] — 총 {len(results['metadatas'])}개")
    for meta, page_content in zip(results["metadatas"], results["documents"]):
        print(format_term(meta, page_content))


def show_all(vectorstore: Chroma) -> None:
    results = vectorstore.get()
    print(f"\n[전체 용어 목록] — 총 {len(results['metadatas'])}개\n")
    for cat in CATEGORIES:
        terms_in_cat = [m for m in results["metadatas"] if m["category"] == cat]
        if terms_in_cat:
            print(f"  [{cat}]")
            for m in terms_in_cat:
                print(f"    • {m['term']}  ({m['english']})")
    print()


def print_help() -> None:
    print(
        """
주식 용어 설명집 명령어
  search <검색어>          — 시맨틱 검색 (예: search 회사 가치 측정)
  cat <카테고리>           — 카테고리별 조회
  all                      — 전체 목록 보기
  cats                     — 카테고리 목록 보기
  rebuild                  — DB 재구축
  help                     — 도움말
  quit / exit              — 종료
"""
    )


def main():
    print("주식 용어 설명집 로딩 중...")

    vs = load_vectorstore()
    if vs.get(limit=1)["ids"]:
        print("Chroma 서버의 기존 컬렉션을 불러왔습니다.")
    else:
        print("첫 실행: 임베딩 DB 구축 중 (1~2분 소요)...")
        terms = load_terms()
        vs = build_vectorstore(terms)
        print(f"완료! {len(terms)}개 용어 저장됨.")

    print_help()

    while True:
        try:
            raw = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            print("종료합니다.")
            break
        elif cmd == "search" and arg:
            search(vs, arg)
            # 내가 키워야 하는 건 이 서치쪽
        elif cmd == "cat" and arg:
            list_by_category(vs, arg)
        elif cmd == "all":
            show_all(vs)
        elif cmd == "cats":
            print("\n카테고리 목록:")
            for c in CATEGORIES:
                print(f"  • {c}")
        elif cmd == "help":
            print_help()
        elif cmd == "rebuild":
            print("DB 재구축 중...")
            terms = load_terms()
            vs = rebuild_vectorstore(vs, terms)
            print(f"완료! {len(terms)}개 용어 저장됨.")
        else:
            print(f"알 수 없는 명령어: '{raw}'  (help 로 도움말 확인)")


if __name__ == "__main__":
    main()
