import unittest
from unittest.mock import MagicMock

from langchain_core.documents import Document

from rag_chat import build_context, retrieve


class RagChatRetrievalTest(unittest.TestCase):
    def test_retrieve_preserves_document_content_and_trace_metadata(self) -> None:
        vectorstore = MagicMock()
        vectorstore.similarity_search_with_relevance_scores.return_value = [
            (
                Document(
                    id="stock-term-per",
                    page_content=(
                        "용어: PER\n영문: Price Earnings Ratio\n"
                        "정의: 주가를 주당순이익으로 나눈 값입니다."
                    ),
                    metadata={
                        "term": "PER",
                        "english": "Price Earnings Ratio",
                        "category": "주요 지표",
                        "source_name": "stock_terms.json",
                        "data_version": "legacy-v1",
                    },
                ),
                0.91,
            )
        ]

        result = retrieve(vectorstore, "이익 대비 주가", top_k=1)

        self.assertEqual(result[0]["term"], "PER")
        self.assertIn("정의: 주가를", result[0]["content"])
        self.assertEqual(result[0]["source_name"], "stock_terms.json")
        self.assertEqual(result[0]["data_version"], "legacy-v1")
        self.assertEqual(result[0]["score"], 0.91)

    def test_context_contains_retrieved_content_and_provenance(self) -> None:
        context = build_context(
            [
                {
                    "term": "PER",
                    "english": "Price Earnings Ratio",
                    "category": "주요 지표",
                    "content": "정의: 주가를 주당순이익으로 나눈 값입니다.",
                    "source_name": "stock_terms.json",
                    "data_version": "legacy-v1",
                    "score": 0.91,
                }
            ]
        )

        self.assertIn("정의: 주가를 주당순이익으로", context)
        self.assertIn("출처: stock_terms.json", context)
        self.assertIn("데이터 버전: legacy-v1", context)


if __name__ == "__main__":
    unittest.main()
