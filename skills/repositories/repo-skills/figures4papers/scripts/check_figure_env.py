#!/usr/bin/env python3
"""Check a Python environment for figures4papers-style plotting.

This diagnostic imports the expected plotting dependencies, checks optional
LaTeX availability, writes a tiny headless matplotlib figure when requested,
and reports actionable status lines. It does not read source-repository files,
make network calls, or modify existing outputs beyond the requested smoke path.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

REQUIRED_IMPORTS = ["numpy", "matplotlib"]
OPTIONAL_IMPORTS = ["scipy", "seaborn", "dateutil"]


def package_version(name: str) -> str:
    try:
        dist = "python-dateutil" if name == "dateutil" else name
        return version(dist)
    except PackageNotFoundError:
        return "unknown"


def check_import(name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(name)
        return True, package_version(name)
    except Exception as exc:  # pragma: no cover - diagnostic output path
        return False, f"{type(exc).__name__}: {exc}"


def write_smoke(output: Path, formats: list[str], dpi: int) -> list[Path]:
    import numpy as np
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    x = np.arange(5)
    fig, ax = plt.subplots(figsize=(3.0, 2.0))
    ax.plot(x, [0, 1, 0.4, 1.2, 0.8], color="#0F4D92", marker="o", linewidth=2)
    ax.set_title("figures4papers env smoke")
    ax.set_xlabel("step")
    ax.set_ylabel("value")
    fig.tight_layout(pad=1.0)
    base = output.with_suffix("") if output.suffix else output
    saved: list[Path] = []
    for fmt in formats:
        path = base.with_suffix(f".{fmt}")
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"failed to create non-empty smoke output: {path}")
        saved.append(path)
    plt.close(fig)
    return saved


def parse_formats(text: str) -> list[str]:
    values = [part.strip().lower().lstrip(".") for part in text.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("at least one format is required")
    allowed = {"png", "pdf", "svg"}
    bad = sorted(set(values) - allowed)
    if bad:
        raise argparse.ArgumentTypeError(f"unsupported smoke format(s): {', '.join(bad)}")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="Check plotting dependencies and headless export for figures4papers-style scripts.")
    parser.add_argument("--output", type=Path, default=Path("figure_env_smoke"),
                        help="Smoke output basename. Extensions are selected by --formats.")
    parser.add_argument("--formats", type=parse_formats, default=parse_formats("png"),
                        help="Comma-separated smoke formats: png,pdf,svg.")
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--skip-save", action="store_true", help="Only import dependencies; do not write a smoke figure.")
    parser.add_argument("--require-latex", action="store_true", help="Return nonzero if LaTeX is not available.")
    args = parser.parse_args()

    failures = []
    print("Required imports:")
    for name in REQUIRED_IMPORTS:
        ok, info = check_import(name)
        print(f"  {name}: {'ok' if ok else 'FAILED'} ({info})")
        if not ok:
            failures.append(name)

    print("Optional imports:")
    for name in OPTIONAL_IMPORTS:
        ok, info = check_import(name)
        print(f"  {name}: {'ok' if ok else 'missing'} ({info})")

    latex = shutil.which("latex")
    print(f"LaTeX: {'ok at ' + latex if latex else 'not found'}")
    if args.require_latex and not latex:
        failures.append("latex")

    if not args.skip_save and not failures:
        saved = write_smoke(args.output, args.formats, args.dpi)
        for path in saved:
            print(f"saved: {path} ({path.stat().st_size} bytes)")

    if failures:
        print("FAILED checks: " + ", ".join(failures))
        return 2
    print("figures4papers plotting environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
