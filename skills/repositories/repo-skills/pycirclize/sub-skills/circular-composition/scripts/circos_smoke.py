#!/usr/bin/env python3
"""Deterministic, offline smoke test for circular-composition skill guidance."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.projections.polar import PolarAxes

from pycirclize import Circos


def _expect_value_error(callable_obj, label: str) -> None:
    try:
        callable_obj()
    except ValueError:
        return
    raise AssertionError(f"expected ValueError for {label}")


def build_composition() -> Circos:
    """Build a small composition exercising global APIs and mixed directions."""
    circos = Circos(
        {"A": (0, 10), "B": (100, 130), "C": 8},
        start=15,
        end=345,
        space=[3, 8, 3],
        sector2clockwise={"C": False},
    )
    assert [sector.name for sector in circos.sectors] == ["A", "B", "C"]
    assert circos.get_sector("B").start == 100
    group_min, group_max = circos.get_group_sectors_deg_lim(["A", "B"])

    circos.axis(fc="none", ec="black", lw=0.5)
    circos.text("composition", r=50, deg=(group_min + group_max) / 2)
    circos.line(r=85, deg_lim=(group_min, group_max), color="grey", ls="dashed")
    circos.rect((90, 96), deg_lim=(group_min, group_max), fc="tomato", alpha=0.2)
    circos.link(("A", 2, 7), ("B", 120, 110), direction=1, color="steelblue")
    circos.link(
        ("B", 105, 125),
        ("C", 2, 6),
        direction=2,
        allow_twist=False,
        color="darkorange",
    )
    circos.link_line(("C", 1), ("A", 8), direction=-1, color="black")
    circos.colorbar(
        bounds=(0.84, 0.3, 0.025, 0.4),
        vmin=0,
        vmax=100,
        cmap="viridis",
        label="score",
    )
    return circos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="new PNG path for the caller-owned Figure export",
    )
    args = parser.parse_args()
    output = args.output.expanduser()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    # Constructor and lookup failures should be caught and repaired explicitly.
    _expect_value_error(lambda: Circos({"A": 1}, start=-10, end=360), "degree span")
    _expect_value_error(
        lambda: Circos({"A": 1, "B": 1, "C": 1}, space=[1], endspace=True),
        "space length",
    )
    _expect_value_error(lambda: Circos({"A": (4, 4)}), "tuple range")

    circos = build_composition()
    try:
        circos.get_sector("missing")
    except ValueError:
        pass
    else:
        raise AssertionError("missing sector lookup did not fail")

    try:
        _ = circos.ax
    except ValueError:
        pass
    else:
        raise AssertionError("ax was available before plotfig")

    # Verify the custom PolarAxes lifecycle and that the returned Figure is the owner.
    fig = plt.figure(figsize=(8, 8), dpi=100)
    polar_ax = fig.add_subplot(projection="polar")
    returned = circos.plotfig(ax=polar_ax)
    assert returned is fig
    assert isinstance(circos.ax, PolarAxes)
    circos.ax.legend(
        handles=[Line2D([], [], color="steelblue", label="directed link")],
        loc="upper right",
    )
    returned.savefig(output, dpi=100, bbox_inches="tight")
    assert output.exists() and output.stat().st_size > 0
    plt.close(returned)

    # Also exercise Circos.savefig without leaving a managed temporary file.
    with tempfile.TemporaryDirectory(prefix="pycirclize-circular-") as temp_dir:
        managed_output = Path(temp_dir) / "managed.png"
        static_circos = Circos({"left": 4, "right": 6}, space=2)
        static_circos.rect((80, 100), fc="lightgrey", ec="black")
        static_circos.savefig(managed_output)
        assert managed_output.exists() and managed_output.stat().st_size > 0

    print(f"circular composition smoke passed: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
