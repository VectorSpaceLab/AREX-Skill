#!/usr/bin/env python3
"""Self-contained template for trend, radar, and heatmap figures.

This script is deterministic, headless-friendly, and built entirely from
synthetic data. It does not read from a source repository or any external data
files. Use it as a safe starting point for publication-style matplotlib panels.
"""

from __future__ import annotations

import argparse
import math
import re
import shutil
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator

SUPPORTED_FORMATS = {
    "png",
    "pdf",
    "svg",
    "eps",
    "jpg",
    "jpeg",
    "tif",
    "tiff",
}

PALETTE = {
    "blue": "#0F4D92",
    "blue_light": "#9BC8FA",
    "green": "#8BCF8B",
    "green_light": "#DDF3DE",
    "red": "#D88F8A",
    "red_light": "#F6CFCB",
    "gray": "#767676",
    "gray_light": "#D0D0D0",
    "teal": "#4B9FA5",
    "gold": "#D9A441",
}


# -----------------------------------------------------------------------------
# Validation helpers
# -----------------------------------------------------------------------------


def as_float_array(name: str, values: Sequence[Sequence[float]] | Sequence[float], ndim: int | None = None) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}D, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def require_length(name: str, seq: Sequence[object], expected: int) -> None:
    actual = len(seq)
    if actual != expected:
        raise ValueError(f"{name} length {actual} does not match expected {expected}")


_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


def validate_month_label(label: str) -> None:
    match = _MONTH_RE.match(label)
    if match is None:
        raise ValueError(f"month label '{label}' must use YYYY-MM format")
    month = int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"month label '{label}' contains invalid month {month}")


def month_labels(start_year: int, start_month: int, n_months: int) -> list[str]:
    if n_months <= 0:
        raise ValueError("n_months must be positive")
    if not 1 <= start_month <= 12:
        raise ValueError("start_month must be in 1..12")
    year = start_year
    month = start_month
    out: list[str] = []
    for _ in range(n_months):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def normalize_formats(formats: str | Sequence[str]) -> list[str]:
    if isinstance(formats, str):
        tokens = [item.strip().lower() for item in formats.split(",")]
    else:
        tokens = [str(item).strip().lower() for item in formats]
    out = [item for item in tokens if item]
    if not out:
        raise ValueError("at least one output format must be provided")
    for fmt in out:
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(f"unsupported output format '{fmt}'. Supported: {sorted(SUPPORTED_FORMATS)}")
    # preserve order but remove duplicates
    seen: set[str] = set()
    unique: list[str] = []
    for fmt in out:
        if fmt not in seen:
            unique.append(fmt)
            seen.add(fmt)
    return unique


def strip_supported_suffix(path: Path) -> Path:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in SUPPORTED_FORMATS:
        return path.with_suffix("")
    return path


def luminance(rgba: Sequence[float]) -> float:
    r, g, b = rgba[:3]
    return 0.2126 * float(r) + 0.7152 * float(g) + 0.0722 * float(b)


def contrast_text_color(cmap, norm, value: float) -> str:
    return "black" if luminance(cmap(norm(value))) > 0.55 else "white"


def format_value(value: float, fmt: str) -> str:
    fmt = fmt.strip()
    if not fmt:
        return str(value)
    if "{" in fmt:
        return fmt.format(value)
    return format(value, fmt)


# -----------------------------------------------------------------------------
# Style
# -----------------------------------------------------------------------------


def configure_matplotlib(use_tex: bool = False) -> None:
    if use_tex and shutil.which("latex") is None:
        raise RuntimeError("--use-tex requested but latex is not available on PATH")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "sans-serif"],
            "font.size": 12,
            "axes.labelsize": 13,
            "axes.titlesize": 13,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 11,
            "axes.linewidth": 2.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.08,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "text.usetex": bool(use_tex),
        }
    )


# -----------------------------------------------------------------------------
# Trend example
# -----------------------------------------------------------------------------


def build_trend_example() -> dict[str, object]:
    x_labels = month_labels(2024, 1, 8)
    series_labels = ["Proposed", "Baseline"]
    # Monthly increments; the template converts them to cumulative counts.
    values = np.array(
        [
            [2, 3, 4, 5, 6, 6, 7, 8],
            [1, 1, 2, 2, 3, 3, 4, 4],
        ],
        dtype=float,
    )
    events = [
        {"x": "2024-02", "label": "Data refresh"},
        {"x": "2024-05", "label": "Model update"},
        {"x": "2024-07", "label": "Full rollout"},
    ]
    return {
        "x_labels": x_labels,
        "series_labels": series_labels,
        "values": values,
        "cumulative": True,
        "events": events,
        "ylabel": "Cumulative count",
        "xlabel": "Month",
    }


def validate_trend_data(data: dict[str, object]) -> tuple[list[str], list[str], np.ndarray, list[dict[str, str]], bool]:
    x_labels = list(data["x_labels"])
    series_labels = list(data["series_labels"])
    values = as_float_array("trend values", data["values"], ndim=2)
    require_length("series_labels", series_labels, values.shape[0])
    require_length("x_labels", x_labels, values.shape[1])
    for label in x_labels:
        validate_month_label(label)
    events = list(data.get("events", []))
    cumulative = bool(data.get("cumulative", True))
    for event in events:
        if not isinstance(event, dict):
            raise TypeError("trend events must be dictionaries")
        if "x" not in event or "label" not in event:
            raise ValueError("each trend event needs 'x' and 'label'")
        if event["x"] not in x_labels:
            raise ValueError(f"trend event x='{event['x']}' is not present in x_labels")
    if cumulative and np.any(values < 0):
        raise ValueError("cumulative trend values should not be negative in the built-in template")
    return x_labels, series_labels, values, events, cumulative


def plot_trend(ax: plt.Axes, data: dict[str, object]) -> None:
    x_labels, series_labels, values, events, cumulative = validate_trend_data(data)
    x = np.arange(len(x_labels), dtype=float)
    series = np.cumsum(values, axis=1) if cumulative else values
    colors = [PALETTE["blue"], PALETTE["gray"], PALETTE["green"], PALETTE["red"]]
    markers = ["o", "s", "D", "^"]

    for idx, row in enumerate(series):
        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]
        ax.fill_between(x, 0, row, color=color, alpha=0.12, linewidth=0)
        ax.plot(
            x,
            row,
            color=color,
            linewidth=2.6,
            marker=marker,
            markersize=5,
            label=series_labels[idx],
            zorder=3,
        )

    ref = series.max(axis=0)
    ymin = 0.0
    ymax = float(np.max(ref))
    span = max(ymax - ymin, 1.0)
    for event_idx, event in enumerate(events):
        pos = x_labels.index(event["x"])
        y = float(ref[pos])
        ax.axvline(pos, color="0.35", linestyle="--", linewidth=0.9, alpha=0.25, zorder=1)
        offset = 0.08 * span * (1.0 + 0.55 * (event_idx % 3))
        ax.annotate(
            event["label"],
            xy=(pos, y),
            xytext=(pos, y + offset),
            ha="center",
            va="bottom",
            fontsize=10.5,
            arrowprops=dict(arrowstyle="-|>", color="0.25", lw=1.0, shrinkA=0, shrinkB=0, mutation_scale=12),
        )

    tick_step = max(1, math.ceil(len(x_labels) / 6))
    tick_positions = x[::tick_step]
    tick_labels = x_labels[::tick_step]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(-0.25, len(x_labels) - 0.75)
    ax.set_ylim(ymin, ymax + 0.28 * span)
    ax.set_xlabel(str(data.get("xlabel", "Month")))
    ax.set_ylabel(str(data.get("ylabel", "Value")))
    ax.grid(axis="y", color="0.90", linewidth=0.8)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.legend(frameon=False, loc="upper left")


# -----------------------------------------------------------------------------
# Radar example
# -----------------------------------------------------------------------------


def build_radar_example() -> dict[str, object]:
    methods = ["Ours", "Baseline A", "Baseline B"]
    spoke_specs = [
        {"label": "Accuracy", "range": (78.0, 92.0), "ticks": [80.0, 84.0, 88.0, 92.0]},
        {"label": "F1", "range": (60.0, 80.0), "ticks": [62.0, 68.0, 74.0, 80.0]},
        {"label": "Latency ↓", "range": (70.0, 24.0), "ticks": [68.0, 56.0, 44.0, 32.0, 24.0]},
        {"label": "Robustness", "range": (0.65, 0.90), "ticks": [0.70, 0.78, 0.84, 0.90]},
    ]
    values = np.array(
        [
            [89.0, 76.0, 28.0, 0.87],
            [84.0, 71.0, 41.0, 0.80],
            [81.0, 66.0, 58.0, 0.74],
        ],
        dtype=float,
    )
    return {"methods": methods, "spoke_specs": spoke_specs, "values": values}


def validate_radar_data(data: dict[str, object]) -> tuple[list[str], list[dict[str, object]], np.ndarray]:
    methods = list(data["methods"])
    specs = list(data["spoke_specs"])
    values = as_float_array("radar values", data["values"], ndim=2)
    require_length("methods", methods, values.shape[0])
    require_length("spoke_specs", specs, values.shape[1])
    for idx, spec in enumerate(specs):
        if not isinstance(spec, dict):
            raise TypeError("each radar spoke spec must be a dictionary")
        for key in ("label", "range", "ticks"):
            if key not in spec:
                raise ValueError(f"radar spoke spec {idx} is missing key '{key}'")
        label = str(spec["label"])
        lo, hi = spec["range"]
        lo = float(lo)
        hi = float(hi)
        if lo == hi:
            raise ValueError(f"radar spoke '{label}' has zero span")
        ticks = as_float_array(f"radar spoke '{label}' ticks", spec["ticks"], ndim=1)
        if len(ticks) == 0:
            raise ValueError(f"radar spoke '{label}' must define at least one tick")
    return methods, specs, values


def normalize_radar_value(value: float, lo: float, hi: float) -> float:
    frac = (value - lo) / (hi - lo)
    return float(np.clip(frac, 0.0, 1.0))


def plot_radar(ax: plt.Axes, data: dict[str, object]) -> None:
    methods, specs, values = validate_radar_data(data)
    n_spokes = len(specs)
    angles = np.linspace(0.0, 2.0 * np.pi, n_spokes, endpoint=False)
    angles_closed = np.concatenate([angles, [angles[0]]])
    colors = [PALETTE["blue"], PALETTE["green"], PALETTE["red"], PALETTE["gray"]]

    ax.set_theta_offset(np.pi / 2.0)
    ax.set_theta_direction(-1)
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    try:
        ax.spines["polar"].set_visible(False)
    except Exception:
        pass

    # Per-spoke ticks and labels.
    for angle, spec in zip(angles, specs):
        label = str(spec["label"])
        lo, hi = spec["range"]
        lo = float(lo)
        hi = float(hi)
        ticks = [float(t) for t in spec["ticks"]]
        # Skip the first tick when there is more than one tick so the center stays readable.
        tick_values = ticks[1:] if len(ticks) > 1 else ticks
        for tick in tick_values:
            radius = normalize_radar_value(tick, lo, hi)
            ax.plot([angle, angle], [max(0.0, radius - 0.015), min(1.0, radius + 0.015)], color="0.60", lw=0.8, zorder=1)
            ax.text(
                angle,
                radius,
                format_value(tick, ".0f" if abs(tick - round(tick)) < 1e-8 else ".2f"),
                fontsize=8,
                ha="center",
                va="center",
                rotation=0,
                clip_on=False,
            )
        ax.text(
            angle,
            1.12,
            label,
            fontsize=11,
            ha="center",
            va="center",
            clip_on=False,
            fontweight="bold",
        )

    # Outer boundary and spokes.
    ax.plot(angles_closed, np.ones_like(angles_closed), color="0.45", lw=0.9, zorder=0)
    for angle in angles:
        ax.plot([angle, angle], [0.0, 1.0], color="0.82", lw=0.75, zorder=0)

    for method_idx, method in enumerate(methods):
        color = colors[method_idx % len(colors)]
        normalized = []
        for spoke_idx, spec in enumerate(specs):
            lo, hi = spec["range"]
            lo = float(lo)
            hi = float(hi)
            normalized.append(normalize_radar_value(float(values[method_idx, spoke_idx]), lo, hi))
        normalized = np.asarray(normalized, dtype=float)
        normalized_closed = np.concatenate([normalized, [normalized[0]]])
        ax.plot(angles_closed, normalized_closed, color=color, lw=2.2, label=method, zorder=3)
        ax.fill(angles_closed, normalized_closed, color=color, alpha=0.09, zorder=2)
        ax.scatter(angles, normalized, s=20, color=color, zorder=4, edgecolors="white", linewidths=0.4)

    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.02))


# -----------------------------------------------------------------------------
# Heatmap example
# -----------------------------------------------------------------------------


def build_heatmap_example() -> dict[str, object]:
    matrix = np.array(
        [
            [16, 12, 8, 5, 3],
            [13, 14, 10, 7, 4],
            [9, 11, 15, 12, 6],
            [6, 8, 12, 16, 9],
            [3, 5, 7, 11, 17],
        ],
        dtype=float,
    )
    row_labels = ["Task A", "Task B", "Task C", "Task D", "Task E"]
    col_labels = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5"]
    return {
        "matrix": matrix,
        "row_labels": row_labels,
        "col_labels": col_labels,
        "annot_format": ".0f",
        "cbar_label": "Score",
        "cmap": "magma",
        "xlabel": "Condition",
        "ylabel": "Category",
    }


def validate_heatmap_data(data: dict[str, object]) -> tuple[np.ndarray, list[str], list[str]]:
    matrix = as_float_array("heatmap matrix", data["matrix"], ndim=2)
    row_labels = list(data["row_labels"])
    col_labels = list(data["col_labels"])
    require_length("row_labels", row_labels, matrix.shape[0])
    require_length("col_labels", col_labels, matrix.shape[1])
    return matrix, row_labels, col_labels


def plot_heatmap(ax: plt.Axes, fig: plt.Figure, data: dict[str, object]) -> None:
    matrix, row_labels, col_labels = validate_heatmap_data(data)
    cmap = plt.get_cmap(str(data.get("cmap", "magma")))
    vmin = float(np.min(matrix))
    vmax = float(np.max(matrix))
    if vmin == vmax:
        vmax = vmin + 1.0
    norm = Normalize(vmin=vmin, vmax=vmax)

    im = ax.imshow(matrix, cmap=cmap, norm=norm, interpolation="nearest", aspect="auto")
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)
    ax.set_xlabel(str(data.get("xlabel", "Column")))
    ax.set_ylabel(str(data.get("ylabel", "Row")))
    ax.set_xlim(-0.5, len(col_labels) - 0.5)
    ax.set_ylim(len(row_labels) - 0.5, -0.5)
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1.0), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1.0), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.1)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fmt = str(data.get("annot_format", ".0f"))
    fontsize = 10 if max(matrix.shape) <= 6 else 8
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = float(matrix[i, j])
            text_color = contrast_text_color(cmap, norm, value)
            ax.text(
                j,
                i,
                format_value(value, fmt),
                ha="center",
                va="center",
                color=text_color,
                fontsize=fontsize,
                fontweight="bold",
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label(str(data.get("cbar_label", "Value")))
    cbar.ax.tick_params(labelsize=10)


# -----------------------------------------------------------------------------
# Output helpers
# -----------------------------------------------------------------------------


def save_figure(fig: plt.Figure, output: str | Path, formats: Sequence[str], dpi: int) -> list[Path]:
    base = strip_supported_suffix(Path(output).expanduser())
    base.parent.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    for fmt in formats:
        path = base.with_suffix(f".{fmt}")
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.08)
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"failed to write output file: {path}")
        saved_paths.append(path)
    plt.close(fig)
    return saved_paths


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create deterministic trend, radar, or heatmap examples with built-in synthetic data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--example",
        choices=("trend", "radar", "heatmap"),
        default="trend",
        help="Choose which built-in synthetic example to render.",
    )
    parser.add_argument(
        "--output",
        default="trend_radar_heatmap_example",
        help="Output basename or path stem. The script appends each requested format.",
    )
    parser.add_argument(
        "--formats",
        default="png,pdf",
        help="Comma-separated output formats such as png,pdf,svg.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Raster DPI used for PNG and rasterized elements in vector exports.",
    )
    parser.add_argument(
        "--use-tex",
        action="store_true",
        help="Enable LaTeX text rendering when latex is available on PATH.",
    )
    return parser.parse_args(argv)


def build_figure(example: str) -> plt.Figure:
    if example == "trend":
        fig, ax = plt.subplots(figsize=(12.8, 5.8))
        plot_trend(ax, build_trend_example())
        fig.tight_layout(pad=1.2)
        return fig
    if example == "radar":
        fig, ax = plt.subplots(figsize=(10.4, 8.2), subplot_kw={"projection": "polar"})
        plot_radar(ax, build_radar_example())
        fig.subplots_adjust(left=0.06, right=0.78, top=0.95, bottom=0.08)
        return fig
    if example == "heatmap":
        fig, ax = plt.subplots(figsize=(8.8, 6.8))
        plot_heatmap(ax, fig, build_heatmap_example())
        fig.tight_layout(pad=1.2)
        return fig
    raise ValueError(f"unknown example '{example}'")


def main(argv: Sequence[str] | None = None) -> list[Path]:
    args = parse_args(argv)
    configure_matplotlib(use_tex=args.use_tex)
    formats = normalize_formats(args.formats)
    fig = build_figure(args.example)
    return save_figure(fig, args.output, formats, args.dpi)


if __name__ == "__main__":
    saved = main()
    for path in saved:
        print(path)
