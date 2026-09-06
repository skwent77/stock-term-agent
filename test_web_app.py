import unittest

from fastapi.testclient import TestClient

from web_app import create_app


class FakeChatService:
    def answer(self, question: str) -> dict:
        return {
            "answer": f"{question}에 대한 테스트 답변",
            "sources": [
                {
                    "term": "PER",
                    "english": "Price Earnings Ratio",
                    "category": "주요 지표",
                    "content": "정의: 주가를 주당순이익으로 나눈 값입니다.",
                    "source_name": "stock_terms.json",
                    "data_version": "legacy-v1",
                    "score": 0.91,
                }
            ],
        }


class WebAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(chat_service=FakeChatService()))

    def test_root_serves_interview_demo_page(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("주식 용어 AI", response.text)
        self.assertIn("질문", response.text)

    def test_health_reports_ready(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_returns_answer_and_sources(self) -> None:
        response = self.client.post("/chat", json={"question": "PER이 뭐야?"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("PER이 뭐야?", body["answer"])
        self.assertEqual(body["sources"][0]["term"], "PER")
        self.assertEqual(body["sources"][0]["score"], 0.91)

    def test_chat_rejects_blank_question(self) -> None:
        response = self.client.post("/chat", json={"question": "   "})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
