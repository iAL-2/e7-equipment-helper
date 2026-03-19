# src/schema.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Literal

Slot = Literal["weapon", "helm", "armor", "necklace", "ring", "boots"]
Rarity = Literal["normal", "uncommon", "rare", "heroic", "epic"]

# Use the canonical stat token names you already use in vocab/rules.
Stat = str          # e.g. "atk", "atk_pct", "crit_chance", "speed", ...
SetName = str       # e.g. "speed", "lifesteal", ...

@dataclass(frozen=True)
class CanonStatLine:
    stat: Stat
    value: int               # store already-parsed integer (no OCR junk)
    is_percent: bool         # optional but can help sanity checks
    confidence: float        # classifier/template confidence

@dataclass(frozen=True)
class CanonItem:
    schema_version: int
    slot: Slot
    set: SetName
    rarity: Rarity
    ilevel: int
    enhance: int
    main: CanonStatLine
    subs: Sequence[CanonStatLine]   # 0..4

@dataclass(frozen=True)
class RecognizeError:
    field: str
    reason: str