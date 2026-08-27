#!/usr/bin/env python3
"""Save a headless IKPy 3D plot using a tiny inline chain."""

from __future__ import annotations

import argparse
from pathlib import Path


_FORMATS = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a tiny self-contained IKPy chain without reading a robot "
            "file or connecting to hardware."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        metavar="PATH",
        help="output image path (.png, .pdf, .svg, .jpg, .tif, or .tiff)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacement of an existing output file",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="request Matplotlib show after saving (not used by default)",
    )
    return parser


def main() -> int:
    # Parse before optional imports so --help works without Matplotlib/IKPy.
    parser = _parser()
    args = parser.parse_args()
    output = args.output.expanduser()

    if output.suffix.lower() not in _FORMATS:
        parser.error("--output must have a supported image suffix")
    if output.exists() and output.is_dir():
        parser.error(f"--output is a directory: {output}")
    if output.exists() and not args.force:
        parser.error(f"output already exists; use --force to replace it: {output}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        parser.error(f"cannot create output directory {output.parent}: {exc}")

    import matplotlib

    # This must happen before pyplot or ikpy.utils.plot is imported.
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    import numpy as np

    from ikpy.chain import Chain
    from ikpy.link import URDFLink
    from ikpy.utils import plot

    links = [
        URDFLink(
            name="base",
            origin_translation=[0.0, 0.0, 0.0],
            origin_orientation=[0.0, 0.0, 0.0],
            joint_type="fixed",
            use_symbolic_matrix=False,
        ),
        URDFLink(
            name="joint",
            origin_translation=[0.0, 0.0, 0.6],
            origin_orientation=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 1.0],
            joint_type="revolute",
            use_symbolic_matrix=False,
        ),
        URDFLink(
            name="tip",
            origin_translation=[0.6, 0.0, 0.0],
            origin_orientation=[0.0, 0.0, 0.0],
            joint_type="fixed",
            use_symbolic_matrix=False,
        ),
    ]
    chain = Chain(
        links,
        active_links_mask=[False, True, False],
        name="inline-tiny-chain",
    )
    angle = 0.5
    joints = [0.0, angle, 0.0]
    target = np.array([0.6 * np.cos(angle), 0.6 * np.sin(angle), 0.6])

    fig, ax = plot.init_3d_figure()
    try:
        chain.plot(joints, ax=ax, target=target, show=False)
        fig.savefig(output, bbox_inches="tight")
        if args.show:
            plot.show_figure()
    finally:
        plt.close(fig)

    print(f"saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
