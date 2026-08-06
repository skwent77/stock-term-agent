"""한국경제 데이터센터의 전종목 시세를 pandas DataFrame으로 변환한다.

페이지가 내부적으로 호출하는 JSON 응답을 사용한다. 이 엔드포인트는 공식
공개 API 계약이 아니므로, 응답 스키마가 바뀔 가능성을 고려해 검증한다.
서비스에 재배포하기 전에는 한국경제/FactSet의 이용 조건을 별도로 확인해야 한다.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd

BASE_URL = "https://datacenter.hankyung.com"
US_URL = f"{BASE_URL}/equities-all/us"
PAGE_URL = f"{BASE_URL}/equities-all"


class HankyungMarketError(RuntimeError):
    """시세 요청 또는 응답 스키마가 올바르지 않을 때 발생한다."""


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError) as exc:
        raise HankyungMarketError(f"숫자로 변환할 수 없는 값입니다: {value!r}") from exc


def _signed(value: Any, mark: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return -abs(number) if str(mark).strip() == "-" else abs(number)


def fetch_us_payload(timeout: float = 15.0) -> list[dict[str, Any]]:
    """미국 전종목 시세 JSON을 한 번 요청한다."""
    request = Request(
        US_URL,
        headers={
            "Accept": "application/json",
            "Referer": PAGE_URL,
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/122.0 Safari/537.36"
            ),
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except Exception as exc:
        raise HankyungMarketError(f"미국 시세 요청에 실패했습니다: {exc}") from exc

    if not isinstance(payload, list):
        raise HankyungMarketError("미국 시세 응답이 예상한 배열 형식이 아닙니다.")
    return payload


def us_payload_to_dataframe(
    payload: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    """업종별 중첩 JSON을 종목당 한 행인 DataFrame으로 평탄화한다."""
    rows: list[dict[str, Any]] = []

    for group in payload:
        sector = group.get("name")
        stocks = group.get("sub")
        if not isinstance(stocks, list):
            raise HankyungMarketError(f"{sector!r} 업종의 sub 필드가 배열이 아닙니다.")

        for stock in stocks:
            if not isinstance(stock, Mapping):
                raise HankyungMarketError(f"{sector!r} 업종에 잘못된 종목 데이터가 있습니다.")
            mark = stock.get("mark", "")
            rows.append(
                {
                    "sector": sector,
                    "symbol": stock.get("symbol"),
                    "name_ko": stock.get("name"),
                    "slug": stock.get("code"),
                    "close": _number(stock.get("close_price")),
                    "change": _signed(stock.get("chg_net"), mark),
                    "change_pct": _signed(stock.get("chg_rate"), mark),
                    "market_cap": _number(stock.get("market_cap")),
                    "direction": stock.get("class"),
                    "source_url": (
                        "https://www.hankyung.com/globalmarket/equities/americas/"
                        f"{stock.get('code')}"
                    ),
                }
            )

    columns = [
        "sector",
        "symbol",
        "name_ko",
        "slug",
        "close",
        "change",
        "change_pct",
        "market_cap",
        "direction",
        "source_url",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if not frame.empty:
        frame = frame.drop_duplicates(subset=["symbol"], keep="first").reset_index(drop=True)
    return frame


def fetch_us_equities(timeout: float = 15.0) -> pd.DataFrame:
    """미국 시세를 받아 분석하기 쉬운 DataFrame으로 반환한다."""
    return us_payload_to_dataframe(fetch_us_payload(timeout=timeout))


def main() -> None:
    parser = argparse.ArgumentParser(description="한국경제 미국 시세 DataFrame 수집기")
    parser.add_argument("--csv", help="선택: 결과를 저장할 CSV 경로")
    parser.add_argument("--limit", type=int, default=20, help="화면에 표시할 행 수")
    args = parser.parse_args()

    frame = fetch_us_equities()
    print(frame.head(max(args.limit, 0)).to_string(index=False))
    print(f"\n총 {len(frame):,}개 종목")

    if args.csv:
        frame.to_csv(args.csv, index=False, encoding="utf-8-sig")
        print(f"CSV 저장: {args.csv}")


if __name__ == "__main__":
    main()
