# src/upstream.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, Sequence

from src.canonical import (
    Vocab, Rules,
    load_vocab, load_rules, load_yaml,
    ParsedItem, parse_parsed_item,
    CanonItem,
    canonicalize,
)

# A rectangle crop: (x, y, w, h) in pixels on the screenshot
Rect = Tuple[int, int, int, int]

# Region key contract for one gear detail panel
REGION_KEYS: Sequence[str] = (
    # identity / header
    "slot",
    "set",
    "rarity",
    "ilevel",
    "enhance",

    # main stat
    "main_stat",
    "main_value",

    # up to 4 subs (stat + value per line)
    "sub1_stat", "sub1_value",
    "sub2_stat", "sub2_value",
    "sub3_stat", "sub3_value",
    "sub4_stat", "sub4_value",
)

def validate_regions(regions: Dict[str, Rect]) -> None:
    missing = [k for k in REGION_KEYS if k not in regions]
    if missing:
        raise RuntimeError(f"RawCapture missing regions: {missing}")

def dummy_regions(rect: Rect = (0, 0, 10, 10)) -> Dict[str, Rect]:
    return {k: rect for k in REGION_KEYS}


@dataclass(frozen=True)
class RawCapture:
    """
    One capture of a gear detail panel.
    """
    screenshot_path: Path
    regions: Dict[str, Rect]
    timestamp_ms: int
    source: str = "emulator"
    meta: Optional[Dict[str, Any]] = None


class Recognizer:
    """
    Interface: implement recognize() to convert RawCapture -> ParsedItem.
    """
    def recognize(self, cap: RawCapture) -> ParsedItem:
        raise NotImplementedError


class YamlRecognizer(Recognizer):
    """
    Temporary recognizer: ignores image, loads a ParsedItem from a YAML fixture.
    """
    def __init__(self, parsed_yaml_path: Path):
        self.parsed_yaml_path = parsed_yaml_path

    def recognize(self, cap: RawCapture) -> ParsedItem:
        d = load_yaml(self.parsed_yaml_path)
        return parse_parsed_item(d)


def run_once_or_raise(
    cap: RawCapture,
    recognizer: Recognizer,
    vocab: Vocab,
    rules: Rules,
) -> CanonItem:
    """
    capture -> recognize -> canonicalize
    If canonicalize fails, raise immediately.
    Returns CanonItem on success (so downstream analysis can consume it).
    """
    validate_regions(cap.regions)

    parsed = recognizer.recognize(cap)
    item, errs = canonicalize(parsed, vocab, rules)
    if errs or item is None:
        raise RuntimeError(f"Canonicalization failed: {errs}")

    return item


def demo() -> None:
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")

    cap = RawCapture(
        screenshot_path=root / "data" / "dummy_screenshot.png",
        regions=dummy_regions(),
        timestamp_ms=0,
        meta={"note": "demo"},
    )

    recognizer = YamlRecognizer(root / "data" / "parseditem.good.yaml")
    item = run_once_or_raise(cap, recognizer, vocab, rules)
    print("OK CanonItem:", item)


if __name__ == "__main__":
    demo()