#!/usr/bin/env python3
"""Tiny deterministic Tensorpack DataFlow serializer smoke checks.

The helper writes only under --workdir, uses synthetic datapoints, and avoids
network/downloads/original-repo paths. It is intended for future agents to check
serializer availability and roundtrip behavior in the user's active runtime.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple


FORMAT_CHOICES = ("numpy", "lmdb", "tfrecord", "hdf5", "all")


class SmokeSkip(RuntimeError):
    """A selected format cannot run because an optional dependency is missing."""


def make_tiny_dataflow(base_cls, seed: int = 42, size: int = 8):
    """Create an actual Tensorpack DataFlow subclass after tensorpack is imported."""

    class _Tiny(base_cls):  # type: ignore[misc, valid-type]
        def __init__(self, seed: int, size: int) -> None:
            self.seed = int(seed)
            self._size = int(size)
            self.cache = []

        def reset_state(self) -> None:
            import numpy as np

            rng = np.random.RandomState(self.seed)
            self.cache = []
            for idx in range(self._size):
                label = int(rng.randint(low=0, high=10))
                image = rng.randn(4, 4, 1).astype("float32") + idx * 0.01
                self.cache.append([label, image])

        def __len__(self) -> int:
            return self._size

        def __iter__(self):
            for dp in self.cache:
                yield dp

    return _Tiny(seed, size)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny Tensorpack DataFlow serializer roundtrip checks."
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="Directory where temporary serializer outputs will be created.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=FORMAT_CHOICES,
        default=["numpy"],
        help="Serializer formats to check. Use 'all' for every supported format.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=8,
        help="Number of tiny datapoints to roundtrip (default: 8).",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated files under --workdir instead of deleting per-format outputs first.",
    )
    return parser.parse_args(argv)


def selected_formats(values: Iterable[str]) -> List[str]:
    values = list(values)
    if "all" in values:
        return ["numpy", "lmdb", "tfrecord", "hdf5"]
    # Preserve user order while removing duplicates.
    out: List[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def import_tensorpack_bits():
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - NumPy is expected but report clearly.
        raise RuntimeError(f"NumPy import failed: {exc}") from exc

    # Tensorpack 0.11's NumPy serializer uses the historic np.object alias.
    # Define it locally for modern NumPy runtimes without changing user data.
    # Avoid hasattr(np, "object") because recent NumPy emits a FutureWarning.
    if "object" not in np.__dict__:
        setattr(np, "object", object)

    try:
        from tensorpack.dataflow import (  # type: ignore
            HDF5Serializer,
            LMDBSerializer,
            NumpySerializer,
            TFRecordSerializer,
        )
        from tensorpack.dataflow.base import DataFlow  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Tensorpack dataflow import failed. Activate an environment with "
            f"tensorpack and its base dependencies installed. Original error: {exc}"
        ) from exc

    return np, DataFlow, {
        "numpy": NumpySerializer,
        "lmdb": LMDBSerializer,
        "tfrecord": TFRecordSerializer,
        "hdf5": HDF5Serializer,
    }


def clear_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def expected_data(dataflow) -> List[list]:
    dataflow.reset_state()
    return list(dataflow)


def actual_data(dataflow) -> List[list]:
    dataflow.reset_state()
    return list(dataflow)


def compare_datapoints(np, expected: List[list], actual: List[list]) -> None:
    if len(expected) != len(actual):
        raise AssertionError(f"length mismatch: expected {len(expected)}, got {len(actual)}")
    for idx, (exp, got) in enumerate(zip(expected, actual)):
        if int(exp[0]) != int(got[0]):
            raise AssertionError(f"label mismatch at {idx}: {exp[0]} != {got[0]}")
        if not np.allclose(np.asarray(exp[1]), np.asarray(got[1])):
            raise AssertionError(f"image mismatch at {idx}")


def run_numpy(np, serializer, source, outdir: Path) -> Tuple[int, Path]:
    path = outdir / "roundtrip.npz"
    serializer.save(source, str(path))
    loaded = serializer.load(str(path), shuffle=False)
    got = actual_data(loaded)
    exp = expected_data(source)
    compare_datapoints(np, exp, got)
    return len(got), path


def run_lmdb(np, serializer, source, outdir: Path) -> Tuple[int, Path]:
    path = outdir / "roundtrip.lmdb"
    serializer.save(source, str(path), write_frequency=4)
    loaded = serializer.load(str(path), shuffle=False)
    got = actual_data(loaded)
    exp = expected_data(source)
    compare_datapoints(np, exp, got)
    return len(got), path


def run_tfrecord(np, serializer, source, outdir: Path) -> Tuple[int, Path]:
    path = outdir / "roundtrip.tfrecord"
    serializer.save(source, str(path))
    loaded = serializer.load(str(path), size=len(source))
    got = actual_data(loaded)
    exp = expected_data(source)
    compare_datapoints(np, exp, got)
    return len(got), path


def run_hdf5(np, serializer, source, outdir: Path) -> Tuple[int, Path]:
    path = outdir / "roundtrip.h5"
    data_paths = ["label", "image"]
    serializer.save(source, str(path), data_paths)
    loaded = serializer.load(str(path), data_paths, shuffle=False)
    got = actual_data(loaded)
    exp = expected_data(source)
    compare_datapoints(np, exp, got)
    return len(got), path


RUNNERS: dict[str, Callable] = {
    "numpy": run_numpy,
    "lmdb": run_lmdb,
    "tfrecord": run_tfrecord,
    "hdf5": run_hdf5,
}


def run_one(fmt: str, workdir: Path, size: int, keep: bool) -> bool:
    np, dataflow_cls, serializers = import_tensorpack_bits()
    fmt_dir = workdir / fmt
    if not keep:
        clear_path(fmt_dir)
    fmt_dir.mkdir(parents=True, exist_ok=True)

    serializer = serializers[fmt]
    source = make_tiny_dataflow(dataflow_cls, size=size)
    source.reset_state()

    try:
        count, path = RUNNERS[fmt](np, serializer, source, fmt_dir)
    except (ImportError, AttributeError) as exc:
        # Tensorpack optional serializers become dummy classes when deps are missing.
        print(f"SKIP {fmt}: optional dependency unavailable or serializer disabled: {exc}")
        return True
    except Exception as exc:
        print(f"FAIL {fmt}: {exc}")
        return False

    print(f"OK {fmt}: roundtripped {count} datapoints at {path}")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.size <= 0:
        print("FAIL: --size must be positive", file=sys.stderr)
        return 2

    workdir = Path(args.workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    ok = True
    for fmt in selected_formats(args.formats):
        try:
            ok = run_one(fmt, workdir, args.size, args.keep) and ok
        except SmokeSkip as exc:
            print(f"SKIP {fmt}: {exc}")
        except Exception as exc:  # Defensive: keep checking remaining formats.
            print(f"FAIL {fmt}: {exc}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
