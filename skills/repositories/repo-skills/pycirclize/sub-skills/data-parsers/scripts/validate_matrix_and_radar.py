#!/usr/bin/env python3
"""Validate tiny pyCirclize parser and chord/radar export workflows.

This deterministic helper uses in-memory data plus temporary local TSV/CSV/BED
fixtures. It performs no network access and removes its temporary directory on
exit. Run it with ``python scripts/validate_matrix_and_radar.py`` from any
working directory after installing pyCirclize.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd

from pycirclize import Circos
from pycirclize.parser import Bed, Matrix, RadarTable, StackedBarTable


def _assert_png(path: Path) -> None:
    assert path.exists(), f"expected export was not created: {path.name}"
    assert path.stat().st_size > 100, f"export is unexpectedly small: {path.name}"
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path.name}"


def validate() -> dict[str, object]:
    """Run deterministic parser, conversion, validation, and export checks."""
    matrix_df = pd.DataFrame(
        [[2, 1], [3, 0]], index=["A", "B"], columns=["A", "B"]
    )
    radar_df = pd.DataFrame(
        [[20, 50, 80], [70, 40, 90]],
        index=["row-a", "row-b"],
        columns=["metric-1", "metric-2", "metric-3"],
    )
    fromto_df = pd.DataFrame(
        [["A", "B", 2], ["A", "A", 1], ["B", "A", 3]],
        columns=["from", "to", "value"],
    )
    stacked_df = pd.DataFrame(
        [[1, 2], [3, 4]], index=["row-a", "row-b"], columns=["x", "y"]
    )

    matrix = Matrix(matrix_df)
    assert matrix.row_names == ["A", "B"]
    assert matrix.col_names == ["A", "B"]
    assert set(matrix.to_sectors()) == {"A", "B"}
    assert len(matrix.to_links()) == 3
    assert list(matrix.to_fromto_table().columns) == ["from", "to", "value"]

    fromto_matrix = Matrix.parse_fromto_table(fromto_df, order=["A", "B"])
    assert fromto_matrix.dataframe.loc["A", "B"] == 2
    assert fromto_matrix.dataframe.loc["A", "A"] == 1
    assert fromto_matrix.dataframe.loc["B", "A"] == 3

    stacked = StackedBarTable(stacked_df)
    assert stacked.row_name2sum == {"row-a": 3, "row-b": 7}
    assert stacked.stacked_bar_bottoms == [[0, 0], [1, 3]]

    radar = RadarTable(radar_df)
    assert radar.row_name2values["row-a"] == [20, 50, 80]
    assert len(radar.get_row_tooltip("row-a")) == 3

    with tempfile.TemporaryDirectory(prefix="pycirclize-data-parsers-") as temp:
        temp_dir = Path(temp)
        matrix_path = temp_dir / "matrix.csv"
        matrix_df.to_csv(matrix_path)
        loaded_matrix = Matrix(matrix_path, delimiter=",")
        assert loaded_matrix.dataframe.equals(matrix_df)

        radar_path = temp_dir / "radar.tsv"
        radar_df.to_csv(radar_path, sep="\t")
        loaded_radar = RadarTable(radar_path, delimiter="\t")
        assert loaded_radar.dataframe.equals(radar_df)

        bed_path = temp_dir / "tiny.bed"
        bed_path.write_text(
            "# comment\nchr1\t0\t10\tfeature-a\t5\nchr2\t3\t9\n",
            encoding="utf-8",
        )
        records = Bed(bed_path).records
        assert [(record.chr, record.start, record.end) for record in records] == [
            ("chr1", 0, 10),
            ("chr2", 3, 9),
        ]
        assert [record.size for record in records] == [10, 6]

        # The factory has no delimiter parameter; pass the delimiter-aware
        # Matrix object when the source file is not tab-delimited.
        chord = Circos.chord_diagram(
            loaded_matrix,
            cmap={"A": "#4477AA", "B": "#CC6677"},
            order=["A", "B"],
        )
        chord_path = temp_dir / "chord.png"
        chord.savefig(chord_path)
        _assert_png(chord_path)

        radar_chart = Circos.radar_chart(
            loaded_radar,
            vmin=0,
            vmax=100,
            marker_size=2,
            cmap={"row-a": "#4477AA", "row-b": "#CC6677"},
        )
        radar_path_out = temp_dir / "radar.png"
        radar_chart.savefig(radar_path_out)
        _assert_png(radar_path_out)

    try:
        Circos.radar_chart(radar_df, vmin=50, vmax=50)
    except ValueError as exc:
        assert "vmax must be larger than vmin" in str(exc)
    else:
        raise AssertionError("radar_chart accepted vmin >= vmax")

    return {
        "matrix_links": len(matrix.to_links()),
        "fromto_labels": fromto_matrix.all_names,
        "bed_records": len(records),
        "exports": ["chord.png", "radar.png"],
        "invalid_radar_range": "rejected",
    }


def main() -> int:
    """Parse optional verbosity and run the validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only use the exit status; suppress the result summary",
    )
    args = parser.parse_args()
    result = validate()
    if not args.quiet:
        print("pyCirclize data-parser validation passed")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
