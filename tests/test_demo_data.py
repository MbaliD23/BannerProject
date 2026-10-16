from banner_analytics.demo_data import demo_banners, demo_runs


def test_reference_snapshot_has_distinct_current_carousels():
    banners = demo_banners()

    assert len(banners) == 11
    assert banners.groupby("website").size().to_dict() == {"Hollywoodbets": 5, "LuckyFish": 6}
    assert banners["id"].is_unique
    assert banners["headline"].is_unique
    assert "Goal Getters 2026 — Win a Share of R500,000" in banners["headline"].tolist()
    assert "Halakasha — Win a Share of R5.3 Million" in banners["headline"].tolist()
    assert banners["image_path"].str.startswith("https://").sum() == 10


def test_reference_runs_match_carousel_counts():
    runs = demo_runs().set_index("website")

    assert runs.loc["LuckyFish", "banners_found"] == 6
    assert runs.loc["Hollywoodbets", "banners_found"] == 5
