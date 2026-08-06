# AGENTS.md

한국어 주식 용어를 검색·설명하는 AI 투자교육 서비스.
이 파일은 이 저장소에서 작업하는 **모든** 코딩 에이전트의 공통 규칙이다.
`CLAUDE.md`는 이 파일을 가리키는 심볼릭 링크다. 규칙은 여기 한 곳에서만 수정한다.

## 언어

사용자와의 모든 대화, 커밋 메시지, 주석, 문서는 **한국어**로 작성한다.

## 역할 분담

이 저장소는 두 에이전트가 함께 작업하며, 역할이 분리되어 있다.

| 에이전트 | 역할 | 하는 일 |
|---|---|---|
| **GPT Codex** | 구현 | 기능 설계와 코드 작성, 테스트 작성, 리팩터링 |
| **Claude Code** | 검증 | diff 리뷰, 테스트 실행, 사양 위반·회귀 지적 |

### Claude Code에게 적용되는 규칙

- **먼저 코드를 수정하지 않는다.** 기본 동작은 읽기·실행·보고다.
- 사용자가 명시적으로 고치라고 요청했을 때만 수정한다.
- 문제를 발견하면 직접 고치지 말고 **파일:줄 + 무엇이 왜 잘못됐는지**를 보고한다.
  Codex가 그 보고를 받아 구현한다.
- 검증 범위는 항상 `git diff`다. 저장소 전체를 재검토하지 않는다.

## 검증 방법

**테스트 러너는 pytest가 아니라 `unittest`다. venv에 pytest가 설치되어 있지 않다.**

```bash
.venv/bin/python -m unittest discover -p "test_*.py"
```

기준선: 테스트 6개 전부 통과(`test_terms_service` 4개, `test_hankyung_market` 2개).
이 숫자가 줄면 회귀다.

의존성은 `requirements-mcp.txt`, 가상환경은 `.venv/`. 인터프리터는 `python`이 아니라
`.venv/bin/python`을 직접 지정한다.

## 작업 루프

```
Codex 구현  →  git diff  →  Claude 검증  →  통과: commit
                                            실패: 지적 → Codex 재작업
```

- 한 커밋은 한 가지 일만 담는다.
- 커밋 전 반드시 테스트를 실행한다.
- 검증되지 않은 변경 위에 새 변경을 쌓지 않는다.

## 현재 구조

```
stock_terms.json          원천 시드 데이터 (용어 데이터의 유일한 출처)
├── terms_service.py      difflib 기반 검색 — 테스트 있음, MCP 서버가 사용
│   └── mcp_server.py     FastMCP 도구 4개 (search_terms, get_term,
│                         list_categories, database_info)
│       └── mcp_agent.py  LangChain create_agent + MCP 클라이언트
└── stock_terms.py        Chroma + HuggingFace 임베딩 검색 — 테스트 없음

hankyung_market.py        한국경제 미국 시세 → pandas DataFrame (독립 모듈)
rag_chat.py               RAG 대화 실험 코드
```

## ⚠️ 알려진 드리프트 — 작업 전 반드시 확인

두 에이전트가 버전 관리 없이 작업한 결과, **사양서와 실제 코드가 어긋나 있다.**
새 작업을 시작하기 전에 이 항목들이 해소됐는지 먼저 확인한다.

1. **검색 구현이 두 벌이다.**
   `terms_service.py`(difflib)와 `stock_terms.py`(Chroma 임베딩)가 같은
   `stock_terms.json`을 대상으로 같은 일을 한다.
   사양서의 목표는 Chroma 경로지만, 실제로 테스트되고 동작하는 건 difflib 경로다.
   **어느 쪽이 정본인지 아직 정해지지 않았다.** 사용자에게 확인 없이 한쪽을
   확장하거나 삭제하지 않는다.

2. **사양서가 금지한 것이 이미 구현되어 있다.**
   `.claude/commands/shift.md`는 "MCP와 pandas ETL은 현재 핵심 범위에 포함하지
   않는다"고 명시하지만, `mcp_server.py`·`mcp_agent.py`·`hankyung_market.py`가
   존재한다. 사양서를 고칠지 코드를 걷어낼지 결정되지 않았다.

3. **`stock_terms.py`에 테스트가 없다.** Chroma 경로를 정본으로 택한다면
   테스트부터 필요하다.

4. **Pydantic 데이터 계약이 아직 없다.** 사양서 1단계의 선행 조건인데
   구현되지 않았다. 현재는 `stock_terms.json`을 검증 없이 그대로 읽는다.

## 아키텍처 원칙

상세한 TDD 사이클, 단계별 구현 순서, 완료 보고 형식은
**`.claude/commands/shift.md`**에 정의되어 있다. 구현 작업 전 반드시 읽는다.
(Claude Code에서는 `/shift`로 불러올 수 있다.)

핵심만 옮기면:

- 모듈은 **데이터 계약 / Document 변환 / Chroma 저장 / 검색 / 도구 / 모델 호출 /
  HTTP** 책임을 섞지 않는다.
- 테스트를 통과시키기 위한 하드코딩, 실제 오류를 감추는 넓은 `except`를 쓰지 않는다.
- 임베딩·네트워크·시간·LLM 응답 같은 비결정적 의존성은 테스트에서 격리한다.
  실제 API를 호출하는 테스트를 만들지 않는다.
- 금융 데이터와 검색 결과에는 값뿐 아니라 **출처와 데이터 버전**을 함께 담는다.
- 검색 결과는 사실 확인의 근거이지 투자 권유가 아니다. 답변에 이를 명시한다.
- 근거가 없으면 지어내지 말고 모른다고 답한다.
- 새 의존성은 표준 라이브러리나 기존 의존성으로 해결할 수 없는 이유를 설명한 뒤 추가한다.
- `langgraph.prebuilt.create_react_agent`는 deprecated다.
  `from langchain.agents import create_agent`를 쓴다.

## 보안

- API 키는 **환경변수로만** 주입한다. 코드·로그·커밋에 절대 넣지 않는다.
- `.env`, `.claude/settings.local.json`, `.chroma_db/`, `work/`는 커밋하지 않는다
  (`.gitignore`에 등록되어 있다).
- `hankyung_market.py`가 쓰는 한국경제 엔드포인트는 **공개 API 계약이 아니다.**
  스키마가 예고 없이 바뀔 수 있고, 재배포 전 이용 조건 확인이 필요하다.
