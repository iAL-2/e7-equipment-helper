from __future__ import annotations
from pathlib import Path
from typing import Literal
import numpy as np

from src.regions_config import ANCHOR_RECT
from src.recognizer_closed import _crop, _to_gray, _best_slide_score, TemplateBank

Profile = Literal["bag", "detail"]

def detect_profile(img_rgb: np.ndarray, bank: TemplateBank) -> Profile:
    crop_rgb = _crop(img_rgb, ANCHOR_RECT)
    crop_g = _to_gray(crop_rgb)

    bag_t = bank.gray("profile", "bag")
    det_t = bank.gray("profile", "detail")
    if bag_t is None or det_t is None:
        # fail-safe: default to bag until both templates exist
        return "bag"

    s_bag = _best_slide_score(crop_g, bag_t, stride=1)
    s_det = _best_slide_score(crop_g, det_t, stride=1)
    return "bag" if s_bag > s_det else "detail"