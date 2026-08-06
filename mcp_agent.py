"""LangChain에서 MCP 서버를 사용하는 간단한 에이전트 예제."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

PROJECT_DIR = Path(__file__).resolve().parent


async def main() -> None:
    provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    models = {
        "openai": os.getenv("OPENAI_MODEL", "openai:gpt-5-mini"),
        "anthropic": os.getenv(
            "ANTHROPIC_MODEL", "anthropic:claude-sonnet-4-6"
        ),
    }
    if provider not in models:
        raise ValueError("MODEL_PROVIDER는 openai 또는 anthropic이어야 합니다.")

    client = MultiServerMCPClient(
        {
            "stock_terms": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(PROJECT_DIR / "mcp_server.py")],
            }
        }
    )
    tools = await client.get_tools()
    memory = InMemorySaver()
    agent = create_agent(
        model=models[provider],
        tools=tools,
        system_prompt=(
            "당신은 주식 투자 초보자를 돕는 금융 교육 에이전트입니다. "
            "주식 용어와 관련된 질문에는 MCP 도구로 데이터를 먼저 확인하세요. "
            "투자 조언이 아니라 교육 정보임을 분명히 하세요."
        ),
        checkpointer=memory,
    )

    print(f"MCP 에이전트 준비 완료 ({models[provider]}). 종료: quit")
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            question = input("\n질문 >> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"quit", "exit", "종료"}:
            break
        if not question:
            continue

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config=config,
        )
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
