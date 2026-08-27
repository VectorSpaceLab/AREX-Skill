#!/usr/bin/env python3
"""Reusable figures4papers-style matplotlib helpers.

This module is a self-contained helper library for future figure scripts. It
sets portable publication rcParams, validates common array shapes, and provides
small helpers for grouped bars, trends, heatmaps, scatter plots, shaded spheres,
and multi-format export.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
    "dark_neutral": "#4D4D4D",
    "highlight": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
}
DEFAULT_COLORS = [PALETTE[k] for k in ["blue_main", "green_3", "red_2", "teal", "violet", "neutral"]]
SUPPORTED_FORMATS = {"png", "pdf", "svg", "eps", "jpg", "jpeg", "tif", "tiff"}


@dataclass(frozen=True)
class FigureStyle:
    font_size: int = 16
    axes_linewidth: float = 2.5
    use_tex: bool = False
    font_family: tuple[str, ...] = ("DejaVu Sans", "Arial", "Helvetica", "sans-serif")


def apply_publication_style(style: FigureStyle | None = None) -> None:
    """Apply portable figures4papers-style matplotlib rcParams."""
    style = style or FigureStyle()
    plt.rcParams.update({
        "text.usetex": bool(style.use_tex),
        "font.family": list(style.font_family),
        "font.size": style.font_size,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": style.axes_linewidth,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })


def create_subplots(nrows: int = 1, ncols: int = 1, figsize: tuple[float, float] | None = None, **kwargs):
    """Return `(fig, axes)` with `axes` flattened to a 1D NumPy array."""
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, **kwargs)
    return fig, np.atleast_1d(axes).ravel()


def _output_base(path: str | Path) -> Path:
    path = Path(path)
    return path.with_suffix("") if path.suffix.lower().lstrip(".") in SUPPORTED_FORMATS else path


def finalize_figure(fig: plt.Figure, out_path: str | Path, formats: Sequence[str] | None = None,
                    dpi: int = 300, close: bool = True, pad: float = 0.05, **savefig_kwargs) -> list[Path]:
    """Save a figure to one or more formats, creating parent directories.

    If `formats` is None, use the extension in `out_path` when present or save
    PNG and PDF by default.
    """
    path = Path(out_path)
    if formats is None:
        suffix = path.suffix.lower().lstrip(".")
        formats = [suffix] if suffix in SUPPORTED_FORMATS else ["png", "pdf"]
    formats = [fmt.lower().lstrip(".") for fmt in formats]
    bad = sorted(set(formats) - SUPPORTED_FORMATS)
    if bad:
        raise ValueError(f"unsupported format(s): {', '.join(bad)}")
    base = _output_base(path)
    base.parent.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for fmt in formats:
        target = base.with_suffix(f".{fmt}")
        fig.savefig(target, dpi=dpi, bbox_inches="tight", pad_inches=pad, **savefig_kwargs)
        if not target.exists() or target.stat().st_size == 0:
            raise RuntimeError(f"failed to save non-empty file: {target}")
        saved.append(target)
    if close:
        plt.close(fig)
    return saved


def _as_1d(name: str, values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite 1D array")
    return arr


def _as_2d(name: str, values: Sequence[Sequence[float]]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2 or not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be a finite 2D array")
    return arr


def make_grouped_bar(ax: plt.Axes, categories: Sequence[str], series: Sequence[Sequence[float]],
                     labels: Sequence[str], ylabel: str = "Value", colors: Sequence[str] | None = None,
                     errors: Sequence[Sequence[float]] | None = None, annotate: bool = False):
    """Render grouped bars with validation and optional annotations."""
    values = _as_2d("series", series)
    if values.shape != (len(labels), len(categories)):
        raise ValueError(f"series shape {values.shape} must equal (len(labels), len(categories))")
    err = None if errors is None else _as_2d("errors", errors)
    if err is not None and err.shape != values.shape:
        raise ValueError("errors must have the same shape as series")
    colors = list(colors or DEFAULT_COLORS)
    x = np.arange(len(categories))
    width = 0.78 / len(labels)
    offsets = (np.arange(len(labels)) - (len(labels) - 1) / 2) * width
    containers = []
    for i, label in enumerate(labels):
        bars = ax.bar(x + offsets[i], values[i], width=width,
                      yerr=None if err is None else err[i], capsize=5,
                      color=colors[i % len(colors)], edgecolor="black", linewidth=1.6,
                      label=label)
        containers.append(bars)
        if annotate:
            annotate_bars(ax, bars, errors=None if err is None else err[i])
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel)
    return containers


def annotate_bars(ax: plt.Axes, bars: Iterable, errors: Sequence[float] | None = None,
                  fmt: str = "{:.2f}", fontsize: int = 10, padding: float | None = None) -> None:
    heights = np.asarray([bar.get_height() for bar in bars], dtype=float)
    err = np.zeros_like(heights) if errors is None else np.asarray(errors, dtype=float)
    span = max(float(np.max(heights + err) - np.min(heights - err)), 1e-9)
    pad = 0.03 * span if padding is None else padding
    for bar, value, e in zip(bars, heights, err):
        ax.text(bar.get_x() + bar.get_width() / 2, value + e + pad,
                fmt.format(value), ha="center", va="bottom", fontsize=fontsize)


def make_trend(ax: plt.Axes, x: Sequence[float], y_series: Sequence[Sequence[float]], labels: Sequence[str],
               colors: Sequence[str] | None = None, ylabel: str | None = None, xlabel: str | None = None,
               show_shadow: bool = True) -> None:
    x_arr = _as_1d("x", x)
    values = _as_2d("y_series", y_series)
    if values.shape != (len(labels), len(x_arr)):
        raise ValueError("y_series must have shape (len(labels), len(x))")
    colors = list(colors or DEFAULT_COLORS)
    for i, label in enumerate(labels):
        ax.plot(x_arr, values[i], color=colors[i % len(colors)], linewidth=2.5, marker="o", label=label)
        if show_shadow:
            ax.fill_between(x_arr, values[i], alpha=0.08, color=colors[i % len(colors)])
    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)


def make_heatmap(ax: plt.Axes, matrix: Sequence[Sequence[float]], x_labels: Sequence[str] | None = None,
                 y_labels: Sequence[str] | None = None, cmap: str = "magma", cbar_label: str | None = None,
                 annotate: bool = False):
    arr = _as_2d("matrix", matrix)
    im = ax.imshow(arr, cmap=cmap, aspect="auto")
    if x_labels is not None:
        if len(x_labels) != arr.shape[1]:
            raise ValueError("x_labels length must match matrix columns")
        ax.set_xticks(np.arange(arr.shape[1]))
        ax.set_xticklabels(x_labels)
    if y_labels is not None:
        if len(y_labels) != arr.shape[0]:
            raise ValueError("y_labels length must match matrix rows")
        ax.set_yticks(np.arange(arr.shape[0]))
        ax.set_yticklabels(y_labels)
    if annotate:
        norm, cmap_obj = im.norm, im.cmap
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                rgba = cmap_obj(norm(arr[i, j]))
                lum = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                ax.text(j, i, f"{arr[i, j]:.2g}", ha="center", va="center",
                        color="black" if lum > 0.55 else "white")
    cbar = ax.figure.colorbar(im, ax=ax)
    if cbar_label:
        cbar.set_label(cbar_label)
    return im


def make_scatter(ax: plt.Axes, x: Sequence[float], y: Sequence[float], label: str | None = None,
                 color: str | None = None, size: float = 50, alpha: float = 0.7):
    x_arr, y_arr = _as_1d("x", x), _as_1d("y", y)
    if len(x_arr) != len(y_arr):
        raise ValueError("x and y must have the same length")
    return ax.scatter(x_arr, y_arr, label=label, color=color or PALETTE["blue_main"], s=size, alpha=alpha)


def make_sphere_illustration(ax: plt.Axes, light_dir: tuple[float, float, float] = (-0.5, 0.5, 0.8),
                             resolution: int = 160, alpha: float = 0.6):
    xs = np.linspace(-1, 1, resolution)
    ys = np.linspace(-1, 1, resolution)
    x, y = np.meshgrid(xs, ys)
    r2 = x ** 2 + y ** 2
    mask = r2 <= 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    normals = np.dstack([x, y, z])
    normals /= np.linalg.norm(normals, axis=2, keepdims=True) + 1e-9
    light = np.asarray(light_dir, dtype=float)
    light /= np.linalg.norm(light) + 1e-9
    shade = np.clip(0.25 + 0.85 * np.sum(normals * light, axis=2), 0, 1)
    image = np.ones_like(shade)
    image[mask] = shade[mask]
    return ax.imshow(image, cmap="gray", extent=[-1, 1, -1, 1], origin="lower", alpha=alpha)
