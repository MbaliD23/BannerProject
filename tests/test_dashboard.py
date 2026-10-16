from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_starts_with_demo_data(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Banner Analytics"
    assert len(app.metric) == 4

