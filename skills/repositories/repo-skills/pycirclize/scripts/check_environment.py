#!/usr/bin/env python3
"""Offline pyCirclize import and tiny-render diagnostic.

Usage: python scripts/check_environment.py [--output PATH]
The default output is a temporary PNG. A caller-supplied output must not exist.
No network access is used.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from pycirclize import Circos, __version__
from pycirclize.parser import Bed, Genbank, Gff, Matrix, RadarTable, StackedBarTable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="optional new PNG output path")
    args = parser.parse_args()

    output = args.output.expanduser() if args.output else None
    if output is not None and output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")

    print(f"pycirclize {__version__}")
    print("public parser imports: ok")
    # Exercise the base dependency/rendering path without filesystem input.
    circos = Circos({"A": 3, "B": 2}, space=2)
    circos.get_sector("A").add_track((80, 100)).line([0, 3], [1, 2])
    if output is None:
        with tempfile.TemporaryDirectory(prefix="pycirclize-check-") as tmp:
            target = Path(tmp) / "smoke.png"
            circos.savefig(target)
            assert target.exists() and target.stat().st_size > 0
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        circos.savefig(output)
        assert output.exists() and output.stat().st_size > 0
        print(f"rendered: {output}")
    print("Agg render: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
