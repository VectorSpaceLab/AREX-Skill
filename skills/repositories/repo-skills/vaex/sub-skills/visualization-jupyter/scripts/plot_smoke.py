#!/usr/bin/env python3
"""Safe Vaex visualization smoke check.

Creates a tiny in-memory DataFrame, renders an expression histogram, a heatmap,
and a scatter plot with the Matplotlib Agg backend, saves the figures to a
fresh output directory, and verifies that the PNG files are non-empty.

No network access, credentials, or destructive filesystem writes are required.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    try:
        import numpy as np  # type: ignore
    except Exception:  # pragma: no cover - numpy import failure is handled elsewhere
        np = None  # type: ignore
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    if hasattr(value, "as_py"):
        return value.as_py()
    return str(value)


def _build_output_dir(base_dir: str | None) -> Path:
    if base_dir is None:
        return Path(tempfile.mkdtemp(prefix="vaex-plot-smoke-"))

    root = Path(base_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / f"vaex-plot-smoke-{uuid.uuid4().hex[:8]}"
    run_dir.mkdir(parents=False, exist_ok=False)
    return run_dir


def _assert_non_empty(path: Path) -> int:
    if not path.is_file():
        raise AssertionError(f"expected a file at {path}")
    size = path.stat().st_size
    if size <= 0:
        raise AssertionError(f"expected non-empty file at {path}")
    return size


def run_smoke(output_dir: str | None = None) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    if not hasattr(matplotlib.cm, "get_cmap") and hasattr(matplotlib, "colormaps"):
        # Vaex 4.x plotting helpers still look up the legacy matplotlib.cm API.
        matplotlib.cm.get_cmap = matplotlib.colormaps.get_cmap  # type: ignore[attr-defined]
    import matplotlib.pyplot as plt
    import vaex

    out_dir = _build_output_dir(output_dir)

    df = vaex.from_arrays(
        x=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0],
        y=[3.0, 2.0, 1.0, 0.0, -1.0, -2.0],
        weight=[1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
    )
    df["radius"] = (df.x ** 2 + df.y ** 2) ** 0.5
    df.select(df.x >= 0, name="nonnegative")

    histogram_path = out_dir / "expression_histogram.png"
    heatmap_path = out_dir / "heatmap.png"
    scatter_path = out_dir / "scatter.png"

    plt.figure(figsize=(4, 3))
    df["x"].viz.histogram(selection="nonnegative", limits="minmax", shape=8, show=False, hardcopy=str(histogram_path))
    plt.close("all")

    plt.figure(figsize=(4, 3))
    df.viz.heatmap("x", "y", limits="minmax", shape=8, show=False, hardcopy=str(heatmap_path), title="tiny heatmap")
    plt.close("all")

    plt.figure(figsize=(4, 3))
    df.viz.scatter("x", "y", selection="nonnegative", length_limit=100, label="nonnegative", s_expr="weight", c_expr="radius")
    plt.tight_layout()
    plt.gcf().savefig(scatter_path, bbox_inches="tight")
    plt.close("all")

    files = {
        "histogram": {"path": str(histogram_path), "size": _assert_non_empty(histogram_path)},
        "heatmap": {"path": str(heatmap_path), "size": _assert_non_empty(heatmap_path)},
        "scatter": {"path": str(scatter_path), "size": _assert_non_empty(scatter_path)},
    }

    return {
        "ok": True,
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "output_dir": str(out_dir),
        "files": files,
        "row_count": int(df.count()),
        "selected_count": int(df.count(selection="nonnegative")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny Vaex visualization smoke check and print JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional base directory for the generated PNG files. A unique subdirectory will be created inside it.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(args.output_dir)
    except Exception as exc:  # keep failure machine-readable for calling agents
        failure = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(failure, indent=2 if args.pretty else None, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(summary, default=_json_default, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
