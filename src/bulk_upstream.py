# src/bulk_upstream.py

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.contracts import RawCapture, CanonItem, RecError
from src.recognizer_closed import ClosedSetRecognizer
from src.regions_config import bulk_item_regions


@dataclass(frozen=True)
class BulkItemResult:
    index: int
    item: CanonItem | None
    errors: Sequence[RecError]


def make_bulk_capture(
    screenshot_path: Path,
    index: int,
    timestamp_ms: int = 0,
) -> RawCapture:
    return RawCapture(
        screenshot_path=screenshot_path,
        regions=bulk_item_regions(index),
        timestamp_ms=timestamp_ms,
        meta={"profile": "bulk", "bulk_index": index},
    )


def recognize_bulk_screen(
    screenshot_path: Path,
    recognizer: ClosedSetRecognizer,
    *,
    entry_count: int,
) -> list[BulkItemResult]:
    results: list[BulkItemResult] = []

    for index in range(entry_count):
        cap = make_bulk_capture(screenshot_path, index)
        item, errors = recognizer.recognize(cap)

        results.append(
            BulkItemResult(
                index=index,
                item=item,
                errors=errors,
            )
        )

    return results