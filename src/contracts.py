# src/contracts.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Sequence

# A rectangle crop: (x, y, w, h) in pixels on the screenshot
Rect = Tuple[int, int, int, int]

# Region key contract for one gear detail panel
REGION_KEYS: Sequence[str] = (
    "slot", "set", "rarity", "ilevel", "enhance",
    "main_stat", "main_value",
    "sub1_stat", "sub1_value",
    "sub2_stat", "sub2_value",
    "sub3_stat", "sub3_value",
    "sub4_stat", "sub4_value",
)

def validate_regions(regions: Dict[str, Rect]) -> None:
    missing = [k for k in REGION_KEYS if k not in regions]
    if missing:
        raise RuntimeError(f"RawCapture missing regions: {missing}")

@dataclass(frozen=True)
class RawCapture:
    screenshot_path: Path
    regions: Dict[str, Rect]
    timestamp_ms: int
    source: str = "emulator"
    meta: Optional[Dict[str, Any]] = None

class Recognizer:
    def recognize(self, cap: RawCapture):
        raise NotImplementedError