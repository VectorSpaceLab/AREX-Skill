#!/usr/bin/env python3
"""Check optional umap.plot dependencies and optionally run a tiny smoke.

The helper is safe by default: it performs no installs, downloads, network
access, destructive writes, or large training. The smoke path uses sklearn's
bundled iris dataset and a tiny UMAP fit only when required dependencies are
already installed.
"""

from __future__ import annotations

import argparse
import importlib.util
from typing import Iterable

BASE_MODULES = (
    ("umap", "umap"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("sklearn", "scikit-learn"),
    ("numba", "numba"),
    ("pynndescent", "pynndescent"),
    ("tqdm", "tqdm"),
)

PLOT_MODULES = (
    ("pandas", "pandas"),
    ("matplotlib", "matplotlib"),
    ("datashader", "datashader"),
    ("bokeh", "bokeh"),
    ("holoviews", "holoviews"),
    ("colorcet", "colorcet"),
    ("skimage", "scikit-image"),
)

OPTIONAL_PLOT_MODULES = (
    ("dask", "dask"),
    ("seaborn", "seaborn"),
)

PLOT_INSTALL_PIP = 'pip install "umap-learn[plot]"'
PLOT_INSTALL_CONDA = "conda install pandas matplotlib datashader bokeh holoviews colorcet scikit-image"


def spec_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def collect_missing(modules: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    return [(module, package) for module, package in modules if not spec_available(module)]


def print_status_line(title: str, modules: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    modules = tuple(modules)
    missing = collect_missing(modules)
    missing_modules = {module for module, _ in missing}
    statuses = []
    for module, package in modules:
        state = "missing" if module in missing_modules else "ok"
        statuses.append(f"{package}:{state}")
    print(f"{title}: " + "; ".join(statuses))
    return missing


def print_advice(missing_base: list[tuple[str, str]], missing_plot: list[tuple[str, str]]) -> None:
    if missing_base:
        print("Base UMAP runtime is incomplete; repair base dependencies before checking optional plotting.")
        print("Missing base modules: " + ", ".join(package for _, package in missing_base))
        print("Typical base install command:")
        print("  pip install umap-learn")
        return

    if missing_plot:
        print("Optional umap.plot stack is incomplete. This is not a base UMAP failure.")
        print("Missing plotting modules: " + ", ".join(package for _, package in missing_plot))
        print("Install the plotting extra:")
        print(f"  {PLOT_INSTALL_PIP}")
        print("Or use the equivalent conda package set:")
        print(f"  {PLOT_INSTALL_CONDA}")
        print("Fallback: use mapper.embedding_ with plain matplotlib or export the embedding.")
        return

    print("Base runtime and core optional plotting modules appear available.")


def run_report() -> int:
    print("UMAP plotting stack report")
    missing_base = print_status_line("Base runtime", BASE_MODULES)
    missing_plot = print_status_line("Plot extra", PLOT_MODULES)
    print_status_line("Other optional plot-extra modules", OPTIONAL_PLOT_MODULES)
    print_advice(missing_base, missing_plot)
    return 0


def run_smoke(rows: int, subset_stride: int) -> int:
    missing_base = collect_missing(BASE_MODULES)
    if missing_base:
        print("Cannot run smoke checks because the base runtime is incomplete.")
        print("Missing base modules: " + ", ".join(package for _, package in missing_base))
        print("Install base UMAP first; this script will not install anything.")
        return 2

    missing_plot = collect_missing(PLOT_MODULES)
    if missing_plot:
        print("Cannot run plotting smoke checks because optional umap.plot dependencies are missing.")
        print("Missing plotting modules: " + ", ".join(package for _, package in missing_plot))
        print("Install advice:")
        print(f"  {PLOT_INSTALL_PIP}")
        print(f"  {PLOT_INSTALL_CONDA}")
        return 3

    import numpy as np
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    import pandas as pd
    from sklearn.datasets import load_iris

    import umap
    from umap import plot as umap_plot

    data, target = load_iris(return_X_y=True)
    rows = max(8, min(rows, data.shape[0]))
    data = data[:rows]
    target = target[:rows]

    subset = np.ones(rows, dtype=bool)
    if subset_stride > 1:
        subset[::subset_stride] = False
        if not subset.any():
            subset[0] = True

    mapper = umap.UMAP(
        n_neighbors=min(5, max(2, rows - 1)),
        n_components=2,
        random_state=42,
        n_epochs=20,
    ).fit(data)

    steps: list[str] = []

    fig, ax = plt.subplots()
    umap_plot.points(mapper, labels=target, ax=ax)
    fig.canvas.draw()
    plt.close(fig)
    steps.append("points(labels)")

    fig, ax = plt.subplots()
    umap_plot.points(mapper, values=data[:, 0], subset_points=subset, ax=ax)
    fig.canvas.draw()
    plt.close(fig)
    steps.append("points(values, subset)")

    fig, ax = plt.subplots()
    umap_plot.nearest_neighbour_distribution(mapper, ax=ax)
    fig.canvas.draw()
    plt.close(fig)
    steps.append("nearest_neighbour_distribution")

    conn_ax = umap_plot.connectivity(mapper, show_points=True)
    conn_ax.figure.canvas.draw()
    plt.close(conn_ax.figure)
    steps.append("connectivity(show_points)")

    diagnostic = umap_plot.diagnostic(
        mapper,
        diagnostic_type="neighborhood",
        return_diagnostics=True,
        plot_result=False,
    )
    if diagnostic is None:
        raise RuntimeError("diagnostic(neighborhood) returned no data")
    steps.append("diagnostic(neighborhood, data-only)")

    hover = pd.DataFrame({"row_id": np.arange(rows), "label": target.astype(str)})
    interactive_plot = umap_plot.interactive(
        mapper,
        labels=target,
        hover_data=hover,
        subset_points=subset,
        interactive_text_search=True,
        interactive_text_search_columns=["label"],
        point_size=6,
    )
    if interactive_plot is None:
        raise RuntimeError("interactive returned no plot object")
    steps.append("interactive(hover/search)")

    print("Smoke passed: " + ", ".join(steps))
    return 0


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report optional umap.plot dependencies and run a tiny smoke when installed.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print dependency availability and actionable install/fallback advice.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Fit a tiny mapper and exercise non-rendering plotting calls when dependencies are installed.",
    )
    parser.add_argument(
        "--rows",
        type=positive_int,
        default=24,
        help="Number of bundled iris rows to use for --smoke.",
    )
    parser.add_argument(
        "--subset-stride",
        type=positive_int,
        default=3,
        help="Stride used to create a row-aligned subset mask in --smoke.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.report and not args.smoke:
        return run_report()

    exit_code = 0
    if args.report:
        exit_code = max(exit_code, run_report())
    if args.smoke:
        exit_code = max(exit_code, run_smoke(args.rows, args.subset_stride))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
