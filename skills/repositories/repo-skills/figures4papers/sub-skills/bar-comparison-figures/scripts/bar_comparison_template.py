#!/usr/bin/env python3
"""Self-contained bar comparison template for publication-style figures.

The script has two deterministic built-in examples:

    python bar_comparison_template.py --example grouped --output figures/grouped
    python bar_comparison_template.py --example horizontal-ablation --formats png pdf

Use the plotting functions and example dictionaries as a starting point for
user-provided values.  The runtime has no network access needs and reads no
external project files.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

# Force a non-interactive backend before importing pyplot so the script works in
# headless batch jobs and CI environments.
matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import Patch


PALETTE = {
    "key": "#0F4D92",  # proposed / focal method
    "key_light": "#3775BA",
    "positive": "#AADCA9",  # related positive family
    "positive_light": "#DDF3DE",
    "contrast": "#E9A6A1",  # contrasting baseline
    "contrast_dark": "#B64342",
    "neutral": "#CFCECE",  # background baseline
    "neutral_dark": "#767676",
}

HATCHES = ["", "//", "\\\\", "xx", "..", "--"]
SUPPORTED_FORMATS = {"png", "pdf", "svg", "eps", "jpg", "jpeg", "tif", "tiff"}


class BarComparisonError(ValueError):
    """Raised when input data cannot produce an unambiguous bar figure."""


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_formats(tokens: Sequence[str]) -> list[str]:
    """Parse comma-separated or space-separated format names."""
    formats: list[str] = []
    for token in tokens:
        for raw in token.replace(",", " ").split():
            fmt = raw.strip().lower().lstrip(".")
            if not fmt:
                continue
            if fmt not in SUPPORTED_FORMATS:
                supported = ", ".join(sorted(SUPPORTED_FORMATS))
                raise BarComparisonError(
                    f"unsupported output format {raw!r}; supported formats: {supported}"
                )
            if fmt not in formats:
                formats.append(fmt)
    if not formats:
        raise BarComparisonError("--formats must request at least one format")
    return formats


def output_stem(output: str | Path) -> Path:
    """Return a file stem; extensions are replaced by requested formats."""
    stem = Path(output)
    if stem.name in {"", ".", ".."}:
        raise BarComparisonError("--output must be a file path or file stem, not a directory")
    if stem.suffix:
        stem = stem.with_suffix("")
    return stem


def apply_style(use_tex: bool = False) -> None:
    """Apply a portable, headless-friendly publication bar style."""
    plt.rcParams.update(
        {
            "text.usetex": bool(use_tex),
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "sans-serif"],
            "font.size": 13,
            "axes.labelsize": 15,
            "axes.titlesize": 16,
            "axes.linewidth": 1.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "xtick.major.width": 1.5,
            "ytick.major.width": 1.5,
            "legend.fontsize": 12,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def require_nonempty_names(names: Sequence[str], field_name: str) -> list[str]:
    if isinstance(names, (str, bytes)) or not isinstance(names, Sequence):
        raise BarComparisonError(f"{field_name} must be a non-empty list of labels")
    clean = [str(name) for name in names]
    if not clean:
        raise BarComparisonError(f"{field_name} must not be empty")
    if any(not name.strip() for name in clean):
        raise BarComparisonError(f"{field_name} contains an empty label")
    return clean


def as_2d_float_array(values: object, field_name: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise BarComparisonError(f"{field_name} must contain numeric values") from exc
    if array.ndim != 2:
        raise BarComparisonError(f"{field_name} must be 2D; got shape {array.shape}")
    if array.size == 0:
        raise BarComparisonError(f"{field_name} must not be empty")
    if not np.all(np.isfinite(array)):
        raise BarComparisonError(f"{field_name} contains NaN or infinite values")
    return array


def validate_error_array(errors: object | None, expected_shape: tuple[int, int], field_name: str) -> np.ndarray | None:
    if errors is None:
        return None
    array = as_2d_float_array(errors, field_name)
    if array.shape != expected_shape:
        raise BarComparisonError(
            f"{field_name} shape {array.shape} does not match expected shape {expected_shape}"
        )
    if np.any(array < 0):
        raise BarComparisonError(f"{field_name} must be non-negative")
    return array


def semantic_colors(count: int) -> list[str]:
    base = [
        PALETTE["key"],
        PALETTE["positive"],
        PALETTE["contrast"],
        PALETTE["neutral"],
        PALETTE["key_light"],
        PALETTE["contrast_dark"],
        PALETTE["neutral_dark"],
        PALETTE["positive_light"],
    ]
    return [base[index % len(base)] for index in range(count)]


def format_value(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 100:
        return f"{value:.0f}"
    if magnitude >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def linear_limits(values: np.ndarray, errors: np.ndarray | None = None) -> tuple[float, float, float]:
    lower_values = values if errors is None else values - errors
    upper_values = values if errors is None else values + errors
    lo = float(np.min(lower_values))
    hi = float(np.max(upper_values))
    span = max(hi - lo, 1e-9)
    abs_ref = max(abs(lo), abs(hi), 1.0)
    margin = max(0.08 * span, 0.015 * abs_ref)

    if lo >= 0:
        # Tighten score-like ranges, but keep zero for wider absolute comparisons.
        lower = max(0.0, lo - margin) if lo / max(hi, 1e-9) > 0.75 else 0.0
    else:
        lower = lo - margin
    upper = hi + 2.5 * margin
    if lower == upper:
        upper = lower + 1.0
    return lower, upper, margin


def grouped_example_data() -> dict[str, object]:
    return {
        "title": "Grouped benchmark comparison",
        "categories": ["Dataset A", "Dataset B", "Dataset C"],
        "groups": ["Proposed", "Related baseline", "Contrast baseline"],
        "values": [
            [0.91, 0.87, 0.89],
            [0.83, 0.81, 0.78],
            [0.76, 0.74, 0.73],
        ],
        "errors": [
            [0.02, 0.02, 0.01],
            [0.03, 0.02, 0.02],
            [0.02, 0.03, 0.02],
        ],
        "ylabel": "Score",
    }


def horizontal_ablation_example_data() -> dict[str, object]:
    return {
        "title": "Horizontal component ablation",
        "components": ["Context", "Retrieval", "Refine"],
        "codes": ["111", "110", "101", "011", "100"],
        "metrics": ["AUROC", "AUPRC"],
        "mean": [
            [0.91, 0.72],
            [0.87, 0.64],
            [0.86, 0.63],
            [0.82, 0.55],
            [0.78, 0.48],
        ],
        "err": [
            [0.01, 0.02],
            [0.02, 0.03],
            [0.02, 0.02],
            [0.02, 0.03],
            [0.03, 0.04],
        ],
    }


def validate_grouped_data(data: dict[str, object]) -> tuple[list[str], list[str], np.ndarray, np.ndarray | None, list[str], str, str]:
    categories = require_nonempty_names(data.get("categories", []), "categories")
    groups = require_nonempty_names(data.get("groups", []), "groups")
    values = as_2d_float_array(data.get("values"), "values")
    expected_shape = (len(groups), len(categories))
    if values.shape != expected_shape:
        raise BarComparisonError(
            f"values shape {values.shape} does not match expected shape "
            f"(len(groups), len(categories)) = {expected_shape}"
        )
    errors = validate_error_array(data.get("errors"), expected_shape, "errors")

    colors_obj = data.get("colors")
    colors = semantic_colors(len(groups)) if colors_obj is None else list(colors_obj)  # type: ignore[arg-type]
    if len(colors) != len(groups):
        raise BarComparisonError(
            f"colors length {len(colors)} does not match len(groups) = {len(groups)}"
        )
    ylabel = str(data.get("ylabel", "Value"))
    title = str(data.get("title", "Grouped bar comparison"))
    return categories, groups, values, errors, colors, ylabel, title


def plot_grouped_bars(data: dict[str, object]) -> plt.Figure:
    categories, groups, values, errors, colors, ylabel, title = validate_grouped_data(data)
    n_groups, n_categories = values.shape
    x = np.arange(n_categories)
    total_width = min(0.82, max(0.58, 0.78))
    bar_width = total_width / n_groups
    offsets = (np.arange(n_groups) - (n_groups - 1) / 2.0) * bar_width

    fig_width = max(7.5, 2.2 * n_categories + 1.2 * n_groups)
    fig, ax = plt.subplots(figsize=(fig_width, 5.4))

    ymin, ymax, pad = linear_limits(values, errors)
    label_positions: list[float] = []

    for group_index, group_name in enumerate(groups):
        group_errors = None if errors is None else errors[group_index]
        bars = ax.bar(
            x + offsets[group_index],
            values[group_index],
            width=bar_width * 0.95,
            yerr=group_errors,
            capsize=5,
            color=colors[group_index],
            edgecolor="black",
            linewidth=1.6,
            hatch=HATCHES[group_index % len(HATCHES)],
            label=group_name,
            error_kw={"capthick": 1.6, "elinewidth": 1.6, "ecolor": "black"},
        )
        error_values = np.zeros(n_categories) if group_errors is None else group_errors
        for bar, value, err_value in zip(bars, values[group_index], error_values):
            center = bar.get_x() + bar.get_width() / 2.0
            if value >= 0:
                y_text = float(value + err_value + pad)
                va = "bottom"
            else:
                y_text = float(value - err_value - pad)
                va = "top"
            label_positions.append(y_text)
            ax.text(
                center,
                y_text,
                format_value(float(value)),
                ha="center",
                va=va,
                fontsize=10.5,
                rotation=0,
            )

    if label_positions:
        ymin = min(ymin, min(label_positions) - pad)
        ymax = max(ymax, max(label_positions) + 1.2 * pad)
    ax.set_ylim(ymin, ymax)
    if ymin < 0 < ymax:
        ax.axhline(0, color="black", linewidth=1.0, alpha=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=14)
    ax.grid(axis="y", color="#BBBBBB", alpha=0.35, linewidth=0.8)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.22),
        ncols=min(n_groups, 3),
        frameon=False,
        handlelength=1.8,
        columnspacing=1.2,
    )
    fig.tight_layout()
    return fig


def decode_component_codes(codes: Sequence[str], components: Sequence[str]) -> list[str]:
    decoded: list[str] = []
    for code in codes:
        if len(code) != len(components):
            raise BarComparisonError(
                f"ablation code {code!r} has length {len(code)}, "
                f"expected len(components) = {len(components)}"
            )
        invalid = sorted(set(code) - {"0", "1"})
        if invalid:
            raise BarComparisonError(
                f"ablation code {code!r} contains invalid characters {invalid}; use only '0' and '1'"
            )
        active = [component for bit, component in zip(code, components) if bit == "1"]
        label = " + ".join(active) if active else "None"
        decoded.append(textwrap.fill(label, width=28, break_long_words=False))
    return decoded


def validate_ablation_data(data: dict[str, object]) -> tuple[list[str], list[str], list[str], np.ndarray, np.ndarray | None, str]:
    components = require_nonempty_names(data.get("components", []), "components")
    codes = require_nonempty_names(data.get("codes", []), "codes")
    metrics = require_nonempty_names(data.get("metrics", []), "metrics")
    mean = as_2d_float_array(data.get("mean"), "mean")
    expected_shape = (len(codes), len(metrics))
    if mean.shape != expected_shape:
        raise BarComparisonError(
            f"mean shape {mean.shape} does not match expected shape "
            f"(len(codes), len(metrics)) = {expected_shape}"
        )
    err = validate_error_array(data.get("err"), expected_shape, "err")
    decoded_labels = decode_component_codes(codes, components)
    title = str(data.get("title", "Horizontal ablation comparison"))
    return decoded_labels, codes, metrics, mean, err, title


def ablation_facecolors(codes: Sequence[str]) -> list[tuple[float, float, float, float]]:
    width = max(len(code) for code in codes)
    colors: list[tuple[float, float, float, float]] = []
    for code in codes:
        active_count = code.count("1")
        completeness = active_count / max(width, 1)
        if active_count == width:
            base = PALETTE["key"]
            alpha = 1.0
        elif active_count >= max(width - 1, 1):
            base = PALETTE["positive"]
            alpha = 0.65 + 0.25 * completeness
        else:
            base = PALETTE["neutral"]
            alpha = 0.35 + 0.4 * completeness
        colors.append(to_rgba(base, alpha))
    return colors


def legend_for_ablation(codes: Sequence[str]) -> list[Patch]:
    width = max(len(code) for code in codes)
    handles = [Patch(facecolor=PALETTE["key"], edgecolor="black", label="Full variant")]
    if any(code.count("1") >= max(width - 1, 1) and code.count("1") != width for code in codes):
        handles.append(
            Patch(facecolor=PALETTE["positive"], edgecolor="black", label="Near-complete variant")
        )
    if any(code.count("1") < max(width - 1, 1) for code in codes):
        handles.append(Patch(facecolor=PALETTE["neutral"], edgecolor="black", label="Smaller subset"))
    return handles


def plot_horizontal_ablation(data: dict[str, object]) -> plt.Figure:
    labels, codes, metrics, mean, err, title = validate_ablation_data(data)
    n_rows, n_metrics = mean.shape
    y_positions = np.arange(n_rows)
    facecolors = ablation_facecolors(codes)

    fig_width = max(8.0, 4.8 * n_metrics + 2.2)
    fig_height = max(4.4, 0.62 * n_rows + 2.2)
    fig, axes_array = plt.subplots(1, n_metrics, sharey=True, figsize=(fig_width, fig_height))
    axes = np.atleast_1d(axes_array)

    for metric_index, (ax, metric_name) in enumerate(zip(axes, metrics)):
        values = mean[:, metric_index]
        metric_err = None if err is None else err[:, metric_index]
        bars = ax.barh(
            y_positions,
            values,
            xerr=metric_err,
            color=facecolors,
            edgecolor="black",
            linewidth=1.5,
            capsize=5,
            error_kw={"capthick": 1.5, "elinewidth": 1.5, "ecolor": "black"},
        )

        err_values = np.zeros(n_rows) if metric_err is None else metric_err
        xmin, xmax, pad = linear_limits(values, metric_err)
        label_positions: list[float] = []
        for bar, value, err_value in zip(bars, values, err_values):
            y_text = bar.get_y() + bar.get_height() / 2.0
            if value >= 0:
                x_text = float(value + err_value + pad)
                ha = "left"
            else:
                x_text = float(value - err_value - pad)
                ha = "right"
            label_positions.append(x_text)
            ax.text(x_text, y_text, format_value(float(value)), va="center", ha=ha, fontsize=10.5)

        if label_positions:
            xmin = min(xmin, min(label_positions) - pad)
            xmax = max(xmax, max(label_positions) + 1.4 * pad)
        ax.set_xlim(xmin, xmax)
        if xmin < 0 < xmax:
            ax.axvline(0, color="black", linewidth=1.0, alpha=0.6)
        ax.set_title(metric_name, pad=10)
        ax.grid(axis="x", color="#BBBBBB", alpha=0.35, linewidth=0.8)
        ax.set_xlabel("Value")
        ax.set_yticks(y_positions)
        if metric_index == 0:
            ax.set_yticklabels(labels)
        else:
            ax.tick_params(axis="y", labelleft=False)

    if not axes[0].yaxis_inverted():
        axes[0].invert_yaxis()

    handles = legend_for_ablation(codes)
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncols=len(handles),
        frameon=False,
        handlelength=1.8,
        columnspacing=1.4,
    )
    fig.suptitle(title, y=1.05, fontsize=17)
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=2.0)
    return fig


def save_figure(fig: plt.Figure, output: str | Path, formats: Iterable[str], dpi: int) -> list[Path]:
    stem = output_stem(output)
    written: list[Path] = []
    for fmt in formats:
        target = stem.with_suffix(f".{fmt}")
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, format=fmt, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
        if not target.exists() or target.stat().st_size <= 0:
            raise BarComparisonError(f"save failed or produced an empty file: {target}")
        written.append(target)
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draw deterministic publication-style bar comparison examples.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--example",
        choices=("grouped", "horizontal-ablation"),
        default="grouped",
        help="Built-in example to render.",
    )
    parser.add_argument(
        "--output",
        default="bar_comparison_template",
        help="Output file stem or file path. Any extension is replaced by --formats.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["png", "pdf"],
        help="Output formats; pass comma-separated or space-separated names.",
    )
    parser.add_argument("--dpi", type=positive_int, default=300, help="Raster output DPI.")
    parser.add_argument(
        "--use-tex",
        action="store_true",
        help="Enable matplotlib text.usetex; omit unless a TeX installation is available.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    fig: plt.Figure | None = None
    try:
        formats = parse_formats(args.formats)
        apply_style(use_tex=args.use_tex)
        if args.example == "grouped":
            fig = plot_grouped_bars(grouped_example_data())
        elif args.example == "horizontal-ablation":
            fig = plot_horizontal_ablation(horizontal_ablation_example_data())
        else:  # pragma: no cover - argparse choices prevent this branch.
            raise BarComparisonError(f"unknown example {args.example!r}")
        written = save_figure(fig, args.output, formats, args.dpi)
    except BarComparisonError as exc:
        print(f"bar_comparison_template.py: error: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        if args.use_tex:
            print(
                "bar_comparison_template.py: error: rendering failed with --use-tex; "
                "verify a working TeX installation or rerun without --use-tex. "
                f"Details: {exc}",
                file=sys.stderr,
            )
            return 2
        raise
    finally:
        if fig is not None:
            plt.close(fig)

    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
