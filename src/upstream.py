# src/upstream.py
from __future__ import annotations

from pathlib import Path

from src.regions_config import REGIONS_BAG, REGIONS_DETAIL
from src.profile_detect import detect_profile
from src.recognizer_closed import ClosedSetRecognizer, TemplateBank, _load_rgb
from src.contracts import RawCapture, validate_regions, CanonItem
from src.canonical import Vocab, Rules, load_vocab, load_rules, validate_canon_item
import re
import subprocess
from typing import Tuple

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

def detect_first_adb_endpoint() -> Tuple[str, int, str]:
    """
    Returns (host, port, serial) for the first attached ADB device.

    Supports serials like:
    - 127.0.0.1:5559
    - emulator-5558

    For emulator-NNNN serials, we convert to:
    host = "127.0.0.1"
    port = NNNN + 1   # emulator console port -> adb port
    prefer_serial = original serial
    """
    result = subprocess.run(
        ["adb", "devices"],
        capture_output=True,
        text=True,
        check=True,
    )

    lines = result.stdout.splitlines()
    devices: list[str] = []

    for line in lines[1:]:  # skip "List of devices attached"
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])

    if not devices:
        raise RuntimeError("No ADB devices detected.")

    serial = devices[0]

    # Case 1: localhost-style serial, e.g. 127.0.0.1:5559
    if ":" in serial:
        host, port_str = serial.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            raise RuntimeError(f"Detected device has non-numeric port: {serial}")
        return host, port, serial

    # Case 2: emulator-style serial, e.g. emulator-5558
    m = re.fullmatch(r"emulator-(\d+)", serial)
    if m:
        console_port = int(m.group(1))
        adb_port = console_port + 1
        return "127.0.0.1", adb_port, serial

    # Fallback: non-emulator device attached
    # Keep serial for targeting, but host/port are not meaningful.
    # Use dummy localhost values only if your downstream connect code requires them.
    return "127.0.0.1", 5555, serial


def demo() -> None:
    root = Path(__file__).resolve().parents[1]
    vocab = load_vocab(root / "data" / "vocab.yaml")
    rules = load_rules(root / "data" / "rules.yaml")

    from src.adb_control import ADBConfig, adb_connect, adb_screencap_png

    host, port, serial = detect_first_adb_endpoint()
    cfg = ADBConfig(host=host, port=port, prefer_serial=serial)
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