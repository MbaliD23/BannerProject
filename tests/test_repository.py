from datetime import date, datetime, timezone

import pandas as pd

from banner_analytics.repository import filter_frame


def test_filter_frame_combines_filters():
    frame = pd.DataFrame(
        [
            {"website": "LuckyFish", "category_list": ["Jackpot Promotion"], "capture_date": datetime(2026, 10, 1, tzinfo=timezone.utc), "headline": "R4.5m jackpot", "ocr_text": "win", "keywords": "jackpot", "brands": "Habanero", "max_prize": 4_500_000},
            {"website": "Hollywoodbets", "category_list": ["Competition"], "capture_date": datetime(2026, 9, 1, tzinfo=timezone.utc), "headline": "Competition", "ocr_text": "enter", "keywords": "win", "brands": "", "max_prize": 50_000},
        ]
    )
    result = filter_frame(frame, websites=["LuckyFish"], date_range=(date(2026, 10, 1), date(2026, 10, 31)), keyword="Habanero", min_prize=1_000_000)
    assert result["website"].tolist() == ["LuckyFish"]

