# src/dump_crops.py
from __future__ import annotations

from pathlib import Path
from typing import Dict

import cv2

from src.contracts import RawCapture, Rect


def dump_crops_from_capture(cap: RawCapture, out_dir: Path) -> Path:
    """
    Dump one PNG per region key using the screenshot_path + regions from RawCapture.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(cap.screenshot_path))
    if img is None:
        raise RuntimeError(f"Could not read image: {cap.screenshot_path}")

    h, w = img.shape[:2]

    for key, (x, y, cw, ch) in cap.regions.items():
        if x < 0 or y < 0 or x + cw > w or y + ch > h:
            raise RuntimeError(f"Region out of bounds: {key}={(x,y,cw,ch)} for image {w}x{h}")

        crop = img[y:y + ch, x:x + cw]
        cv2.imwrite(str(out_dir / f"{key}.png"), crop)

    return out_dir


def dump_crops_from_image(img_path: Path, regions: Dict[str, Rect]) -> Path:
    """
    Backwards-compatible helper for your old workflow: dump crops from a PNG + regions dict.
    """
    cap = RawCapture(
        screenshot_path=img_path,
        regions=regions,
        timestamp_ms=0,
        source="file",
        meta=None,
    )
    out_dir = img_path.parent / (img_path.stem + "_crops")
    return dump_crops_from_capture(cap, out_dir)


if __name__ == "__main__":
    import sys
    from src.regions_config import REGIONS

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.dump_crops <path_to_png>")

    p = Path(sys.argv[1])
    out = dump_crops_from_image(p, REGIONS)
    print(f"Wrote crops to: {out}")