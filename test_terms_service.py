import unittest

from terms_service import TermsService


class TermsServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = TermsService()

    def test_get_term_in_korean(self):
        result = self.service.get_term("PER")
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "주요 지표")

    def test_search_by_description(self):
        results = self.service.search("회사의 시장 가치", limit=3)
        self.assertTrue(results)
        self.assertEqual(results[0]["term"], "시가총액")

    def test_categories_count_matches_total(self):
        total = sum(item["count"] for item in self.service.categories())
        self.assertEqual(total, self.service.count)

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.search("배당", limit=0)


if __name__ == "__main__":
    unittest.main()
