#!/usr/bin/env python3
"""Offline, deterministic MedMNIST evaluation/export smoke check.

The helper creates a tiny NPZ fixture in a temporary directory, so it does not
need a downloaded dataset and never deletes files from the package default
root.  It does not train a model.  Use --workdir only when a retained fixture
is wanted; an existing run directory is rejected rather than overwritten.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# Prefer an installed package, but make the helper usable from a source tree
# when invoked from its repository root. No checkout location is hard-coded.
_script = Path(__file__).resolve()
_candidates = [Path.cwd(), *_script.parents]
for _candidate in _candidates:
    if (_candidate / "medmnist" / "__init__.py").is_file():
        sys.path.insert(0, str(_candidate))
        break

import numpy as np

from medmnist import (
    AdrenalMNIST3D,
    ChestMNIST,
    Evaluator,
    PathMNIST,
    PneumoniaMNIST,
    RetinaMNIST,
)
from medmnist.evaluator import getACC, getAUC


N = 4
SPLITS = ("train", "val", "test")


class _TinyLengthMixin:
    """Avoid the registry sample-count assertion for tiny local fixtures."""

    def __len__(self):  # noqa: D401 - this is a fixture adapter
        return int(self.imgs.shape[0])


class TinyPneumonia(_TinyLengthMixin, PneumoniaMNIST):
    pass


class TinyPath(_TinyLengthMixin, PathMNIST):
    pass


class TinyAdrenal(_TinyLengthMixin, AdrenalMNIST3D):
    pass


class LocalEvaluator(Evaluator):
    """Evaluator variant that keeps parse_and_evaluate inside a temp root."""

    fixture_root: str | None = None

    def __init__(self, flag, split, size=None, root=None):
        selected_root = self.fixture_root if root is None else root
        if selected_root is None:
            raise RuntimeError("LocalEvaluator.fixture_root was not configured")
        super().__init__(flag, split, size=size, root=selected_root)


def _assert_metric(name: str, metrics) -> None:
    if not (np.isclose(metrics.AUC, 1.0) and np.isclose(metrics.ACC, 1.0)):
        raise AssertionError(
            f"{name} expected AUC=1.0 and ACC=1.0, got "
            f"AUC={metrics.AUC!r}, ACC={metrics.ACC!r}"
        )
    print(f"{name}: AUC={metrics.AUC:.3f} ACC={metrics.ACC:.3f}")


def _write_npz(root: Path, flag: str, labels: np.ndarray, images: np.ndarray, size=None) -> None:
    suffix = "" if size in (None, 28) else f"_{size}"
    payload = {}
    for split in SPLITS:
        payload[f"{split}_images"] = images
        payload[f"{split}_labels"] = labels
    np.savez(root / f"{flag}{suffix}.npz", **payload)


def _make_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    binary_y = np.array([[0], [1], [0], [1]], dtype=np.int64)
    binary_images = np.arange(N * 8 * 8, dtype=np.uint8).reshape(N, 8, 8)
    _write_npz(root, "pneumoniamnist", binary_y, binary_images)
    _write_npz(root, "pneumoniamnist", binary_y, binary_images, size=64)

    multilabel_y = np.array(
        [[0, 0], [1, 1], [0, 1], [1, 0]], dtype=np.int64
    )
    chest_images = np.arange(N * 8 * 8, dtype=np.uint8).reshape(N, 8, 8)
    _write_npz(root, "chestmnist", multilabel_y, chest_images)

    multiclass_y = np.array([[0], [1], [2], [1]], dtype=np.int64)
    path_images = np.arange(N * 8 * 8 * 3, dtype=np.uint8).reshape(N, 8, 8, 3)
    _write_npz(root, "pathmnist", multiclass_y, path_images)

    ordinal_y = np.array([[0], [1], [2], [1]], dtype=np.int64)
    retina_images = np.arange(N * 8 * 8 * 3, dtype=np.uint8).reshape(N, 8, 8, 3)
    _write_npz(root, "retinamnist", ordinal_y, retina_images)

    # A tiny grayscale volume is sufficient for GIF save and montage paths.
    volume_y = np.array([[0], [1], [2], [1]], dtype=np.int64)
    volumes = np.arange(N * 4 * 4 * 4, dtype=np.uint8).reshape(N, 4, 4, 4)
    _write_npz(root, "adrenalmnist3d", volume_y, volumes)


def _run_metrics(root: Path, results: Path) -> None:
    results.mkdir(parents=True, exist_ok=True)

    binary_y = np.array([[0], [1], [0], [1]])
    binary_1d = np.array([0.10, 0.90, 0.20, 0.80])
    binary_2d = np.column_stack((1.0 - binary_1d, binary_1d))
    binary_eval = LocalEvaluator("pneumoniamnist", "test", root=str(root))
    _assert_metric("binary 1-D", binary_eval.evaluate(binary_1d, results, "binary-1d"))
    _assert_metric("binary 2-D", binary_eval.evaluate(binary_2d, results, "binary-2d"))
    if binary_eval.labels.shape != binary_y.shape:
        raise AssertionError(f"binary labels changed shape: {binary_eval.labels.shape}")

    multilabel_score = np.array(
        [[0.10, 0.20], [0.90, 0.80], [0.20, 0.70], [0.80, 0.30]]
    )
    multilabel_eval = LocalEvaluator("chestmnist", "test", root=str(root))
    _assert_metric(
        "multilabel",
        multilabel_eval.evaluate(multilabel_score, results, "multilabel"),
    )

    multiclass_score = np.array(
        [
            [0.90, 0.05, 0.05],
            [0.05, 0.90, 0.05],
            [0.05, 0.05, 0.90],
            [0.05, 0.90, 0.05],
        ]
    )
    multiclass_eval = LocalEvaluator("pathmnist", "test", root=str(root))
    _assert_metric(
        "multiclass",
        multiclass_eval.evaluate(multiclass_score, results, "multiclass"),
    )

    ordinal_eval = LocalEvaluator("retinamnist", "test", root=str(root))
    _assert_metric(
        "ordinal",
        ordinal_eval.evaluate(multiclass_score, results, "ordinal"),
    )

    # Also verify the low-level functions with the exact task labels.
    if not np.isclose(getAUC(binary_y, binary_1d, "binary-class"), 1.0):
        raise AssertionError("low-level binary AUC did not equal 1.0")
    if not np.isclose(getACC(binary_y, binary_1d, "binary-class"), 1.0):
        raise AssertionError("low-level binary ACC did not equal 1.0")


def _run_roundtrip(root: Path, results: Path) -> None:
    results.mkdir(parents=True, exist_ok=True)
    LocalEvaluator.fixture_root = str(root)
    evaluator = LocalEvaluator("pneumoniamnist", "test", size=64)
    scores = np.array([0.10, 0.90, 0.20, 0.80])
    metrics = evaluator.evaluate(scores, save_folder=str(results), run="roundtrip")
    _assert_metric("_64 direct", metrics)

    expected = results / (
        "pneumoniamnist_64_test_"
        "[AUC]1.000_[ACC]1.000@roundtrip.csv"
    )
    if not expected.is_file():
        raise AssertionError(f"standard result was not written: {expected.name}")

    parsed = LocalEvaluator.parse_and_evaluate(str(expected), run="roundtrip")
    _assert_metric("_64 parse", parsed)
    LocalEvaluator.fixture_root = None
    print(f"round trip: {expected.name}")


def _run_exports(root: Path, export_root: Path) -> None:
    export_root.mkdir(parents=True, exist_ok=True)

    np.random.seed(0)
    dataset_2d = TinyPneumonia(split="test", root=str(root))
    dataset_2d.save(str(export_root / "2d"), postfix="png", write_csv=True)
    dataset_2d.montage(length=2, replace=True, save_folder=str(export_root / "2d"))
    image_dir = export_root / "2d" / "pneumoniamnist"
    csv_path = export_root / "2d" / "pneumoniamnist.csv"
    montage_path = export_root / "2d" / "pneumoniamnist_test_montage.jpg"
    if not list(image_dir.glob("*.png")) or not csv_path.is_file() or not montage_path.is_file():
        raise AssertionError("2-D PNG/CSV/JPG export was incomplete")
    print("2-D export: PNG, CSV, and JPG montage present")

    np.random.seed(0)
    dataset_3d = TinyAdrenal(split="test", root=str(root))
    dataset_3d.save(str(export_root / "3d"), postfix="gif", write_csv=True)
    dataset_3d.montage(length=2, replace=True, save_folder=str(export_root / "3d"))
    volume_dir = export_root / "3d" / "adrenalmnist3d"
    volume_csv = export_root / "3d" / "adrenalmnist3d.csv"
    volume_montage = export_root / "3d" / "adrenalmnist3d_test_montage.gif"
    if not list(volume_dir.glob("*.gif")) or not volume_csv.is_file() or not volume_montage.is_file():
        raise AssertionError("3-D GIF/CSV/GIF montage export was incomplete")
    print("3-D export: GIF, CSV, and GIF montage present")


def _prepare_run_dir(workdir: str | None):
    if workdir is None:
        holder = tempfile.TemporaryDirectory(prefix="medmnist-smoke-")
        run_dir = Path(holder.name)
        return holder, run_dir

    parent = Path(workdir).expanduser()
    parent.mkdir(parents=True, exist_ok=True)
    run_dir = parent / "medmnist_smoke_run"
    if run_dir.exists():
        raise RuntimeError(
            f"refusing to overwrite existing {run_dir}; choose another --workdir "
            "or remove only this user-created fixture directory"
        )
    run_dir.mkdir()
    return None, run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic offline MedMNIST evaluator and export checks "
            "against a temporary synthetic NPZ fixture. No network or training."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("all", "metrics", "roundtrip", "export"),
        default="all",
        help="check set to run (default: all)",
    )
    parser.add_argument(
        "--workdir",
        help=(
            "optional parent for a retained medmnist_smoke_run directory; "
            "existing run directories are never overwritten"
        ),
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    holder = None
    try:
        holder, run_dir = _prepare_run_dir(args.workdir)
        root = run_dir / "fixture-root"
        results = run_dir / "results"
        exports = run_dir / "exports"
        _make_fixture(root)
        print(f"synthetic fixture: {root}")

        if args.mode in ("all", "metrics"):
            _run_metrics(root, results)
        if args.mode in ("all", "roundtrip"):
            _run_roundtrip(root, results)
        if args.mode in ("all", "export"):
            _run_exports(root, exports)

        print("SMOKE PASS: offline evaluator/export checks completed")
        if args.workdir:
            print(f"retained artifacts: {run_dir}")
        return 0
    except Exception as exc:  # provide a clear CLI error without a long traceback
        print(f"SMOKE ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        # TemporaryDirectory performs only its own temporary cleanup. A supplied
        # --workdir is intentionally retained and is never cleaned here.
        if holder is not None:
            holder.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
