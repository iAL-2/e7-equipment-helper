# src/upstream.py
from __future__ import annotations

from pathlib import Path

from src.regions_config import REGIONS_BAG, REGIONS_DETAIL
from src.profile_detect import detect_profile
from src.recognizer_closed import ClosedSetRecognizer, TemplateBank, _load_rgb
from src.contracts import RawCapture, validate_regions, CanonItem
from src.canonical import Vocab, Rules, load_vocab, load_rules, validate_canon_item

def run_once_or_raise(
    cap: RawCapture,
    recognizer: ClosedSetRecognizer,
    vocab: Vocab,
    rules: Rules,
) -> CanonItem:
    validate_regions(cap.regions)

    item, rec_errs = recognizer.recognize(cap)
    if item is None:
        raise RuntimeError(f"Recognition failed: {rec_errs}")

    ok, val_errs = validate_canon_item(item, vocab, rules)
    if not ok:
        raise RuntimeError(f"Validation failed: {val_errs}")

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

    img = _load_rgb(shot_path)
    bank = TemplateBank(root / "data" / "recognition" / "templates")

    profile = detect_profile(img, bank)
    print("Profile:", profile)
    regions = REGIONS_BAG if profile == "bag" else REGIONS_DETAIL

    cap = RawCapture(
        screenshot_path=shot_path,
        regions=regions,
        timestamp_ms=0,
        meta={"adb_serial": serial, "profile": profile},
    )

    DEBUG_DUMP_CROPS = True  # flip to True when you want dumps
    if DEBUG_DUMP_CROPS:
        from src.dump_crops import dump_crops_from_capture
        dump_crops_from_capture(cap, root / "data" / "captures" / "last_run_crops")

    recognizer = ClosedSetRecognizer.create(root=root)
    print("Recognizer type:", type(recognizer))
    item = run_once_or_raise(cap, recognizer, vocab, rules)
    print("OK CanonItem:", item)


if __name__ == "__main__":
    demo()