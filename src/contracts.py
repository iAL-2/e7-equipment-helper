# src/contracts.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Sequence
from typing import List, Literal, Protocol, Tuple

Slot = Literal["weapon", "helm", "armor", "necklace", "ring", "boots"]
Rarity = Literal["normal", "uncommon", "rare", "heroic", "epic"]

# Keep as str if you don’t want Literals yet
SetName = str
Stat = str

@dataclass(frozen=True)
class CanonStatLine:
    stat: Stat
    value: int
    confidence: float

@dataclass(frozen=True)
class CanonItem:
    schema_version: int
    slot: Slot
    set: SetName
    rarity: Rarity
    ilevel: int
    enhance: int
    main: CanonStatLine
    subs: Sequence[CanonStatLine]  # 0..4

@dataclass(frozen=True)
class RecError:
    field: str
    reason: str

class Recognizer(Protocol):
    def recognize(self, cap: RawCapture) -> Tuple[Optional[CanonItem], Sequence[RecError]]:
        ...

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