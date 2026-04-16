from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List

import cv2

# Order for detail-screen calibration output
REGION_KEYS_DETAIL = [
    "slot",
    "set",
    "rarity",
    "ilevel",
    "enhance",
    "main_stat",
    "main_value",
    "sub1_stat",
    "sub1_value",
    "sub2_stat",
    "sub2_value",
    "sub3_stat",
    "sub3_value",
    "sub4_stat",
    "sub4_value",
]

# For each REGION_KEYS_DETAIL entry:
# - click Top-Left corner
# - click Bottom-Right corner
#
# Controls:
# - Left click: add point
# - Z: undo last click
# - R: reset all clicks
# - ESC: abort
#
# When finished, it prints a Python dict you can paste into src/regions_config.py
# as REGIONS_DETAIL.

def main(img_path: str) -> None:
    p = Path(img_path)
    img = cv2.imread(str(p))
    if img is None:
        raise RuntimeError(f"Could not read image: {p}")

    region_keys = REGION_KEYS_DETAIL
    points: List[Tuple[int, int]] = []
    mouse_pos: Tuple[int, int] | None = None

    def current_key_index() -> int:
        return len(points) // 2

    def current_key_name() -> str:
        i = current_key_index()
        if i >= len(region_keys):
            return "DONE"
        return region_keys[i]

    def on_mouse(event, x, y, flags, param):
        nonlocal mouse_pos
        mouse_pos = (x, y)

        if event == cv2.EVENT_LBUTTONDOWN:
            key_idx = len(points) // 2
            click_num = 1 if len(points) % 2 == 0 else 2
            key_name = region_keys[key_idx] if key_idx < len(region_keys) else "DONE"

            points.append((x, y))
            print(f"[{key_name}] click {click_num}/2: ({x},{y})")

    cv2.namedWindow("calibrate", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("calibrate", on_mouse)

    while True:
        view = img.copy()
        label = (
            f"Click TL then BR for: {current_key_name()}  "
            f"({len(points)}/{2 * len(region_keys)})   "
            f"[Z=undo, R=reset, ESC=abort]"
        )
        cv2.putText(
            view,
            label,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        # draw completed rectangles
        for i in range(len(points) // 2):
            (x1, y1) = points[2 * i]
            (x2, y2) = points[2 * i + 1]
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                view,
                region_keys[i],
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )

        # draw in-progress rectangle after TL click
        if len(points) % 2 == 1 and mouse_pos is not None:
            (x1, y1) = points[-1]
            (x2, y2) = mouse_pos
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 255), 1)

        cv2.imshow("calibrate", view)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:  # ESC
            cv2.destroyAllWindows()
            print("Aborted.")
            return

        if key in (ord("z"), ord("Z")):
            if points:
                removed = points.pop()
                print(f"Undo: removed {removed}; now targeting [{current_key_name()}]")
            continue

        if key in (ord("r"), ord("R")):
            points.clear()
            print("Reset all points.")
            continue

        if len(points) >= 2 * len(region_keys):
            break

    cv2.destroyAllWindows()

    regions: Dict[str, Rect] = {}
    for i, name in enumerate(region_keys):
        (x1, y1) = points[2 * i]
        (x2, y2) = points[2 * i + 1]
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        regions[name] = (x, y, w, h)

    print("\nREGIONS_DETAIL = {")
    for k in region_keys:
        print(f'    "{k}": {regions[k]},')
    print("}")

    print(f"\nImage size: {img.shape[1]}x{img.shape[0]} (w x h)")
    print("Paste REGIONS_DETAIL into src/regions_config.py")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m src.calibrate_regions <path_to_png>")

    main(sys.argv[1])