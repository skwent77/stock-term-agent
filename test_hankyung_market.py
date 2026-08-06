import unittest

from hankyung_market import HankyungMarketError, us_payload_to_dataframe


class HankyungMarketTest(unittest.TestCase):
    def test_flattens_and_converts_numbers(self) -> None:
        payload = [
            {
                "name": "전기전자",
                "sub": [
                    {
                        "code": "aapl",
                        "symbol": "AAPL",
                        "name": "애플",
                        "close_price": "200.25",
                        "chg_net": "3.50",
                        "chg_rate": "1.72",
                        "market_cap": "3,000,000.50",
                        "class": "down",
                        "mark": "-",
                    }
                ],
            }
        ]

        frame = us_payload_to_dataframe(payload)

        self.assertEqual(frame.loc[0, "sector"], "전기전자")
        self.assertEqual(frame.loc[0, "symbol"], "AAPL")
        self.assertEqual(frame.loc[0, "close"], 200.25)
        self.assertEqual(frame.loc[0, "change"], -3.5)
        self.assertEqual(frame.loc[0, "change_pct"], -1.72)
        self.assertEqual(frame.loc[0, "market_cap"], 3_000_000.5)

    def test_rejects_unexpected_sector_shape(self) -> None:
        with self.assertRaises(HankyungMarketError):
            us_payload_to_dataframe([{"name": "전기전자", "sub": None}])


if __name__ == "__main__":
    unittest.main()
