from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd


def demo_banners() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    campaigns = [
        ("LuckyFish", "It's Hello Win October — R4.5 Million", "Jackpot Promotion", 4_500_000, ["jackpot", "win", "cash"], "Habanero"),
        ("Hollywoodbets", "Stand a chance to win R3 Million", "Competition", 3_000_000, ["win", "bet now"], "Habanero"),
        ("Hollywoodbets", "App Jackpot R200,000 Monthly Prize Pool", "App Download Promotion", 200_000, ["app", "jackpot"], ""),
        ("LuckyFish", "100% Welcome Bonus", "Welcome Bonus", 1_000, ["welcome", "bonus"], ""),
        ("LuckyFish", "Aviator Weekend Race", "Aviator Promotion", 50_000, ["win", "aviator"], "Spribe"),
        ("Hollywoodbets", "Cashback on Live Casino", "Cashback Offer", 5_000, ["cashback", "casino"], "Evolution"),
    ]
    rows = []
    for offset in range(72):
        site, headline, category, prize, keywords, brand = campaigns[offset % len(campaigns)]
        captured = now - timedelta(days=offset * 3)
        rows.append(
            {
                "id": f"demo-{offset}",
                "capture_date": captured,
                "website": site,
                "position": offset % 4 + 1,
                "headline": headline,
                "categories": category,
                "category_list": [category],
                "ocr_text": f"{headline}\nBET NOW\nTs & Cs apply",
                "monetary_values": str(prize),
                "max_prize": float(prize),
                "detected_dates": "",
                "keywords": ", ".join(keywords),
                "brands": brand,
                "image_path": "",
                "description": f"Banner promoting a {category.lower()} with a strong call to action.",
                "is_new": offset < 6,
                "is_active": offset < 12,
                "colours": ["#082F36", "#8B5CF6", "#16D9C4"],
            }
        )
    return pd.DataFrame(rows)


def demo_runs() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    return pd.DataFrame(
        [
            {"website": site, "started_at": now - timedelta(days=day), "finished_at": now - timedelta(days=day, minutes=-3), "status": "success", "banners_found": 4, "error": None}
            for day in range(7)
            for site in ("LuckyFish", "Hollywoodbets")
        ]
    )

