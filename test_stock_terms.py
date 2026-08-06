import unittest
from unittest.mock import MagicMock, patch

import stock_terms


class StockTermsVectorStoreTest(unittest.TestCase):
    @patch("stock_terms.HuggingFaceEmbeddings")
    def test_embeddings_are_normalized(self, embeddings_class) -> None:
        stock_terms.create_embeddings()

        embeddings_class.assert_called_once_with(
            model_name=stock_terms.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    @patch("stock_terms.Chroma.from_documents")
    @patch("stock_terms.create_embeddings")
    def test_vectorstore_uses_cosine_distance(
        self,
        create_embeddings,
        from_documents,
    ) -> None:
        embedding = MagicMock()
        create_embeddings.return_value = embedding

        stock_terms.build_vectorstore(
            [
                {
                    "term": "시가총액",
                    "english": "Market Capitalization",
                    "category": "기본 개념",
                    "definition": "회사의 시장 가치입니다.",
                    "example": "주가와 발행주식 수를 곱합니다.",
                }
            ]
        )

        kwargs = from_documents.call_args.kwargs
        self.assertEqual(kwargs["embedding"], embedding)
        self.assertEqual(kwargs["collection_metadata"], {"hnsw:space": "cosine"})

    @patch("stock_terms.build_vectorstore")
    def test_rebuild_deletes_open_collection_before_recreating(self, build_vectorstore) -> None:
        current_store = MagicMock()
        terms = [{"term": "시가총액"}]

        result = stock_terms.rebuild_vectorstore(current_store, terms)

        current_store.delete_collection.assert_called_once_with()
        build_vectorstore.assert_called_once_with(terms)
        self.assertEqual(result, build_vectorstore.return_value)


if __name__ == "__main__":
    unittest.main()
