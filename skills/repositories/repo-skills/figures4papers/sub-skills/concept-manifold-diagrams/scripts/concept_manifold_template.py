#!/usr/bin/env python3
"""Self-contained figures4papers-style concept/manifold diagram templates.

Examples:
  python concept_manifold_template.py --example distribution --output output/distribution
  python concept_manifold_template.py --example manifold --output output/manifold --formats png,pdf
  python concept_manifold_template.py --example swiss-roll --output output/swiss_roll
  python concept_manifold_template.py --example sphere --output output/sphere --seed 7

All examples use deterministic synthetic data, validate key arrays, use a
headless matplotlib backend, and never read from the original repository.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_3": "#8BCF8B",
    "red_strong": "#B64342",
    "red_soft": "#D88F8A",
    "neutral": "#6F6F6F",
    "neutral_light": "#CFCECE",
    "teal": "#42949E",
    "violet": "#9A4D8E",
}
SUPPORTED_FORMATS = {"png", "pdf", "svg", "eps", "jpg", "jpeg", "tif", "tiff"}
EPS = 1e-9


def parse_formats(value: str) -> list[str]:
    formats = [part.strip().lower().lstrip(".") for part in value.split(",") if part.strip()]
    if not formats:
        raise argparse.ArgumentTypeError("--formats must not be empty")
    bad = sorted(set(formats) - SUPPORTED_FORMATS)
    if bad:
        raise argparse.ArgumentTypeError(f"unsupported format(s): {', '.join(bad)}")
    return formats


def apply_style(font_size: int = 15) -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": font_size,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 2.0,
        "legend.frameon": False,
        "svg.fonttype": "none",
    })


def output_base(path: Path) -> Path:
    return path.with_suffix("") if path.suffix.lower().lstrip(".") in SUPPORTED_FORMATS else path


def save_figure(fig: plt.Figure, output: Path, formats: Sequence[str], dpi: int) -> list[Path]:
    base = output_base(output)
    base.parent.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for fmt in formats:
        out = base.with_suffix(f".{fmt}")
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError(f"save failed or produced an empty file: {out}")
        saved.append(out)
    plt.close(fig)
    return saved


def finite_array(name: str, arr: np.ndarray, ndim: int | None = None) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")
    return arr


def gaussian(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    y = np.exp(-0.5 * ((x - mu) / sigma) ** 2)
    return y / max(float(y.max()), EPS)


def plot_distribution(seed: int) -> plt.Figure:
    del seed  # deterministic analytic curves only
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(17, 5.2))
    x = np.linspace(0.0, 1.0, 700)
    prior = gaussian(x, 0.30, 0.09)
    blind = 0.34 * gaussian(x, 0.32, 0.14) + 0.20
    guided = gaussian(x, 0.72, 0.08)
    curves = finite_array("curves", np.vstack([prior, blind, guided]), ndim=2)
    if curves.shape[1] != len(x):
        raise ValueError("all distribution curves must match x length")

    ax_left.plot(x, prior, color=PALETTE["neutral"], linewidth=2.2, label="Prior")
    ax_left.fill_between(x, 0, prior, color=PALETTE["neutral"], alpha=0.12)
    ax_left.plot(x, blind, color=PALETTE["red_soft"], linewidth=2.2, label="Blind")
    ax_left.fill_between(x, 0, blind, color=PALETTE["red_soft"], alpha=0.12)
    ax_left.plot(x, guided, color=PALETTE["blue_main"], linewidth=2.8, label="Guided")
    ax_left.fill_between(x, 0, guided, color=PALETTE["blue_main"], alpha=0.12)
    target_x = 0.72
    guided_y = float(np.interp(target_x, x, guided))
    blind_y = float(np.interp(target_x, x, blind))
    ax_left.vlines(target_x, 0, guided_y, color="black", linestyle=":", linewidth=1.8, alpha=0.65)
    ax_left.annotate("", xy=(target_x, guided_y), xytext=(target_x, blind_y),
                     arrowprops={"arrowstyle": "<->", "linewidth": 2.0, "color": "black"})
    ax_left.text(target_x + 0.025, 0.5 * (guided_y + blind_y), "gap", va="center", fontsize=18)
    ax_left.set_xlabel("Concept coordinate")
    ax_left.set_ylabel("Illustrative density")
    ax_left.legend(loc="upper center", ncols=3)

    rng = np.random.default_rng(42)
    t = np.linspace(0, 1, 300)
    ridge_text = np.column_stack([t, 0.20 + 0.09 * np.sin(2 * np.pi * t)])
    ridge_mm = np.column_stack([t, 0.72 + 0.08 * np.sin(2 * np.pi * t + 0.6)])
    pts_text = ridge_text[rng.integers(0, len(t), 700)] + rng.normal(0, [0.035, 0.045], size=(700, 2))
    pts_mm = ridge_mm[rng.integers(0, len(t), 700)] + rng.normal(0, [0.035, 0.045], size=(700, 2))
    ax_right.scatter(pts_mm[:, 0], pts_mm[:, 1], s=10, color=PALETTE["blue_secondary"], alpha=0.12, label="Target manifold")
    ax_right.scatter(pts_text[:, 0], pts_text[:, 1], s=10, color=PALETTE["neutral"], alpha=0.12, label="Prior manifold")
    ax_right.plot(ridge_text[:, 0], ridge_text[:, 1], linestyle="--", color=PALETTE["neutral"], linewidth=2.5)
    ax_right.plot(ridge_mm[:, 0], ridge_mm[:, 1], color=PALETTE["blue_main"], linewidth=3.0)
    ax_right.annotate("guided path", xy=(0.55, ridge_mm[165, 1]), xytext=(0.36, 0.95),
                      arrowprops={"arrowstyle": "->", "lw": 1.6},
                      bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9})
    ax_right.set_axis_off()
    ax_right.legend(loc="lower center", ncols=2)
    fig.tight_layout(pad=1.2)
    return fig


def try_kde(points: np.ndarray, grid: int = 130):
    try:
        from scipy.stats import gaussian_kde
    except Exception as exc:  # pragma: no cover - exercised only without scipy
        raise ImportError("KDE contours require scipy; install scipy or use a scatter-only design") from exc
    unique = np.unique(points.round(8), axis=0)
    if unique.shape[0] < 5:
        raise ValueError("KDE requires at least five unique 2D points")
    xmin, ymin = points.min(axis=0) - 0.5
    xmax, ymax = points.max(axis=0) + 0.5
    xx, yy = np.mgrid[xmin:xmax:complex(grid), ymin:ymax:complex(grid)]
    kde = gaussian_kde(points.T)
    zz = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    return xx, yy, zz


def plot_manifold(seed: int) -> plt.Figure:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 500)
    lower = np.column_stack([10 * t, 1.1 + 0.35 * np.sin(2 * np.pi * t)])
    upper = np.column_stack([10 * t, 4.2 + 0.30 * np.sin(2 * np.pi * t + 0.7)])
    idx_lower = rng.integers(0, len(t), 900)
    idx_upper = rng.integers(0, len(t), 900)
    points_lower = lower[idx_lower] + rng.normal(0, [0.18, 0.20], size=(900, 2))
    points_upper = upper[idx_upper] + rng.normal(0, [0.20, 0.22], size=(900, 2))
    finite_array("points_lower", points_lower, ndim=2)
    finite_array("points_upper", points_upper, ndim=2)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.scatter(points_upper[:, 0], points_upper[:, 1], s=9, color=PALETTE["blue_secondary"], alpha=0.10)
    ax.scatter(points_lower[:, 0], points_lower[:, 1], s=9, color=PALETTE["neutral"], alpha=0.10)
    for pts, color in [(points_upper, PALETTE["blue_main"]), (points_lower, PALETTE["neutral"] )]:
        xx, yy, zz = try_kde(pts)
        levels = np.quantile(zz, np.linspace(0.74, 0.99, 8))
        ax.contour(xx, yy, zz, levels=levels, colors=color, linewidths=1.3, alpha=0.35)
    ax.plot(lower[:, 0], lower[:, 1], linestyle="--", color=PALETTE["neutral"], linewidth=2.5, label="Prior ridge")
    ax.plot(upper[:, 0], upper[:, 1], color=PALETTE["blue_main"], linewidth=3.0, label="Target ridge")
    for xpos in [2.0, 4.5, 7.2]:
        y0 = np.interp(xpos, lower[:, 0], lower[:, 1])
        y1 = np.interp(xpos, upper[:, 0], upper[:, 1])
        ax.annotate("", xy=(xpos, y1), xytext=(xpos, y0),
                    arrowprops={"arrowstyle": "->", "lw": 2.0, "color": PALETTE["red_strong"]})
    ax.text(0.6, 4.85, "target manifold", bbox={"facecolor": "white", "edgecolor": "none"})
    ax.text(0.6, 0.35, "prior manifold", bbox={"facecolor": "white", "edgecolor": "none"})
    ax.set_axis_off()
    ax.legend(loc="lower center", ncols=2)
    fig.tight_layout(pad=1.0)
    return fig


def generate_swiss_roll(n_samples: int, rng: np.random.Generator, noise: float = 0.35):
    t = 1.5 * np.pi * (1 + 2 * rng.random(n_samples))
    x = t * np.cos(t) + noise * rng.normal(size=n_samples)
    z = t * np.sin(t) + noise * rng.normal(size=n_samples)
    return x, z, t


def compute_diffusion_matrix(points: np.ndarray, order_param: np.ndarray, sigma: float = 2.0, threshold: float = 0.02):
    order = np.argsort(order_param)
    points_sorted = points[order]
    t_sorted = order_param[order]
    diff = points_sorted[:, None, :] - points_sorted[None, :, :]
    spatial = np.sqrt(np.sum(diff * diff, axis=2))
    manifold = np.abs(t_sorted[:, None] - t_sorted[None, :])
    combined = spatial + 0.45 * manifold
    P = np.exp(-(combined ** 2) / (2 * sigma ** 2))
    P[P < threshold] = 0.0
    row_sums = P.sum(axis=1, keepdims=True)
    if np.any(row_sums <= 0):
        raise ValueError("diffusion matrix has an all-zero row; lower the threshold or add self-connections")
    P = P / row_sums
    if not np.allclose(P.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError("diffusion matrix rows are not normalized")
    return P, order


def plot_swiss_roll(seed: int) -> plt.Figure:
    rng = np.random.default_rng(seed)
    x, z, t = generate_swiss_roll(180, rng)
    points = np.column_stack([x, z])
    P, order = compute_diffusion_matrix(points, t)
    inverse_order = np.empty_like(order)
    inverse_order[order] = np.arange(len(order))

    fig, (ax_matrix, ax_cloud) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1, 1.2]})
    ax_matrix.imshow(P, cmap="Reds", aspect="equal", origin="upper")
    ax_matrix.set_axis_off()
    ax_matrix.set_title("Normalized diffusion matrix")

    threshold = 0.055
    for i in range(len(points)):
        row_i = inverse_order[i]
        strong = np.where(P[row_i] > threshold)[0]
        for row_j in strong[:8]:
            j = order[row_j]
            if i < j:
                prob = max(P[row_i, row_j], P[row_j, row_i])
                ax_cloud.plot([points[i, 0], points[j, 0]], [points[i, 1], points[j, 1]],
                              color="black", linewidth=1.1, alpha=min(0.8, prob * 6), zorder=1)
    scatter = ax_cloud.scatter(points[:, 0], points[:, 1], c=t, cmap="viridis", s=55,
                               alpha=0.65, edgecolors="white", linewidth=0.5, zorder=2)
    ax_cloud.set_aspect("equal")
    ax_cloud.set_axis_off()
    ax_cloud.set_title("Manifold point cloud")
    fig.colorbar(scatter, ax=ax_cloud, fraction=0.046, pad=0.04, label="Manifold order")
    fig.tight_layout(pad=1.0)
    return fig


def shaded_sphere(ax: plt.Axes, resolution: int = 220) -> None:
    xs = np.linspace(-1, 1, resolution)
    ys = np.linspace(-1, 1, resolution)
    x, y = np.meshgrid(xs, ys)
    r2 = x ** 2 + y ** 2
    mask = r2 <= 1.0
    z = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    normals = np.dstack([x, y, z])
    norms = np.linalg.norm(normals, axis=2, keepdims=True) + EPS
    normals = normals / norms
    light = np.array([-0.45, 0.55, 0.75])
    light = light / np.linalg.norm(light)
    intensity = np.clip(0.25 + 0.85 * np.sum(normals * light, axis=2), 0, 1)
    image = np.ones_like(intensity)
    image[mask] = intensity[mask]
    ax.imshow(image, extent=[-1, 1, -1, 1], origin="lower", cmap="gray", vmin=0, vmax=1)


def arc_points(a: np.ndarray, b: np.ndarray, n: int = 80) -> np.ndarray:
    a = a / (np.linalg.norm(a) + EPS)
    b = b / (np.linalg.norm(b) + EPS)
    theta = np.arccos(np.clip(np.dot(a, b), -1.0, 1.0))
    if theta < 1e-6:
        return np.repeat(a[None, :], n, axis=0)
    u = np.linspace(0, 1, n)
    pts = (np.sin((1 - u) * theta)[:, None] * a + np.sin(u * theta)[:, None] * b) / np.sin(theta)
    return pts


def plot_sphere(seed: int) -> plt.Figure:
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    shaded_sphere(ax)
    pts = np.array([[-0.45, 0.55], [0.65, 0.25], [-0.25, -0.58]])
    pts = finite_array("sphere_points", pts, ndim=2)
    for a, b, color, style in [(pts[0], pts[1], PALETTE["red_strong"], "-"),
                               (pts[1], pts[2], PALETTE["red_strong"], "-"),
                               (pts[2], pts[0], PALETTE["teal"], "--")]:
        arc = arc_points(a, b)
        ax.plot(arc[:, 0], arc[:, 1], color=color, linewidth=3.0, linestyle=style, alpha=0.85)
        mid = arc[len(arc) // 2]
        tangent = arc[min(len(arc) - 1, len(arc) // 2 + 1)] - arc[max(0, len(arc) // 2 - 1)]
        ax.arrow(mid[0], mid[1], 0.08 * tangent[0], 0.08 * tangent[1],
                 color=color, head_width=0.045, length_includes_head=True, linewidth=0)
    jitter = rng.normal(0, 0.01, size=pts.shape)
    ax.scatter(pts[:, 0] + jitter[:, 0], pts[:, 1] + jitter[:, 1], s=90,
               color=PALETTE["blue_main"], edgecolors="white", linewidth=1.0, zorder=5)
    ax.text(0, -1.28, "geodesic dispersion sketch", ha="center", fontsize=16)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.35, 1.18)
    ax.set_axis_off()
    fig.tight_layout(pad=0.5)
    return fig


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate figures4papers-style conceptual/manifold diagram examples.")
    parser.add_argument("--example", choices=["distribution", "manifold", "swiss-roll", "sphere"], default="distribution")
    parser.add_argument("--output", type=Path, default=Path("concept_manifold_template"),
                        help="Output basename or path. Extensions are controlled by --formats.")
    parser.add_argument("--formats", type=parse_formats, default=parse_formats("png,pdf"))
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed for synthetic examples.")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    apply_style()
    if args.example == "distribution":
        fig = plot_distribution(args.seed)
    elif args.example == "manifold":
        fig = plot_manifold(args.seed)
    elif args.example == "swiss-roll":
        fig = plot_swiss_roll(args.seed)
    else:
        fig = plot_sphere(args.seed)
    saved = save_figure(fig, args.output, args.formats, args.dpi)
    for path in saved:
        print(path)


if __name__ == "__main__":
    main()
