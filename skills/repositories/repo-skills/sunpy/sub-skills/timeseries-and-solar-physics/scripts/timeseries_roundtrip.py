#!/usr/bin/env python3
"""Create, transform, and ECSV-round-trip a tiny local SunPy TimeSeries."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import astropy.units as u
import pandas as pd
from astropy.table import Table

from sunpy.timeseries import GenericTimeSeries, TimeSeries


def build_series() -> GenericTimeSeries:
    """Return a deterministic in-memory series with complete units."""
    index = pd.date_range("2020-01-01T00:00:00", periods=6, freq="min")
    data = pd.DataFrame(
        {
            "flux": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "counts": [10, 12, 11, 15, 14, 16],
        },
        index=index,
    )
    return GenericTimeSeries(
        data,
        meta={"instrument": "synthetic", "purpose": "local round-trip smoke"},
        units={"flux": u.W / u.m**2, "counts": u.ct},
    )


def round_trip(ts: GenericTimeSeries, path: Path) -> GenericTimeSeries:
    """Write an Astropy ECSV table and load it through the TimeSeries factory."""
    table = ts.to_table()
    # ECSV's portable schema does not list numpy datetime64 dtypes. Store the
    # leading date column as ISO strings; TimeSeries converts it back on read.
    table["date"] = [str(value) for value in table["date"]]
    table.meta["purpose"] = "local round-trip smoke"
    table.write(path, format="ascii.ecsv", overwrite=True)
    restored_table = Table.read(path, format="ascii.ecsv")
    restored = TimeSeries(restored_table)
    if not isinstance(restored, GenericTimeSeries):
        raise AssertionError(f"Expected GenericTimeSeries, got {type(restored)!r}")
    return restored


def validate(original: GenericTimeSeries, restored: GenericTimeSeries) -> None:
    """Assert the data, time axis, columns, and units survived the round trip."""
    if original.columns != restored.columns:
        raise AssertionError((original.columns, restored.columns))
    pd.testing.assert_frame_equal(
        original.to_dataframe(),
        restored.to_dataframe(),
        check_freq=False,
    )
    for column in original.columns:
        if original.units[column] != restored.units[column]:
            raise AssertionError(
                f"Unit mismatch for {column}: "
                f"{original.units[column]} != {restored.units[column]}"
            )
    if original.time_range != restored.time_range:
        raise AssertionError("Time ranges differ after ECSV round trip")


def save_plot(ts: GenericTimeSeries, path: Path) -> None:
    """Save a non-interactive plot using an explicit headless backend."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots()
    ts.plot(axes=ax, columns=["flux"])
    ax.set_title("Synthetic SunPy TimeSeries")
    fig.savefig(path, dpi=120)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a network-free GenericTimeSeries construction, transformation, "
            "and temporary ECSV round-trip smoke."
        )
    )
    parser.add_argument(
        "--plot",
        type=Path,
        help="Optional PNG output path; uses the non-interactive Agg backend.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    original = build_series()

    # Verify a local selection and a pandas resample followed by reconstruction.
    window = original.truncate("2020-01-01 00:01", "2020-01-01 00:04")
    if window.shape != (4, 2):
        raise AssertionError(f"Unexpected truncated shape: {window.shape}")
    resampled_df = original.to_dataframe().resample("2min").mean()
    resampled = GenericTimeSeries(resampled_df, original.meta, original.units)
    if resampled.shape != (3, 2):
        raise AssertionError(f"Unexpected resampled shape: {resampled.shape}")

    with tempfile.TemporaryDirectory(prefix="sunpy-timeseries-") as directory:
        ecsv_path = Path(directory) / "tiny-timeseries.ecsv"
        restored = round_trip(original, ecsv_path)
        validate(original, restored)

    if args.plot is not None:
        save_plot(original, args.plot)

    print(
        json.dumps(
            {
                "status": "ok",
                "class": type(original).__name__,
                "shape": list(original.shape),
                "columns": original.columns,
                "units": {name: str(unit) for name, unit in original.units.items()},
                "start": original.time_range.start.isot,
                "end": original.time_range.end.isot,
                "resampled_shape": list(resampled.shape),
                "plot": str(args.plot) if args.plot is not None else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
