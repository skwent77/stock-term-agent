# 주식 용어 MCP 서버

기존 `rag_chat.py`와 달리 ChromaDB, 임베딩, `retrieve()`를 사용하지 않습니다.
LLM이 필요할 때 `stock_terms.json`을 조회하는 MCP 도구를 직접 호출합니다.
LangGraph의 인메모리 체크포인터가 같은 실행 세션의 대화 문맥을 유지합니다.

## 제공 도구

- `search_terms`: 키워드/문장으로 관련 용어 검색
- `get_term`: 한국어 또는 영어 용어 정확 조회
- `list_categories`: 카테고리와 용어 수 조회
- `database_info`: 데이터베이스 요약 조회

## 설치

```bash
cd /Users/jaehyun/Documents/leasemo
python3 -m venv .venv
.venv/bin/pip install -r requirements-mcp.txt
```

## MCP 서버 테스트

```bash
.venv/bin/fastmcp dev mcp_server.py
```

stdio 서버로 직접 실행하려면:

```bash
.venv/bin/python mcp_server.py
```

## LangChain 에이전트 실행

OpenAI:

```bash
export OPENAI_API_KEY="..."
MODEL_PROVIDER=openai .venv/bin/python mcp_agent.py
```

Anthropic:

```bash
export ANTHROPIC_API_KEY="..."
MODEL_PROVIDER=anthropic .venv/bin/python mcp_agent.py
```

모델을 바꾸려면 `OPENAI_MODEL` 또는 `ANTHROPIC_MODEL` 환경 변수를 설정합니다.

예를 들어 다음처럼 연속 질문하면 두 번째 질문에서 첫 번째 대화 문맥을 사용합니다.

```text
질문 >> PER이 뭐야?
질문 >> 그 지표가 낮으면 무조건 좋은 거야?
```

## Claude Desktop/Codex 등의 MCP 설정 예

클라이언트 설정의 서버 목록에 다음 내용을 추가합니다.

```json
{
  "mcpServers": {
    "stock-terms": {
      "command": "/Users/jaehyun/Documents/leasemo/.venv/bin/python",
      "args": ["/Users/jaehyun/Documents/leasemo/mcp_server.py"]
    }
  }
}
```

API 키나 `credentials.json`을 MCP 설정에 넣을 필요는 없습니다.

## 영상 개념과 코드의 대응

| 영상 개념 | 이 프로젝트 |
|---|---|
| 사용자 질의 | `mcp_agent.py`의 입력 루프 |
| LLM의 이해·계획 | LangChain `create_agent` |
| 외부 도구 | `mcp_server.py`의 MCP tools |
| 메모리 | `InMemorySaver`와 `thread_id` |
| 최종 응답 | agent의 마지막 메시지 |

이 구현은 벡터 검색이나 RAG를 사용하지 않습니다. `search_terms`는 작은 JSON 파일을
직접 검색하는 일반 MCP 도구입니다.
