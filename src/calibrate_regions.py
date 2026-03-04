from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List

import cv2

from src.upstream import REGION_KEYS, Rect

# For each REGION_KEYS entry:
# - click Top-Left corner
# - click Bottom-Right corner
# Press ESC to abort.
# When finished, it prints a Python dict you can paste as REGIONS.

def main(img_path: str) -> None:
    p = Path(img_path)
    img = cv2.imread(str(p))
    if img is None:
        raise RuntimeError(f"Could not read image: {p}")

    points: List[Tuple[int, int]] = []

    def current_key_name() -> str:
        i = len(points) // 2
        if i >= len(REGION_KEYS):
            return "DONE"
        return REGION_KEYS[i]

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            print(f"[{current_key_name()}] click {len(points)%2 or 2}/2: ({x},{y})")

    cv2.namedWindow("calibrate", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("calibrate", on_mouse)

    while True:
        view = img.copy()
        label = f"Click TL then BR for: {current_key_name()}  ({len(points)}/{2*len(REGION_KEYS)})"
        cv2.putText(view, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # draw already-completed rectangles
        for i in range(len(points)//2):
            (x1, y1) = points[2*i]
            (x2, y2) = points[2*i+1]
            x = min(x1, x2); y = min(y1, y2)
            w = abs(x2 - x1); h = abs(y2 - y1)
            cv2.rectangle(view, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("calibrate", view)
        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # ESC
            cv2.destroyAllWindows()
            print("Aborted.")
            return
        if len(points) >= 2 * len(REGION_KEYS):
            break

    cv2.destroyAllWindows()

    regions: Dict[str, Rect] = {}
    for i, name in enumerate(REGION_KEYS):
        (x1, y1) = points[2*i]
        (x2, y2) = points[2*i + 1]
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        regions[name] = (x, y, w, h)

    print("\nREGIONS = {")
    for k in REGION_KEYS:
        print(f'    "{k}": {regions[k]},')
    print("}")

    print(f"\nImage size: {img.shape[1]}x{img.shape[0]} (w x h)")
    print("Save REGIONS somewhere like src/regions_config.py and import it.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.calibrate_regions <path_to_png>")
    main(sys.argv[1])