#!/usr/bin/env python3
"""Tiny local smoke test for HyperTools IO.

Runs a few self-contained save/load round-trips in a temporary directory and,
when requested, creates a local pylsl outlet to verify hyp.io.lsl_stream().

Examples
--------
python scripts/smoke_io.py
python scripts/smoke_io.py --lsl-local-smoke
"""

from __future__ import annotations

import argparse
import importlib.util
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd


def _import_hypertools():
    try:
        import hypertools as hyp
    except Exception as exc:  # pragma: no cover - exercised by runtime envs
        raise SystemExit(
            f"unable to import hypertools: {exc}. Install the package and its "
            "runtime dependencies before running this smoke helper.") from exc
    return hyp


def _assert_frame_equal(left: pd.DataFrame, right: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(left, right)


def _round_trip_local_files(hyp, base: Path) -> None:
    array = np.arange(12, dtype=float).reshape(4, 3)
    frame = pd.DataFrame(
        {
            "left": [1, 2, 3],
            "right": [4, 5, 6],
        }
    )
    payload = {"label": "io-smoke", "answer": 42}

    pkl_path = base / "payload.pkl"
    hyp.save(payload, pkl_path)
    assert hyp.load(pkl_path) == payload

    npy_path = base / "array.npy"
    hyp.save(array, npy_path)
    np.testing.assert_allclose(hyp.load(npy_path), array)

    npz_path = base / "bundle.npz"
    hyp.save([array, array + 1], npz_path)
    bundle = hyp.load(npz_path)
    assert isinstance(bundle, list) and len(bundle) == 2
    np.testing.assert_allclose(bundle[0], array)
    np.testing.assert_allclose(bundle[1], array + 1)

    csv_path = base / "frame.csv"
    hyp.save(frame, csv_path)
    _assert_frame_equal(hyp.load(csv_path), frame)

    xlsx_spec = importlib.util.find_spec("openpyxl")
    if xlsx_spec is not None:
        xlsx_path = base / "frame.xlsx"
        hyp.save(frame, xlsx_path)
        _assert_frame_equal(hyp.load(xlsx_path), frame)
    else:
        print("openpyxl not installed; skipped .xlsx smoke")

    print("local save/load round-trip OK")


def _start_local_outlet(name: str, n_channels: int = 4):
    import pylsl

    info = pylsl.StreamInfo(name, "EEG", n_channels, 100.0, "float32",
                            f"hypertools-io-smoke-{name}")
    outlet = pylsl.StreamOutlet(info)
    stop = threading.Event()

    def _push() -> None:
        i = 0
        while not stop.is_set():
            sample = [float(i) + 0.1 * c for c in range(n_channels)]
            outlet.push_sample(sample)
            i += 1
            time.sleep(0.01)

    thread = threading.Thread(target=_push, daemon=True)
    thread.start()
    return stop, thread


def _lsl_local_smoke(hyp) -> None:
    try:
        import pylsl
    except ImportError:
        print("LSL smoke skipped: pylsl is not installed")
        return

    from hypertools.io.streaming import is_stream

    name = f"hypertools-io-smoke-{time.time_ns()}"
    stop, thread = _start_local_outlet(name)
    try:
        # Give the outlet a moment to announce itself before resolving.
        time.sleep(0.25)
        stream = hyp.io.lsl_stream(name=name, timeout=5.0)
        assert is_stream(stream)
        samples = [next(stream) for _ in range(5)]
        assert all(len(sample) == 4 for sample in samples)
        assert all(isinstance(value, float)
                   for sample in samples for value in sample)
        if hasattr(stream, "close"):
            stream.close()
    finally:
        stop.set()
        thread.join(timeout=5.0)
        assert not thread.is_alive(), "local LSL outlet thread did not stop"

    print("local LSL smoke OK")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run small HyperTools IO smoke checks.")
    parser.add_argument(
        "--lsl-local-smoke",
        action="store_true",
        help="also create a local pylsl outlet and resolve it with hyp.io.lsl_stream()",
    )
    args = parser.parse_args()

    hyp = _import_hypertools()

    with TemporaryDirectory(prefix="hypertools-io-smoke-") as tmp:
        _round_trip_local_files(hyp, Path(tmp))

    if args.lsl_local_smoke:
        _lsl_local_smoke(hyp)
    else:
        print("LSL smoke skipped (pass --lsl-local-smoke to enable it)")

    print("IO smoke complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
