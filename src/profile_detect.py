from __future__ import annotations
from pathlib import Path
from typing import Literal
import numpy as np

from src.regions_config import ANCHOR_RECT
from src.recognizer_closed import _crop, _to_gray, _best_slide_score, TemplateBank

Profile = Literal["bag", "detail", "detail_modify", "bulk"]

def _canon_profile_token(tok: str) -> Profile:
    if tok in ("detail", "detail__normal"):
        return "detail"
    if tok in ("detail_modify", "detail__modify"):
        return "detail_modify"
    return "bag"


def detect_profile(img_rgb: np.ndarray, bank: TemplateBank) -> Profile:
    crop_rgb = _crop(img_rgb, ANCHOR_RECT)
    crop_g = _to_gray(crop_rgb)

    candidates = [
        "bag",
        "detail",
        "detail__normal",
        "detail_modify",
        "detail__modify",
    ]

    scored: list[tuple[str, float]] = []
    for tok in candidates:
        templ = bank.gray("profile", tok)
        if templ is None:
            continue
        score = _best_slide_score(crop_g, templ, stride=1)
        scored.append((tok, score))

    if not scored:
        return "bag"   # fail-safe

    best_tok, _ = max(scored, key=lambda x: x[1])
    return _canon_profile_token(best_tok)