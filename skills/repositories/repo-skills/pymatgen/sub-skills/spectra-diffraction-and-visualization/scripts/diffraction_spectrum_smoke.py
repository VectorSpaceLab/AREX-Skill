#!/usr/bin/env python3
"""Headless smoke check for pymatgen diffraction and spectrum plotting APIs.

The script builds a tiny in-memory crystal, computes XRD peaks, creates a toy
XAS spectrum, and saves plots using a noninteractive matplotlib backend. It
performs no network access and writes only inside the user-specified output
directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymatgen.core import Structure


def build_structure() -> "Structure":
    """Return a simple CsCl-like cubic structure."""
    from pymatgen.core import Lattice, Structure

    return Structure(
        Lattice.cubic(4.209),
        ["Cs", "Cl"],
        [[0, 0, 0], [0.5, 0.5, 0.5]],
    )


def write_outputs(output_dir: Path, max_peaks: int) -> dict:
    """Compute XRD and toy XAS outputs and return a compact summary."""
    import matplotlib

    matplotlib.use("Agg")

    import numpy as np
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.analysis.xas.spectrum import XAS
    from pymatgen.vis.plotters import SpectrumPlotter

    output_dir.mkdir(parents=True, exist_ok=True)
    structure = build_structure()

    xrd_calculator = XRDCalculator(wavelength="CuKa")
    pattern = xrd_calculator.get_pattern(structure, two_theta_range=(0, 90))
    xrd_axes = xrd_calculator.get_plot(structure, two_theta_range=(0, 90), annotate_peaks=None)
    xrd_path = output_dir / "xrd.png"
    xrd_axes.figure.savefig(xrd_path, dpi=120, bbox_inches="tight")

    energy = np.linspace(7700, 7800, 201)
    intensity = np.exp(-0.5 * ((energy - 7728) / 4) ** 2) + 0.2 * np.exp(-0.5 * ((energy - 7750) / 8) ** 2)
    xas = XAS(energy, intensity, structure, "Cs", edge="K", spectrum_type="XANES", absorbing_index=0)
    plotter = SpectrumPlotter(xshift=xas.e0, yshift=0.1)
    plotter.add_spectrum("toy Cs K-edge XANES", xas, color="b")
    xas_path = output_dir / "toy-xas.png"
    plotter.save_plot(str(xas_path), xlim=(-30, 80))

    peak_count = min(max_peaks, len(pattern.x))
    peaks = [
        {
            "two_theta": round(float(pattern.x[idx]), 6),
            "intensity": round(float(pattern.y[idx]), 6),
            "hkls": pattern.hkls[idx],
            "d_hkl": round(float(pattern.d_hkls[idx]), 6),
        }
        for idx in range(peak_count)
    ]
    summary = {
        "formula": structure.formula,
        "xrd_peak_count": len(pattern.x),
        "reported_peaks": peaks,
        "xas_e0": round(float(xas.e0), 6),
        "files": [str(xrd_path), str(xas_path)],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute a tiny XRD pattern and save a toy XAS plot using pymatgen with an Agg backend."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("diffraction-spectrum-smoke-output"),
        help="Directory for xrd.png, toy-xas.png, and summary.json.",
    )
    parser.add_argument(
        "--max-peaks",
        type=int,
        default=5,
        help="Number of leading XRD peaks to include in the printed summary.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_peaks < 1:
        raise SystemExit("--max-peaks must be positive")
    summary = write_outputs(args.output_dir, args.max_peaks)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
