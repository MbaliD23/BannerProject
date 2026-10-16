from decimal import Decimal

from banner_analytics.analyzer import categorize, extract_content, extract_money


def test_money_parses_million_and_commas():
    values = extract_money("Win R4.5 Million or R200,000 today")
    assert [value.amount for value in values] == [Decimal("4500000.0"), Decimal("200000")]


def test_multilabel_categories_are_extensible():
    taxonomy = {"categories": {"Jackpot Promotion": ["jackpot"], "App Download Promotion": ["app"]}}
    result = dict(categorize("Download the app for our jackpot", taxonomy))
    assert "Jackpot Promotion" in result
    assert "App Download Promotion" in result


def test_content_extracts_cta_and_terms():
    taxonomy = {"categories": {"Competition": ["win"]}, "keywords": ["win"], "brands": [], "social_platforms": []}
    content = extract_content("Stand a chance to WIN\nR3 Million\nBET NOW\nTs & Cs apply", taxonomy)
    assert content["cta_text"] == "Bet Now"
    assert content["terms_reference"] == "Ts & Cs apply"
    assert content["money"][0].amount == Decimal("3000000")

