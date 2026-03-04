# src/upstream.py
from __future__ import annotations

from pathlib import Path

from src.contracts import RawCapture, validate_regions
from src.regions_config import REGIONS
from src.recognizer_easyocr import EasyOCRE7Recognizer
from src.canonical import Vocab, Rules, load_vocab, load_rules, CanonItem, canonicalize


def run_once_or_raise(
    cap: RawCapture,
    recognizer: EasyOCRE7Recognizer,
    vocab: Vocab,
    rules: Rules,
) -> CanonItem:
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

    from src.adb_control import ADBConfig, adb_connect, adb_screencap_png

    cfg = ADBConfig(host="127.0.0.1", port=5555, prefer_serial="127.0.0.1:5555")
    adb_connect(cfg)

    shot_path = root / "data" / "captures" / "gear_panel.png"
    serial = adb_screencap_png(cfg, shot_path)

    cap = RawCapture(
        screenshot_path=shot_path,
        regions=REGIONS,
        timestamp_ms=0,
        meta={"adb_serial": serial},
    )

    DEBUG_DUMP_CROPS = True  # flip to True when you want dumps
    if DEBUG_DUMP_CROPS:
        from src.dump_crops import dump_crops_from_capture
        dump_crops_from_capture(cap, root / "data" / "captures" / "last_run_crops")

    recognizer = EasyOCRE7Recognizer.create()
    print("Recognizer type:", type(recognizer))
    item = run_once_or_raise(cap, recognizer, vocab, rules)
    print("OK CanonItem:", item)


if __name__ == "__main__":
    demo()