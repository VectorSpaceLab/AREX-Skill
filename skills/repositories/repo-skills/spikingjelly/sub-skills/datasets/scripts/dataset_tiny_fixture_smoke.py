#!/usr/bin/env python3
"""No-download smoke test for SpikingJelly dataset builder contracts.

This script creates tiny temporary event fixtures and exercises the same public
builder/util contracts distilled from the repository's dataset tests. It does
not read or download any real dataset.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict

import numpy as np
import torch

from spikingjelly.datasets import base, transform, utils


def _events(extra_tail: bool = False) -> Dict[str, np.ndarray]:
    """Return sorted polarity events with repeated positions for accumulation checks."""
    if extra_tail:
        return {
            "t": np.array([0, 1, 2, 3, 4, 5], dtype=np.int64),
            "x": np.array([0, 0, 1, 1, 0, 1], dtype=np.int64),
            "y": np.array([0, 0, 1, 1, 1, 0], dtype=np.int64),
            "p": np.array([0, 0, 1, 1, 0, 1], dtype=np.int64),
        }
    return {
        "t": np.array([0, 1, 2, 3], dtype=np.int64),
        "x": np.array([0, 0, 1, 1], dtype=np.int64),
        "y": np.array([0, 0, 1, 1], dtype=np.int64),
        "p": np.array([0, 0, 1, 1], dtype=np.int64),
    }


def _write_event_archive(path: Path, events: Dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    utils.np_savez(path, **events)


def _assert_array_equal(name: str, actual: np.ndarray, expected: np.ndarray) -> None:
    if not np.array_equal(actual, expected):
        raise AssertionError(
            f"{name} mismatch:\nactual={actual!r}\nexpected={expected!r}"
        )


def _smoke_fixed_number_builder(work_root: Path) -> None:
    root = work_root / "fixed_number"
    raw_root = root / "events_np"
    events = _events()
    event_file = raw_root / "class0" / "sample.npz"
    _write_event_archive(event_file, events)

    cfg = base.NeuromorphicDatasetConfig(
        root=root,
        train=True,
        data_type="frame",
        frames_number=2,
        split_by="number",
    )
    processed_root, loader = base.FrameFixedNumberBuilder(
        cfg, raw_root, H=2, W=2
    ).build()

    frames_file = processed_root / "class0" / "sample.npz"
    frames = loader(frames_file)
    expected = utils.integrate_events_by_fixed_frames_number(
        events, split_by="number", frames_num=2, H=2, W=2
    ).astype(np.float32)

    if frames.dtype != np.float32:
        raise AssertionError(f"load_npz_frames should return float32, got {frames.dtype}")
    if frames.shape != (2, 2, 2, 2):
        raise AssertionError(f"unexpected fixed-number frame shape: {frames.shape}")
    _assert_array_equal("fixed-number builder frames", frames, expected)


def _custom_two_frames(events, H: int, W: int) -> np.ndarray:
    mid = len(events["t"]) // 2
    return np.stack(
        [
            utils.integrate_events_segment_to_frame(
                events["x"], events["y"], events["p"], H, W, 0, mid
            ),
            utils.integrate_events_segment_to_frame(
                events["x"], events["y"], events["p"], H, W, mid, len(events["t"])
            ),
        ]
    )


def _smoke_custom_builder(work_root: Path) -> None:
    root = work_root / "custom"
    raw_root = root / "events_np"
    events = _events()
    event_file = raw_root / "class0" / "sample.npz"
    _write_event_archive(event_file, events)

    cfg = base.NeuromorphicDatasetConfig(
        root=root,
        train=None,
        data_type="frame",
        custom_integrate_function=_custom_two_frames,
        custom_integrated_frames_dir_name="custom_two_frames",
    )
    processed_root, loader = base.FrameCustomIntegrateBuilder(
        cfg, raw_root, H=2, W=2
    ).build()

    frames = loader(processed_root / "class0" / "sample.npz")
    expected = _custom_two_frames(events, H=2, W=2).astype(np.float32)
    if processed_root.name != "custom_two_frames":
        raise AssertionError(f"custom root name was not honored: {processed_root}")
    _assert_array_equal("custom builder frames", frames, expected)


def _smoke_fixed_duration_padding() -> None:
    first = utils.integrate_events_by_fixed_duration(_events(), duration=2, H=2, W=2)
    second = utils.integrate_events_by_fixed_duration(
        _events(extra_tail=True), duration=2, H=2, W=2
    )
    padded, labels, lengths = utils.pad_sequence_collate([(first, 4), (second, 7)])

    if padded.shape != (2, 3, 2, 2, 2):
        raise AssertionError(f"unexpected padded shape: {tuple(padded.shape)}")
    if not torch.equal(labels, torch.tensor([4, 7])):
        raise AssertionError(f"unexpected labels: {labels}")
    if not torch.equal(lengths, torch.tensor([2, 3])):
        raise AssertionError(f"unexpected sequence lengths: {lengths}")

    mask = utils.padded_sequence_mask(lengths)
    expected_mask = torch.tensor(
        [[True, True], [True, True], [False, True]], dtype=torch.bool
    )
    if not torch.equal(mask, expected_mask):
        raise AssertionError(f"unexpected padded mask:\n{mask}")


def _smoke_random_temporal_delete() -> None:
    np.random.seed(0)
    sequence = torch.arange(8).reshape(2, 4)
    actual = transform.RandomTemporalDelete(T_remain=2, batch_first=True)(sequence)
    expected = torch.tensor([[2, 3], [6, 7]])
    if not torch.equal(actual, expected):
        raise AssertionError(f"unexpected temporal-delete result: {actual}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sj_dataset_smoke_") as tmpdir:
        work_root = Path(tmpdir)
        _smoke_fixed_number_builder(work_root)
        _smoke_custom_builder(work_root)
        _smoke_fixed_duration_padding()
        _smoke_random_temporal_delete()

    print(
        "dataset_tiny_fixture_smoke: ok "
        "(fixed-number builder, custom builder, fixed-duration padding, temporal delete)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
