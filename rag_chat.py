"""
주식 용어 RAG 챗봇
- ChromaDB에서 관련 용어 검색 (Retrieval)
- 검색된 용어를 컨텍스트로 Claude에 전달 (Augmented Generation)

설치: uv pip install anthropic python-dotenv langchain-chroma langchain-community sentence-transformers
"""

import os
from dotenv import load_dotenv
import anthropic
from langchain_chroma import Chroma

from stock_terms import load_vectorstore

load_dotenv()

def retrieve(vectorstore: Chroma, query: str, top_k: int = 3) -> list[dict]:
    """질문과 관련된 용어를 ChromaDB에서 검색"""
    results = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    retrieved = []
    for doc, score in results:
        m = doc.metadata
        retrieved.append({
            "term": m["term"],
            "english": m["english"],
            "category": m["category"],
            "content": doc.page_content,
            "source_name": m["source_name"],
            "data_version": m["data_version"],
            "score": score,
        })
    return retrieved


def build_context(retrieved: list[dict]) -> str:
    """검색된 용어를 Claude에 넘길 컨텍스트 문자열로 변환"""
    lines = []
    for item in retrieved:
        lines.append(
            f"[{item['term']} / {item['english']}] ({item['category']})\n"
            f"{item['content']}\n"
            f"출처: {item['source_name']}\n"
            f"데이터 버전: {item['data_version']}"
        )
    return "\n\n".join(lines)


def ask_claude(client: anthropic.Anthropic, question: str, context: str) -> str:
    """RAG: 검색된 컨텍스트를 포함해 Claude에 질문"""
    system_prompt = (
        "당신은 주식 투자 초보자를 돕는 친절한 금융 교육 도우미입니다.\n"
        "아래 제공된 주식 용어 데이터베이스를 바탕으로 질문에 답하세요.\n"
        "데이터베이스에 없는 내용은 '제 데이터에는 없지만'이라고 먼저 밝히고 답하세요.\n"
        "어려운 용어는 쉽게 풀어서 설명하고, 구체적인 예시를 들어주세요."
    )

    user_message = (
        f"[관련 용어 데이터베이스]\n{context}\n\n"
        f"[사용자 질문]\n{question}"
    )

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("오류: ANTHROPIC_API_KEY가 .env 파일에 없습니다.")
        return

    print("Chroma 서버와 임베딩 모델 로딩 중...")
    vectorstore = load_vectorstore()
    client = anthropic.Anthropic(api_key=api_key)

    print("\n주식 용어 RAG 챗봇 준비 완료!")
    print("궁금한 점을 자유롭게 질문하세요. (종료: quit)\n")

    while True:
        try:
            question = input("질문 >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "종료"):
            print("종료합니다.")
            break

        # 1. Retrieve — ChromaDB에서 관련 용어 검색
        retrieved = retrieve(vectorstore, question, top_k=3)

        print(f"\n[검색된 관련 용어] {', '.join(r['term'] for r in retrieved)}")

        # 2. Augment + Generate — Claude에 컨텍스트와 함께 질문
        context = build_context(retrieved)
        print("[Claude 답변 생성 중...]\n")

        answer = ask_claude(client, question, context)
        print(f"{answer}\n")
        print("-" * 50)


if __name__ == "__main__":
    main()
