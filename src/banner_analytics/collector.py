from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from PIL import Image
from playwright.sync_api import Locator, Page, sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from .analyzer import extract_content, visual_analysis
from .config import get_settings, load_sites
from .database import session_scope
from .models import Banner, BannerCategory, CaptureRun, DetectedDate, MonetaryValue, Website
from .ocr import extract_text

logger = logging.getLogger(__name__)


def _first_visible(page: Page, selectors: list[str]) -> Locator:
    for selector in selectors:
        locator = page.locator(selector)
        for index in range(min(locator.count(), 10)):
            candidate = locator.nth(index)
            try:
                box = candidate.bounding_box()
                if candidate.is_visible() and box and box["width"] >= 450 and box["height"] >= 100:
                    return candidate
            except Exception:
                continue
    raise RuntimeError(f"No sufficiently large carousel found; tried: {selectors}")


def _perceptual_hash(path: Path) -> str:
    image = Image.open(path).convert("L").resize((9, 8))
    pixels = list(image.getdata())
    bits = [pixels[row * 9 + col] > pixels[row * 9 + col + 1] for row in range(8) for col in range(8)]
    return f"{sum(1 << idx for idx, bit in enumerate(bits) if bit):016x}"


class BannerCollector:
    def __init__(self, site: dict):
        self.site = site
        self.settings = get_settings()

    def _capture_slides(self, page: Page, run_id) -> list[dict]:
        carousel = _first_visible(page, self.site["carousel_selectors"])
        captures: list[dict] = []
        seen: set[str] = set()
        folder = self.settings.storage_path / self.site["key"] / datetime.now().strftime("%Y/%m/%d")
        folder.mkdir(parents=True, exist_ok=True)

        def save_target(target: Locator) -> bool:
            position = len(captures) + 1
            try:
                if not target.is_visible():
                    return False
                filename = f"{run_id}-{position:02d}.png"
                path = folder / filename
                target.screenshot(path=str(path), animations="disabled")
                content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                if content_hash in seen:
                    path.unlink(missing_ok=True)
                    return False
                seen.add(content_hash)
                image = target.locator("img").first
                source_url = image.get_attribute("src") if image.count() else None
                link = target.locator("a").first
                href = link.get_attribute("href") if link.count() else None
                captures.append(
                    {
                        "position": position + 1,
                        "path": path,
                        "content_hash": content_hash,
                        "perceptual_hash": _perceptual_hash(path),
                        "source_url": urljoin(self.site["url"], source_url) if source_url else None,
                        "clickthrough_url": urljoin(self.site["url"], href) if href else None,
                    }
                )
                return True
            except Exception as exc:
                logger.warning("Skipping slide %s on %s: %s", position, self.site["key"], exc)
                return False

        slide_selector = next(
            (selector for selector in self.site["slide_selectors"] if carousel.locator(selector).count()),
            None,
        )
        slides = carousel.locator(slide_selector) if slide_selector else None
        if slides:
            for position in range(min(slides.count(), 20)):
                save_target(slides.nth(position))

        # Rotate dynamic/virtualized carousels so lazily rendered slides are also captured.
        next_button = None
        for selector in self.site.get("next_selectors", []):
            candidate = page.locator(selector).first
            try:
                if candidate.count() and candidate.is_visible():
                    next_button = candidate
                    break
            except Exception:
                continue
        stale_rotations = 0
        for _ in range(20 if next_button else 0):
            before = len(captures)
            try:
                next_button.click()
                time.sleep(0.35)
            except Exception:
                break
            live_slides = carousel.locator(slide_selector) if slide_selector else None
            if live_slides:
                for index in range(min(live_slides.count(), 20)):
                    save_target(live_slides.nth(index))
            if len(captures) == before:
                stale_rotations += 1
                if stale_rotations >= 2:
                    break
            else:
                stale_rotations = 0

        if not captures:
            path = folder / f"{run_id}-01.png"
            carousel.screenshot(path=str(path), animations="disabled")
            captures.append(
                {
                    "position": 1,
                    "path": path,
                    "content_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "perceptual_hash": _perceptual_hash(path),
                    "source_url": None,
                    "clickthrough_url": None,
                }
            )
        return captures

    @retry(
        wait=wait_exponential(min=2, max=20),
        stop=stop_after_attempt(get_settings().retries),
        reraise=True,
    )
    def collect(self) -> int:
        with session_scope() as session:
            website = session.query(Website).filter_by(key=self.site["key"]).one_or_none()
            if website is None:
                website = Website(key=self.site["key"], name=self.site["name"], url=self.site["url"])
                session.add(website)
                session.flush()
            run = CaptureRun(website_id=website.id, status="running")
            session.add(run)
            session.flush()
            run_id = run.id

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.settings.headless)
                page = browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
                page.set_default_timeout(self.settings.timeout_ms)
                page.goto(self.site["url"], wait_until=self.site.get("wait_until", "networkidle"))
                for selector in self.site.get("dismiss_selectors", []):
                    try:
                        page.locator(selector).first.click(timeout=1500)
                    except Exception:
                        pass
                captures = self._capture_slides(page, run_id)
                browser.close()

            with session_scope() as session:
                run = session.get(CaptureRun, run_id)
                previous_hashes = {
                    row[0]
                    for row in session.query(Banner.content_hash)
                    .filter(Banner.website_id == run.website_id, Banner.capture_run_id != run.id)
                    .all()
                }
                for item in captures:
                    text, ocr_engine = extract_text(item["path"])
                    content = extract_content(text)
                    colours, flags, description = visual_analysis(text, item["path"])
                    banner = Banner(
                        capture_run_id=run.id,
                        website_id=run.website_id,
                        position=item["position"],
                        unique_identifier=f"{self.site['key']}-{item['perceptual_hash']}",
                        content_hash=item["content_hash"],
                        perceptual_hash=item["perceptual_hash"],
                        image_path=str(item["path"]),
                        source_image_url=item["source_url"],
                        clickthrough_url=item["clickthrough_url"],
                        ocr_text=text,
                        headline=content["headline"],
                        subheadline=content["subheadline"],
                        cta_text=content["cta_text"],
                        terms_reference=content["terms_reference"],
                        detected_brands=content["brands"],
                        social_platforms=content["social_platforms"],
                        promotional_keywords=content["keywords"],
                        primary_colours=colours,
                        visual_flags=flags,
                        automated_description=description,
                        is_new=item["content_hash"] not in previous_hashes,
                        raw_metadata={"ocr_engine": ocr_engine},
                    )
                    banner.categories = [BannerCategory(category=name, confidence=confidence) for name, confidence in content["categories"]]
                    banner.monetary_values = [MonetaryValue(raw_text=value.raw_text, amount=value.amount) for value in content["money"]]
                    banner.detected_dates = [DetectedDate(raw_text=value.raw_text, parsed_date=value.parsed_date, date_type=value.date_type) for value in content["dates"]]
                    session.add(banner)
                run.status = "success"
                run.banners_found = len(captures)
                run.finished_at = datetime.now(timezone.utc)
            return len(captures)
        except Exception as exc:
            logger.exception("Collection failed for %s", self.site["key"])
            with session_scope() as session:
                run = session.get(CaptureRun, run_id)
                run.status = "failed"
                run.error_message = str(exc)[:2000]
                run.finished_at = datetime.now(timezone.utc)
            raise


def collect_all() -> dict[str, int | str]:
    results: dict[str, int | str] = {}
    for site in load_sites():
        try:
            results[site["key"]] = BannerCollector(site).collect()
        except Exception as exc:
            results[site["key"]] = f"failed: {exc}"
    return results

