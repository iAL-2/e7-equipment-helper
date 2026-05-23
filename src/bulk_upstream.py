# src/bulk_upstream.py
from __future__ import annotations

from pathlib import Path

from src.contracts import RawCapture
from src.regions_config import ANCHOR_RECT, bulk_item_rects
from src.dump_crops import dump_crops_from_capture


DEBUG_DUMP_BULK_CROPS = True


def make_bulk_capture(
    shot_path: Path,
    *,
    adb_serial: str | None = None,
) -> RawCapture:
    return RawCapture(
        screenshot_path=shot_path,
        regions=bulk_item_rects(),
        timestamp_ms=0,
        meta={
            "adb_serial": adb_serial,
            "profile": "bulk",
        },
    )


def debug_dump_bulk_crops(
    shot_path: Path,
    root: Path,
    *,
    adb_serial: str | None = None,
) -> None:
    cap = make_bulk_capture(
        shot_path,
        adb_serial=adb_serial,
    )

    dump_crops_from_capture(
        cap,
        root / "data" / "captures" / "bulk_dumps",
        extra_regions={"anchor": ANCHOR_RECT},
    )