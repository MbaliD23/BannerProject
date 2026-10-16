from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd


REFERENCE_CAMPAIGNS = [
    {
        "website": "LuckyFish",
        "position": 1,
        "headline": "Progressive Jackpot — Stand a Chance to Win Big",
        "categories": ["Jackpot Promotion"],
        "prize": 0,
        "keywords": ["progressive jackpot", "win big", "bet now"],
        "brands": "LuckyFish",
        "ocr_text": "PROGRESSIVE JACKPOT\nSTAND A CHANCE TO WIN BIG\nBET NOW",
        "image_path": "https://content.luckyfish.co.za/LFGO_829_LF_Progressive_Jackpot_bc02f62ba1.webp",
        "description": "LuckyFish progressive jackpot campaign with a direct bet-now call to action.",
    },
    {
        "website": "LuckyFish",
        "position": 2,
        "headline": "20% More Luck on Deposits",
        "categories": ["Deposit Bonus"],
        "prize": 10_000,
        "keywords": ["deposit", "20% more luck", "deposit now"],
        "brands": "LuckyFish",
        "ocr_text": "ONE DAY ONLY\n20% MORE LUCK ON DEPOSITS BETWEEN R100 AND R10,000\nDEPOSIT NOW",
        "image_path": "https://content.luckyfish.co.za/LFGO_1482_LF_20_Deposits_webr_v2_ab1fe896ab.webp",
        "description": "One-day LuckyFish deposit bonus offering 20% more value on qualifying deposits.",
    },
    {
        "website": "LuckyFish",
        "position": 3,
        "headline": "It's Hello Win October — R4.5 Million",
        "categories": ["Jackpot Promotion", "Seasonal Campaign"],
        "prize": 4_500_000,
        "keywords": ["hello win october", "jackpot race", "cash"],
        "brands": "Habanero",
        "ocr_text": "IT'S HELLO WIN OCTOBER\nSTAND A CHANCE TO WIN A SHARE OF R4.5 MILLION IN CASH\nBET NOW",
        "image_path": "https://content.luckyfish.co.za/LFGO_1448_LF_Habanero_JPR_Oct_webr_3627d9b9c5.webp",
        "description": "Halloween-themed Habanero jackpot race promoting a R4.5 million cash prize pool.",
    },
    {
        "website": "LuckyFish",
        "position": 4,
        "headline": "Aviator — Now Boarding Your Luck",
        "categories": ["Aviator Promotion", "Competition"],
        "prize": 250_000,
        "keywords": ["aviator", "bonus bets", "bet now"],
        "brands": "Aviator",
        "ocr_text": "HAVE YOU STARTED NOW BOARDING YOUR LUCK?\nSTAND A CHANCE TO WIN A SHARE OF R250,000 IN BONUS BETS\nBET NOW",
        "image_path": "https://content.luckyfish.co.za/LFGO_1495_LF_Aviator_Promo_3_a812ae3f2b.webp",
        "description": "Aviator campaign offering a share of R250,000 in bonus bets.",
    },
    {
        "website": "LuckyFish",
        "position": 5,
        "headline": "Goal Getters 2026 — Win a Share of R500,000",
        "categories": ["Sports Betting Promotion", "Competition"],
        "prize": 500_000,
        "keywords": ["goal getters", "cash jackpots", "e-cin vouchers"],
        "brands": "Goal Getters 2026",
        "ocr_text": "GOAL GETTERS 2026\nSTAND A CHANCE TO WIN A SHARE OF R500,000 IN CASH JACKPOTS OR E-CIN VOUCHERS",
        "image_path": "https://content.luckyfish.co.za/LFGO_1264_LF_The_Beautiful_Game_2026_Rotator_3f58893063.webp",
        "description": "Football campaign offering cash jackpots and e-cin vouchers worth R500,000.",
    },
    {
        "website": "LuckyFish",
        "position": 6,
        "headline": "Jackpot Kickoff — Stand a Chance to Win Big",
        "categories": ["Jackpot Promotion", "Sports Betting Promotion"],
        "prize": 0,
        "keywords": ["jackpot kickoff", "win big", "football"],
        "brands": "Jackpot Kickoff",
        "ocr_text": "JACKPOT KICKOFF\nSTAND A CHANCE TO WIN BIG",
        "image_path": "https://content.luckyfish.co.za/LFGO_1253_LF_Jackpot_Kick_Off_2026_Rotator_d95ee545e2.webp",
        "description": "LuckyFish football jackpot campaign encouraging customers to play for a growing prize.",
    },
    {
        "website": "Hollywoodbets",
        "position": 1,
        "headline": "Halakasha — Win a Share of R5.3 Million",
        "categories": ["Sports Betting Promotion", "Competition"],
        "prize": 5_300_000,
        "keywords": ["halakasha", "cash", "betting vouchers", "EPL experience"],
        "brands": "Halakasha",
        "ocr_text": "HALAKASHA — LET'S PLAY\nSTAND A CHANCE TO WIN A SHARE OF R5.3 MILLION IN CASH, BETTING VOUCHERS AND AN EPL EXPERIENCE",
        "image_path": "https://blog.hollywoodbets.net/wp-content/uploads/2026/08/HWSB1383_HALAKASHA_12_BLOG-1024x512.jpg",
        "description": "Long-running soccer campaign combining cash, betting vouchers, and an EPL experience.",
    },
    {
        "website": "Hollywoodbets",
        "position": 2,
        "headline": "Red Tiger & Red Baron — Home Makeovers and Cash Prizes",
        "categories": ["Competition", "Slot Promotion"],
        "prize": 1_000_000,
        "keywords": ["home makeover", "cash prizes", "red tiger", "red baron"],
        "brands": "Red Tiger, Red Baron",
        "ocr_text": "STAND A CHANCE TO WIN ONE OF TWO HOME MAKEOVERS OR A SHARE OF OVER R1 MILLION IN CASH PRIZES\nRED TIGER\nRED BARON",
        "image_path": "",
        "description": "October slots campaign offering two home makeovers and more than R1 million in cash prizes.",
    },
    {
        "website": "Hollywoodbets",
        "position": 3,
        "headline": "Spina Zonke Jackpot Race — R3 Million",
        "categories": ["Jackpot Promotion", "Slot Promotion"],
        "prize": 3_000_000,
        "keywords": ["spina zonke", "jackpot race", "cash"],
        "brands": "Habanero, Spina Zonke",
        "ocr_text": "SPINA ZONKE JACKPOT RACE\nSTAND A CHANCE TO WIN A SHARE OF R3 MILLION IN CASH\nBET NOW",
        "image_path": "https://blog.hollywoodbets.net/wp-content/uploads/2026/10/Hollywoodbets-Spina-Zonke-Jackpot-Race-October-2026-1024x512.jpg",
        "description": "Spina Zonke jackpot race advertising a R3 million cash prize pool.",
    },
    {
        "website": "Hollywoodbets",
        "position": 4,
        "headline": "App Jackpot — R200,000 Monthly Prize Pool",
        "categories": ["App Download Promotion", "Jackpot Promotion"],
        "prize": 200_000,
        "keywords": ["app jackpot", "monthly prize pool", "download app"],
        "brands": "Hollywoodbets App",
        "ocr_text": "APP JACKPOT\nR200,000 MONTHLY PRIZE POOL\nDOWNLOAD THE APP AND BET NOW",
        "image_path": "https://blog.hollywoodbets.net/wp-content/uploads/2026/09/Hollywoodbets-App-Jackpot-October-2026-1024x512.jpg",
        "description": "Hollywoodbets app acquisition campaign featuring a R200,000 monthly prize pool.",
    },
    {
        "website": "Hollywoodbets",
        "position": 5,
        "headline": "October Heat — Win a Share of R3 Million",
        "categories": ["Competition", "Slot Promotion", "Seasonal Campaign"],
        "prize": 3_000_000,
        "keywords": ["october heat", "cash", "tournament", "bet now"],
        "brands": "EGT Digital",
        "ocr_text": "OCTOBER HEAT\nSTAND A CHANCE TO WIN A SHARE OF R3 MILLION IN CASH RIGHT NOW\nBET NOW",
        "image_path": "https://blog.hollywoodbets.net/wp-content/uploads/2026/10/HWSZ0194_EGT-October-Heat-Network-Tournament_BLOG-1024x512.jpg",
        "description": "Four-phase EGT Digital slots tournament with R3 million in cash prizes.",
    },
]


def demo_banners() -> pd.DataFrame:
    """Return a non-repeating reference snapshot of the current homepage campaigns."""
    captured = datetime.now(timezone.utc)
    rows = []
    for index, campaign in enumerate(REFERENCE_CAMPAIGNS):
        categories = campaign["categories"]
        rows.append(
            {
                "id": f"reference-{campaign['website'].lower()}-{campaign['position']}",
                "capture_date": captured - timedelta(seconds=index),
                "website": campaign["website"],
                "position": campaign["position"],
                "headline": campaign["headline"],
                "categories": ", ".join(categories),
                "category_list": categories,
                "ocr_text": campaign["ocr_text"],
                "monetary_values": str(campaign["prize"]) if campaign["prize"] else "",
                "max_prize": float(campaign["prize"]),
                "detected_dates": "16 October 2026 snapshot",
                "keywords": ", ".join(campaign["keywords"]),
                "brands": campaign["brands"],
                "image_path": campaign["image_path"],
                "description": campaign["description"],
                "is_new": True,
                "is_active": True,
                "colours": ["#07343A", "#6F42D9", "#D5A800"],
            }
        )
    return pd.DataFrame(rows)


def demo_runs() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    return pd.DataFrame(
        [
            {"website": "LuckyFish", "started_at": now - timedelta(minutes=4), "finished_at": now - timedelta(minutes=2), "status": "success", "banners_found": 6, "error": None},
            {"website": "Hollywoodbets", "started_at": now - timedelta(minutes=4), "finished_at": now - timedelta(minutes=2), "status": "success", "banners_found": 5, "error": None},
        ]
    )
