#!/usr/bin/env python3
"""Run deterministic, local checks for pykitti tracking label utilities."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description=(
            "Exercise KittiTrackingLabels and to_array_list on an in-memory "
            "and temporary local fixture; no network or GUI is used."
        )
    )


def _label_row(track_id: int, cls: str, x1: int, y1: int, x2: int, y2: int, occluded: int):
    # Payload through roty: id, class, truncated, occluded, alpha,
    # x1, y1, x2, y2, xd, yd, zd, x, y, z, roty.
    return [
        track_id,
        cls,
        0.0,
        occluded,
        0.0,
        x1,
        y1,
        x2,
        y2,
        1.5,
        1.6,
        3.7,
        1.0,
        2.0,
        15.0,
        0.1,
    ]


def main() -> int:
    _parser().parse_args()

    # Import only the installed/public package surface; do not alter sys.path
    # or import files from a source checkout.
    import numpy as np
    import pandas as pd
    from pykitti.tracking import KittiTrackingLabels, to_array_list

    columns = KittiTrackingLabels.columns[:-1]  # label fields, no score
    rows = []
    index = []
    for frame in range(3):
        rows.extend(
            [
                _label_row(42, "Car", 10 + frame, 20, 30 + frame, 40, frame),
                _label_row(7, "Cyclist", 50 + frame, 60, 70 + frame, 90, 2 - frame),
            ]
        )
        index.extend([frame, frame])
    # Keep one ignored row in the middle frame while retaining two real objects
    # per frame, so current NumPy can form dense property arrays.
    rows.insert(4, _label_row(-1, "DontCare", 0, 0, 1, 1, 0))
    index.insert(4, 1)
    source_df = pd.DataFrame(rows, columns=columns, index=index)

    labels = KittiTrackingLabels(source_df, remove_dontcare=True, split_on_reappear=True)
    assert labels.ids == [0, 1], labels.ids
    assert labels.max_objects == 2
    assert labels.index.tolist() == [0, 1, 2]
    assert len(labels) == 3

    boxes = labels.bbox
    assert boxes.shape == (3, 2, 4), boxes.shape
    np.testing.assert_array_equal(
        boxes[0], np.asarray([[10, 20, 20, 20], [50, 60, 20, 30]])
    )
    assert labels.bbox.dtype.kind in "iu"

    corners = KittiTrackingLabels(
        source_df, bbox_with_size=False, split_on_reappear=False
    ).bbox
    np.testing.assert_array_equal(corners[0], np.asarray([[10, 20, 30, 40], [50, 60, 70, 90]]))

    classes = labels.cls
    assert classes.shape == (3, 2, 1), classes.shape
    assert classes[0, :, 0].tolist() == ["Car", "Cyclist"]

    occlusion = labels.occlusion
    assert occlusion.shape == (3, 2, 1), occlusion.shape
    np.testing.assert_array_equal(occlusion[0, :, 0], np.asarray([0, 2]))

    presence = labels.presence
    assert presence.shape == (3, 2), presence.shape
    np.testing.assert_array_equal(presence, np.ones((3, 2), dtype=bool))

    # Direct conversion verifies per-frame grouping and normalized-ID ordering.
    grouped = pd.DataFrame(
        {"id": [2, 1, 1, 2], "value": [20, 10, 11, 21]},
        index=[0, 0, 1, 1],
    )
    converted = to_array_list(grouped)
    assert converted.shape == (2, 2, 1), converted.shape
    np.testing.assert_array_equal(converted[:, :, 0], np.asarray([[10, 20], [11, 21]]))

    # Reappearance splitting is checked through the supported metadata matrix,
    # without asking ragged per-frame properties to densify.
    reappear = pd.DataFrame(
        [_label_row(42, "Car", 1, 2, 3, 4, 0), _label_row(42, "Car", 5, 6, 7, 8, 0)],
        columns=columns,
        index=[0, 2],
    )
    split = KittiTrackingLabels(reappear, split_on_reappear=True)
    assert split.ids == [0, 1], split.ids
    np.testing.assert_array_equal(
        split.presence,
        np.asarray([[True, False], [False, False], [False, True]], dtype=bool),
    )

    # Exercise text-file parsing with the 17-token label-row schema.
    with tempfile.TemporaryDirectory() as directory:
        label_path = Path(directory) / "0000.txt"
        payload = _label_row(9, "Car", 1, 2, 5, 8, 0)
        label_path.write_text("0 " + " ".join(map(str, payload)) + "\n", encoding="utf-8")
        from_file = KittiTrackingLabels(str(label_path), split_on_reappear=False)
        assert from_file.bbox.shape == (1, 1, 4)
        np.testing.assert_array_equal(from_file.bbox[0, 0], np.asarray([1, 2, 4, 6]))

    # These are known legacy limitations, not smoke-test failures. Probe them
    # so the script documents the live environment without claiming support.
    legacy = {}
    try:
        labels.id
    except AttributeError:
        legacy["id"] = "unavailable"
    else:
        legacy["id"] = "available"
    try:
        labels.num_objects
    except (AttributeError, TypeError):
        legacy["num_objects"] = "legacy-incompatible"
    else:
        legacy["num_objects"] = "available"

    print("tracking label fixture: PASS")
    print("pandas:", pd.__version__, "legacy probes:", legacy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
