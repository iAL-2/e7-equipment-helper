# src/bulk_upstream.py
from __future__ import annotations

from pathlib import Path

from src.contracts import RawCapture
from src.regions_config import ANCHOR_RECT, bulk_item_rects, bulk_item_regions
from src.dump_crops import dump_crops_from_capture


DEBUG_DUMP_BULK_CROPS = True


BULK_PLACEHOLDER_SLOT = "weapon"
BULK_PLACEHOLDER_RARITY = "epic"
BULK_PLACEHOLDER_OTHERWORLDLY = False

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

def debug_dump_bulk_item_fields(
    shot_path: Path,
    root: Path,
    *,
    adb_serial: str | None = None,
    item_index: int = 0,
) -> None:
    cap = RawCapture(
        screenshot_path=shot_path,
        regions=bulk_item_regions(item_index),
        timestamp_ms=0,
        meta={
            "adb_serial": adb_serial,
            "profile": "bulk",
            "item_index": item_index,
        },
    )

    dump_crops_from_capture(
        cap,
        root / "data" / "captures" / "bulk_dumps" / "fields" / f"item_{item_index:02d}",
        extra_regions={"anchor": ANCHOR_RECT},
    )

from src.regions_config import BULK_COLS, BULK_ROWS

def debug_dump_all_bulk_item_fields(
    shot_path: Path,
    root: Path,
    *,
    adb_serial: str | None = None,
) -> None:
    for item_index in range(BULK_COLS * BULK_ROWS):
        debug_dump_bulk_item_fields(
            shot_path,
            root,
            adb_serial=adb_serial,
            item_index=item_index,
        )