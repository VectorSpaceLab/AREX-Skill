"""Small helpers for converting COCO annotations into LayoutParser blocks.

The main public helper mirrors the notebook recipe from the repository's COCO
example, but keeps the logic in a reusable, self-contained module.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

import layoutparser as lp


def load_coco_annotations(
    annotations: Iterable[dict], coco: Optional[Any] = None
) -> lp.Layout:
    """Convert COCO-style annotations into a LayoutParser layout.

    Args:
        annotations:
            A list or iterable of COCO annotation dicts for one image.
        coco:
            Optional COCO object whose ``cats`` map turns category ids into
            category names.

    Returns:
        A ``layoutparser.Layout`` whose blocks are ``TextBlock(Rectangle(...))``.
    """

    layout = lp.Layout()

    for ele in annotations:
        x, y, w, h = ele["bbox"]
        layout.append(
            lp.TextBlock(
                block=lp.Rectangle(x, y, x + w, y + h),
                type=ele["category_id"] if coco is None else coco.cats[ele["category_id"]]["name"],
                id=ele.get("id"),
                score=ele.get("score"),
            )
        )

    return layout


def _smoke() -> None:
    sample = [
        {"bbox": [10, 20, 30, 40], "category_id": 1, "id": 7, "score": 0.9},
    ]
    layout = load_coco_annotations(sample)
    print(layout.to_dict())


if __name__ == "__main__":
    _smoke()
