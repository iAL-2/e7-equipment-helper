# src/recognizer_easyocr.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List

import cv2
import numpy as np
import easyocr

from src.contracts import RawCapture, Recognizer, Rect, validate_regions
from src.canonical import ParsedItem, ParsedStatLine
from src.canonical import norm_stat

# Simple helpers

def crop(img: np.ndarray, r: Rect) -> np.ndarray:
    x, y, w, h = r
    return img[y:y+h, x:x+w]

def preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    # grayscale + scale up for better OCR on small text
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    # light threshold to increase contrast
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th

def ocr_text(reader: easyocr.Reader, img: np.ndarray, allowlist: Optional[str] = None, mode: str = "best") -> Tuple[Optional[str], float]:
    """
    mode:
      - "best": return the single best-confidence chunk
      - "concat": concatenate all chunks top-to-bottom, left-to-right (good for multi-line labels)
    """
    proc = preprocess_for_ocr(img)
    results = reader.readtext(proc, detail=1, paragraph=False, allowlist=allowlist)
    if not results:
        return None, 0.0

    if mode == "best":
        best = max(results, key=lambda t: float(t[2]))
        text = str(best[1]).strip()
        conf = float(best[2])
        return (None, 0.0) if text == "" else (text, conf)

    if mode == "concat":
        # Each item: [bbox, text, conf]
        # bbox is 4 points: [[x,y], [x,y], [x,y], [x,y]]
        def key_fn(t):
            bbox = t[0]
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            return (min(ys), min(xs))  # top-to-bottom, then left-to-right

        ordered = sorted(results, key=key_fn)
        texts = [str(t[1]).strip() for t in ordered if str(t[1]).strip() != ""]
        if not texts:
            return None, 0.0

        # join with space (your _basic_norm later turns whitespace into underscores)
        joined = " ".join(texts)
        conf = min(float(t[2]) for t in ordered)  # conservative
        return joined, conf

    raise ValueError(f"Unknown mode: {mode}")

def parse_int_maybe(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    # keep digits only
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits == "":
        return None
    return int(digits)

def parse_float_maybe(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    # keep digits and dot
    kept = []
    dot_used = False
    for ch in s:
        if ch.isdigit():
            kept.append(ch)
        elif ch == "." and not dot_used:
            kept.append(".")
            dot_used = True
    t = "".join(kept)
    if t in ("", "."):
        return None
    return float(t)

def upgrade_pct(stat_label: Optional[str], value_text: Optional[str]) -> Optional[str]:
    if stat_label is None:
        return None
    if value_text is None:
        return stat_label
    if "%" in value_text:
        if stat_label == "atk":
            return "atk_pct"
        if stat_label == "hp":
            return "hp_pct"
        if stat_label == "def":
            return "def_pct"
    return stat_label

@dataclass
class EasyOCRE7Recognizer(Recognizer):
    """
    First-pass recognizer using EasyOCR on each cropped region.

    Notes:
    - We keep allowlists for numeric-heavy fields to reduce garbage.
    - Stat labels (main_stat/sub*_stat) are read as plain text for now; you'll normalize later.
    """
    reader: easyocr.Reader

    @classmethod
    def create(cls) -> "EasyOCRE7Recognizer":
        # english-only is fine for E7 UI; GPU False keeps it simple
        r = easyocr.Reader(["en"], gpu=False)
        return cls(reader=r)

    def recognize(self, cap: RawCapture) -> ParsedItem:
        validate_regions(cap.regions)

        img = cv2.imread(str(cap.screenshot_path))
        if img is None:
            raise RuntimeError(f"Could not read screenshot: {cap.screenshot_path}")

        # resolution guard (calibrated on this)
        h, w = img.shape[:2]
        if (w, h) != (1920, 1080):
            raise RuntimeError(f"Unexpected screenshot size {w}x{h}; calibrated for 1920x1080.")

        # ---- header fields ----
        slot_txt, slot_c = ocr_text(self.reader, crop(img, cap.regions["slot"]), mode="concat")
        set_txt, set_c = ocr_text(self.reader, crop(img, cap.regions["set"]), mode="concat")
        rarity_txt, rarity_c = ocr_text(self.reader, crop(img, cap.regions["rarity"]), mode="concat")
        

        ilevel_txt, ilevel_c = ocr_text(self.reader, crop(img, cap.regions["ilevel"]), allowlist="0123456789")
        enhance_txt, enhance_c = ocr_text(self.reader, crop(img, cap.regions["enhance"]), allowlist="0123456789+")

        print("OCR ilevel:", ilevel_txt, "conf", ilevel_c)
        print("OCR enhance:", enhance_txt, "conf", enhance_c)

        ilevel = parse_int_maybe(ilevel_txt)
        enhance = parse_int_maybe(enhance_txt)
        if enhance is None:
            enhance = 0

        # ---- main ----
        main_stat_txt, main_stat_c = ocr_text(self.reader, crop(img, cap.regions["main_stat"]), mode="concat")
        main_val_txt, main_val_c = ocr_text(self.reader, crop(img, cap.regions["main_value"]), allowlist="0123456789.%+")
        main_val = parse_float_maybe(main_val_txt)

        main_stat_norm = norm_stat(main_stat_txt)
        main_stat_norm = upgrade_pct(main_stat_norm, main_val_txt)

        main = ParsedStatLine(
            stat=main_stat_norm,
            value=main_val,
            confidence=min(main_stat_c, main_val_c) if (main_stat_norm is not None and main_val is not None) else 0.0,
        )

        # ---- subs ----
        subs: List[ParsedStatLine] = []
        for i in range(1, 5):
            stat_k = f"sub{i}_stat"
            val_k = f"sub{i}_value"

            st_txt, st_c = ocr_text(self.reader, crop(img, cap.regions[stat_k]))
            val_txt, val_c = ocr_text(self.reader, crop(img, cap.regions[val_k]), allowlist="0123456789.%+")

            val = parse_float_maybe(val_txt)
            if st_txt is None or val is None:
                continue

            st_norm = norm_stat(st_txt)
            st_norm = upgrade_pct(st_norm, val_txt)
            if st_norm is None:
                continue

            subs.append(ParsedStatLine(
                stat=st_norm,
                value=val,
                confidence=min(st_c, val_c),
            ))

        return ParsedItem(
            schema_version=1,
            slot=slot_txt,
            set=set_txt,
            rarity=rarity_txt,
            ilevel=ilevel,
            enhance=enhance,
            main=main,
            subs=subs,
        )