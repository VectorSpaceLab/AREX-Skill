#!/usr/bin/env python3
"""Validate tiny NeuroMANCER dictionary, static, and sequence data contracts.

This helper is deterministic, in-memory, and intentionally does not train,
perform network access, create checkpoints, or write files. It is safe to run
from any current working directory when the NeuroMANCER package is installed.
"""

from __future__ import annotations

import argparse
import sys


def run_smoke() -> int:
    """Build tiny fixtures and return a process-style status code."""
    try:
        import numpy as np
        import torch
        from neuromancer.dataset import DictDataset, SequenceDataset, StaticDataset
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(
            "data_smoke --run requires an importable neuromancer installation "
            f"and its CPU dependencies: {exc}",
            file=sys.stderr,
        )
        return 2

    torch.manual_seed(0)
    static_raw = {
        "x": np.arange(12, dtype=np.float32).reshape(4, 3),
        "y": np.arange(4, dtype=np.float32).reshape(4, 1),
    }
    static = StaticDataset(static_raw, name="train")
    static_batch = static.collate_fn([static[0], static[1]])
    assert len(static) == 4
    assert tuple(static_batch["x"].shape) == (2, 3)
    assert tuple(static_batch["y"].shape) == (2, 1)
    assert static_batch["name"] == "train"
    assert tuple(static.get_full_batch()["x"].shape) == (4, 3)

    dict_data = DictDataset(
        {"x": torch.zeros(4, 3), "y": torch.ones(4, 1)}, name="dev"
    )
    dict_batch = dict_data.collate_fn([dict_data[0], dict_data[1]])
    assert tuple(dict_batch["x"].shape) == (2, 3)
    assert dict_batch["name"] == "dev"

    sequence_raw = {
        "X": np.arange(8, dtype=np.float32).reshape(8, 1),
        "U": np.arange(16, dtype=np.float32).reshape(8, 2),
    }
    sequence = SequenceDataset(
        sequence_raw, nsteps=2, moving_horizon=False, name="train"
    )
    sequence_batch = sequence.collate_fn([sequence[0], sequence[1]])
    assert len(sequence) == 3
    assert {"Xp", "Xf", "Up", "Uf", "index"}.issubset(sequence[0])
    assert tuple(sequence_batch["Xp"].shape) == (2, 2, 1)
    assert tuple(sequence_batch["Uf"].shape) == (2, 2, 2)
    assert sequence_batch["name"] == "nstep_train"

    print("data_smoke: static/dict/sequence contracts passed")
    print(f"data_smoke: static={len(static)} sequence_items={len(sequence)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run only when explicitly requested."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic, in-memory NeuroMANCER data contract smoke "
            "without training or filesystem/network side effects."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="create tiny fixtures and validate dataset keys/shapes",
    )
    parser.add_argument(
        "--temp-dir",
        default=None,
        help="reserved optional scratch location; no files are written by this helper",
    )
    args = parser.parse_args(argv)
    del args.temp_dir  # Explicitly document that the smoke remains write-free.
    if not args.run:
        parser.print_help()
        return 0
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
