# Resume bullets

## English

- Built a provider-agnostic AI agent with LangChain, enabling GPT and Claude models to discover and invoke custom MCP tools for Korean financial-term lookup.
- Replaced a ChromaDB-based RAG pipeline with a lightweight JSON-backed tool architecture, eliminating embedding-model startup and vector-store dependencies.
- Added stateful multi-turn conversations with LangGraph checkpointing and separated MCP transport, domain logic, and data access for independent testing.
- Implemented and validated four typed MCP tools—search, exact lookup, category discovery, and database metadata—with automated unit and end-to-end tool-call tests.

## 한국어

- LangChain 기반 멀티 프로바이더 AI 에이전트를 개발해 GPT와 Claude가 한국어 금융 용어용 MCP 도구를 동적으로 선택·호출하도록 구현했습니다.
- ChromaDB 기반 RAG 파이프라인을 JSON 직접 조회 도구 구조로 전환해 임베딩 모델 초기화와 벡터 저장소 의존성을 제거했습니다.
- LangGraph 체크포인트 기반 멀티턴 대화 메모리를 적용하고 MCP 전송, 도메인 로직, 데이터 접근 계층을 분리해 테스트 가능성을 높였습니다.
- 검색·정확 조회·카테고리 탐색·메타데이터 조회 등 4개의 타입 기반 MCP 도구를 구현하고 단위 및 실제 도구 호출 테스트로 검증했습니다.
