import unittest

from term_documents import preprocess_terms, term_to_document


class TermDocumentsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_term = {
            "term": "  시가총액  ",
            "english": "Market   Capitalization",
            "category": "기본 개념",
            "definition": "현재 주가와   총 발행 주식 수를\n곱한 값입니다.",
            "example": "주가 × 발행주식 수",
        }

    def test_term_is_normalized_and_converted_to_one_document(self) -> None:
        document = term_to_document(
            self.raw_term,
            source_name="stock_terms.json",
            data_version="2026-08-09",
        )

        self.assertIn("용어: 시가총액", document.page_content)
        self.assertIn("영문: Market Capitalization", document.page_content)
        self.assertIn(
            "정의: 현재 주가와 총 발행 주식 수를 곱한 값입니다.",
            document.page_content,
        )
        self.assertEqual(document.metadata["term"], "시가총액")

    def test_document_id_is_stable_when_explanation_changes(self) -> None:
        original = term_to_document(
            self.raw_term,
            source_name="stock_terms.json",
            data_version="2026-08-09",
        )
        changed = term_to_document(
            {**self.raw_term, "definition": "수정된 정의입니다."},
            source_name="stock_terms.json",
            data_version="2026-08-10",
        )

        self.assertEqual(original.id, changed.id)
        self.assertEqual(original.metadata["term_id"], changed.metadata["term_id"])

    def test_metadata_contains_only_scalar_filter_and_trace_fields(self) -> None:
        document = term_to_document(
            {**self.raw_term, "aliases": ["마켓캡", "기업가치"]},
            source_name="stock_terms.json",
            data_version="2026-08-09",
        )

        self.assertEqual(document.metadata["aliases"], "마켓캡 | 기업가치")
        self.assertTrue(
            all(
                isinstance(value, (str, int, float, bool))
                for value in document.metadata.values()
            )
        )

    def test_one_short_term_becomes_one_document_without_chunking(self) -> None:
        documents = preprocess_terms(
            [self.raw_term, {**self.raw_term, "term": "PER", "english": "Price Earnings Ratio"}],
            source_name="stock_terms.json",
            data_version="2026-08-09",
        )

        self.assertEqual(len(documents), 2)

    def test_missing_required_field_is_rejected_with_field_name(self) -> None:
        invalid = {key: value for key, value in self.raw_term.items() if key != "definition"}

        with self.assertRaisesRegex(ValueError, "definition"):
            term_to_document(
                invalid,
                source_name="stock_terms.json",
                data_version="2026-08-09",
            )

    def test_blank_trace_metadata_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_name"):
            term_to_document(
                self.raw_term,
                source_name=" ",
                data_version="2026-08-09",
            )


if __name__ == "__main__":
    unittest.main()
