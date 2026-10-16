from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import dateparser
import numpy as np
from PIL import Image

from .config import load_taxonomy


MONEY_RE = re.compile(
    r"(?i)(?:R|ZAR)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(thousand|k|million|mil|m)?"
)
DATE_RE = re.compile(
    r"(?i)\b(?:\d{1,2}[\s/-](?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|\d{1,2})[\s/-]\d{2,4}|\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{2,4})?)\b"
)
CTA_PATTERNS = ["bet now", "play now", "join now", "download now", "enter now", "learn more"]


@dataclass(frozen=True)
class MoneyMatch:
    raw_text: str
    amount: Decimal


@dataclass(frozen=True)
class DateMatch:
    raw_text: str
    parsed_date: date | None
    date_type: str


def extract_money(text: str) -> list[MoneyMatch]:
    values: list[MoneyMatch] = []
    for match in MONEY_RE.finditer(text):
        base = Decimal(match.group(1).replace(",", ""))
        suffix = (match.group(2) or "").lower()
        multiplier = Decimal("1000000") if suffix in {"million", "mil", "m"} else Decimal("1000") if suffix in {"thousand", "k"} else Decimal("1")
        values.append(MoneyMatch(match.group(0), base * multiplier))
    return values


def extract_dates(text: str) -> list[DateMatch]:
    lowered = text.lower()
    result: list[DateMatch] = []
    for match in DATE_RE.finditer(text):
        raw = match.group(0)
        parsed = dateparser.parse(raw, settings={"DATE_ORDER": "DMY", "PREFER_DATES_FROM": "future"})
        context = lowered[max(0, match.start() - 35) : match.end() + 10]
        kind = "draw" if "draw" in context else "expiry" if any(word in context for word in ("expire", "ends", "until")) else "start" if any(word in context for word in ("start", "from")) else "unspecified"
        result.append(DateMatch(raw, parsed.date() if parsed else None, kind))
    return result


def categorize(text: str, taxonomy: dict | None = None) -> list[tuple[str, float]]:
    taxonomy = taxonomy or load_taxonomy()
    lowered = text.lower()
    matches: list[tuple[str, float]] = []
    for category, rules in taxonomy.get("categories", {}).items():
        hits = sum(1 for rule in rules if rule.lower() in lowered)
        if hits:
            matches.append((category, min(0.55 + hits * 0.15, 0.98)))
    return sorted(matches, key=lambda item: item[1], reverse=True) or [("Uncategorised", 0.25)]


def extract_content(text: str, taxonomy: dict | None = None) -> dict:
    taxonomy = taxonomy or load_taxonomy()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lowered = text.lower()
    cta = next((cta.title() for cta in CTA_PATTERNS if cta in lowered), None)
    terms = next((line for line in lines if any(x in line.lower() for x in ("t&c", "terms", "apply"))), None)
    keywords = [word for word in taxonomy.get("keywords", []) if word.lower() in lowered]
    brands = [brand for brand in taxonomy.get("brands", []) if brand.lower() in lowered]
    social = [platform for platform in taxonomy.get("social_platforms", []) if platform.lower() in lowered]
    return {
        "headline": max(lines, key=len) if lines else None,
        "subheadline": lines[1] if len(lines) > 1 else None,
        "cta_text": cta,
        "terms_reference": terms,
        "keywords": keywords,
        "brands": brands,
        "social_platforms": social,
        "categories": categorize(text, taxonomy),
        "money": extract_money(text),
        "dates": extract_dates(text),
    }


def dominant_colours(path: Path, count: int = 4) -> list[str]:
    image = Image.open(path).convert("RGB")
    image.thumbnail((160, 90))
    pixels = np.asarray(image).reshape(-1, 3)
    quantized = (pixels // 48) * 48 + 24
    colours, counts = np.unique(quantized, axis=0, return_counts=True)
    top = colours[np.argsort(counts)[-count:][::-1]]
    return ["#%02x%02x%02x" % tuple(int(channel) for channel in colour) for colour in top]


def visual_analysis(text: str, image_path: Path) -> tuple[list[str], dict, str]:
    lowered = text.lower()
    flags = {
        "money_graphics": bool(MONEY_RE.search(text) or any(x in lowered for x in ("cash", "prize"))),
        "mobile_app_graphics": any(x in lowered for x in ("app", "download", "mobile")),
        "game_graphics": any(x in lowered for x in ("game", "slot", "casino", "aviator", "poker")),
        "jackpot_messaging": "jackpot" in lowered,
        "branded_elements": bool(extract_content(text)["brands"]),
    }
    categories = [name for name, _ in categorize(text)]
    prize = extract_money(text)
    category_phrase = categories[0].lower() if categories else "promotion"
    prize_phrase = f" featuring a {prize[0].raw_text} cash value" if prize else ""
    cta_phrase = " Includes a clear call to action." if any(x in lowered for x in CTA_PATTERNS) else ""
    description = f"Banner promoting a {category_phrase}{prize_phrase}.{cta_phrase}".strip()
    return dominant_colours(image_path), flags, description

