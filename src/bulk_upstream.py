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
    )

from src.regions_config import BULK_COLS, BULK_ROWS

def debug_dump_all_bulk_item_fields(
    shot_path: Path,
    root: Path,
    *,
    adb_serial: str | None = None,
) -> None:
    # Always dump full card crops too.
    debug_dump_bulk_crops(
        shot_path,
        root,
        adb_serial=adb_serial,
    )

    for item_index in range(BULK_COLS * BULK_ROWS):
        debug_dump_bulk_item_fields(
            shot_path,
            root,
            adb_serial=adb_serial,
            item_index=item_index,
        )

from pathlib import Path
import numpy as np
from PIL import Image


def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)


def purple_glow_score(crop_rgb: np.ndarray) -> float:
    arr = crop_rgb.astype(np.float32)

    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]

    # Crude purple/magenta condition:
    # red and blue high relative to green.
    purple = (
        (r > 90) &
        (b > 110) &
        (g < 90) &
        ((r + b) > (2.4 * g))
    )

    return float(purple.mean())


def rim_mask(h: int, w: int, thickness: int = 12) -> np.ndarray:
    mask = np.zeros((h, w), dtype=bool)
    mask[:thickness, :] = True
    mask[-thickness:, :] = True
    mask[:, :thickness] = True
    mask[:, -thickness:] = True
    return mask


def purple_glow_rim_score(crop_rgb: np.ndarray, thickness: int = 12) -> float:
    arr = crop_rgb.astype(np.float32)

    r = arr[..., 0]
    g = arr[..., 1]
    b = arr[..., 2]

    purple = (
        (r > 90) &
        (b > 110) &
        (g < 95) &
        ((r + b) > (2.2 * g))
    )

    rim = rim_mask(crop_rgb.shape[0], crop_rgb.shape[1], thickness=thickness)
    return float(purple[rim].mean())


def debug_otherworldly_score(path: Path) -> None:
    crop = load_rgb(path)
    full_score = purple_glow_score(crop)
    rim_score = purple_glow_rim_score(crop, thickness=12)

    print(
        path.parent.name,
        path.name,
        f"full={full_score:.4f}",
        f"rim={rim_score:.4f}",
    )

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]

    for item_index in range(16):
        path = (
            root
            / "data"
            / "captures"
            / "bulk_dumps"
            / "fields"
            / f"item_{item_index:02d}"
            / "otherworldly.png"
        )

        if path.exists():
            debug_otherworldly_score(path)

def predict_otherworldly_from_crop_hardcode(crop_rgb: np.ndarray) -> bool:
    return purple_glow_rim_score(crop_rgb, thickness=12) >= 0.05 


OTHERWORLDLY_RIM_THRESHOLD = 0.05
def predict_otherworldly_from_crop_debug(crop_rgb: np.ndarray) -> tuple[bool, float]:
    score = purple_glow_rim_score(crop_rgb, thickness=12)
    return score >= OTHERWORLDLY_RIM_THRESHOLD, score