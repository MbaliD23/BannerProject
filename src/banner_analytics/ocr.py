from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from .config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _easy_reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False)


def _easyocr(path: Path) -> str:
    results = _easy_reader().readtext(str(path), detail=0, paragraph=False)
    return "\n".join(str(item).strip() for item in results if str(item).strip())


def _tesseract(path: Path) -> str:
    import pytesseract
    from PIL import Image

    if get_settings().tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = get_settings().tesseract_cmd
    return pytesseract.image_to_string(Image.open(path), config="--psm 6").strip()


def extract_text(path: Path) -> tuple[str, str]:
    preferred = get_settings().ocr_engine
    engines = [("easyocr", _easyocr), ("tesseract", _tesseract)]
    if preferred == "tesseract":
        engines.reverse()
    errors = []
    for name, engine in engines:
        try:
            return engine(path), name
        except Exception as exc:  # OCR backends fail independently.
            logger.warning("OCR engine %s failed for %s: %s", name, path, exc)
            errors.append(f"{name}: {exc}")
    raise RuntimeError("All OCR engines failed: " + "; ".join(errors))

