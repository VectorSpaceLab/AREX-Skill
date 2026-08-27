#!/usr/bin/env python3
"""Offline seaborn environment diagnostic for generated repo skill users."""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def status(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        return False, f"missing or failed import: {exc}"
    version = getattr(mod, "__version__", "unknown")
    return True, str(version)


def render_smoke(output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    df = pd.DataFrame({"x": [0, 1, 2, 3], "y": [1.0, 2.0, 1.5, 3.0], "g": ["a", "a", "b", "b"]})
    fig, ax = plt.subplots(figsize=(4, 3))
    sns.lineplot(data=df, x="x", y="y", hue="g", marker="o", ax=ax)
    ax.set(title="seaborn smoke")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check seaborn imports and optional plotting dependencies.")
    parser.add_argument("--render-smoke", action="store_true", help="Render a tiny Agg-backed plot.")
    parser.add_argument("--output", default="seaborn_smoke.png", help="Output path for --render-smoke.")
    args = parser.parse_args(argv)

    required = ["seaborn", "numpy", "pandas", "matplotlib"]
    optional = ["scipy", "statsmodels", "fastcluster", "ipywidgets"]
    failed = False
    print(f"python={sys.version.split()[0]}")
    for name in required:
        ok, info = status(name)
        print(f"required {name}: {'OK' if ok else 'FAIL'} ({info})")
        failed = failed or not ok
    for name in optional:
        ok, info = status(name)
        print(f"optional {name}: {'OK' if ok else 'SKIP'} ({info})")
    if args.render_smoke and not failed:
        try:
            render_smoke(Path(args.output))
        except Exception as exc:  # noqa: BLE001
            print(f"render smoke: FAIL ({exc})", file=sys.stderr)
            return 1
        print(f"render smoke: OK ({args.output})")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
