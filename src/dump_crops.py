# src/dump_crops.py
from __future__ import annotations

from pathlib import Path
import cv2

from src.regions_config import REGIONS

def main(img_path: str) -> None:
    p = Path(img_path)
    img = cv2.imread(str(p))
    if img is None:
        raise RuntimeError(f"Could not read image: {p}")

    out_dir = p.parent / (p.stem + "_crops")
    out_dir.mkdir(parents=True, exist_ok=True)

    for key, (x, y, w, h) in REGIONS.items():
        crop = img[y:y+h, x:x+w]
        out_path = out_dir / f"{key}.png"
        cv2.imwrite(str(out_path), crop)

    print(f"Wrote crops to: {out_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.dump_crops <path_to_png>")
    main(sys.argv[1])