from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook

from banner_analytics.exporter import excel_bytes


def test_excel_export_converts_timezone_aware_datetimes_to_local_naive_values():
    frame = pd.DataFrame(
        {
            "capture_date": [datetime(2026, 10, 16, 8, 30, tzinfo=timezone.utc)],
            "website": ["LuckyFish"],
            "position": [1],
            "headline": ["R4.5 Million jackpot"],
            "categories": ["Jackpot Promotion"],
            "ocr_text": ["WIN R4.5 MILLION"],
            "monetary_values": ["4500000"],
            "detected_dates": [""],
            "keywords": ["win, jackpot"],
            "brands": ["Habanero"],
            "image_path": ["banner.png"],
            "is_new": [True],
        }
    )

    workbook = load_workbook(BytesIO(excel_bytes(frame)))
    exported_date = workbook["Banner Analytics"]["A2"].value

    assert exported_date == datetime(2026, 10, 16, 10, 30)
    assert exported_date.tzinfo is None

