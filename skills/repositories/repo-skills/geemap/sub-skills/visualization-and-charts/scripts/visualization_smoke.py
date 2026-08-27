#!/usr/bin/env python3
"""Safe geemap visualization smoke checks.

This script exercises palette, colorbar, and local chart helper behavior without
Earth Engine credentials. Optional visualization backends are reported only when
requested.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any


def _record(results: list[dict[str, Any]], name: str, status: str, detail: str = "", **extra: Any) -> None:
    item: dict[str, Any] = {"name": name, "status": status}
    if detail:
        item["detail"] = detail
    item.update(extra)
    results.append(item)


def _check_chart_helpers(results: list[dict[str, Any]]) -> None:
    import pandas as pd
    from geemap import chart

    dt = chart.DataTable(
        {"col1": [1, 2], "col2": [3, 4], "date": ["2022-01-01", "2022-01-02"]},
        date_column="date",
    )
    assert tuple(dt.shape) == (2, 3)
    assert pd.api.types.is_datetime64_any_dtype(dt["date"])

    df = pd.DataFrame({"label": ["A", "B"], "val1": [1, 2], "val2": [3, 4]})
    transposed = chart.transpose_df(df, "label")
    assert list(transposed.columns) == ["A", "B"]
    try:
        chart.transpose_df(df, "missing")
    except ValueError:
        pass
    else:
        raise AssertionError("transpose_df should reject a missing label column")

    arr_df = chart.array_to_df(
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        x_values=[10, 20, 30],
        y_labels=["a", "b"],
        x_label="time",
    )
    assert list(arr_df.columns) == ["time", "a", "b"]
    assert arr_df["b"].tolist() == [4.0, 5.0, 6.0]

    _record(results, "chart_helpers", "ok", "DataTable, transpose_df, and array_to_df passed")


def _check_colormaps(results: list[dict[str, Any]], colorbar_out: Path | None) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from geemap import colormaps

    ndvi = colormaps.get_palette("ndvi")
    assert len(ndvi) == 17 and ndvi[0] == "FFFFFF"

    viridis = colormaps.get_palette("viridis", n_class=5, hashtag=True)
    assert len(viridis) == 5 and viridis[0].startswith("#")

    terrain = colormaps.get_palette("terrain", n_class=3, hashtag=True)
    assert terrain == ["#333399", "#fefe98", "#ffffff"]

    fig = colormaps.get_colorbar(
        viridis,
        vmin=0,
        vmax=1,
        discrete=True,
        orientation="horizontal",
        return_fig=True,
    )
    assert fig is not None
    if colorbar_out is not None:
        colorbar_out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(colorbar_out, bbox_inches="tight")
    plt.close(fig)

    _record(results, "colormaps", "ok", "Named palettes and matplotlib colorbar passed")


def _check_cartoee_palette(results: list[dict[str, Any]]) -> None:
    from geemap import cartoee

    palette = cartoee.build_palette("viridis", 5)
    assert palette[0] == "#440154" and palette[-1] == "#fde725"
    _record(results, "cartoee_palette", "ok", "cartoee.build_palette passed")


def _check_plot_helpers(results: list[dict[str, Any]]) -> None:
    import pandas as pd
    from geemap import plot

    data = pd.DataFrame({"label": ["a", "b"], "value": [2, 1]})
    fig = plot.bar_chart(data, x="label", y="value", title="Smoke")
    assert len(fig.data) >= 1
    _record(results, "plot_helpers", "ok", "geemap.plot.bar_chart produced a Plotly figure")


def _optional_import(name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(name)
        return True, "import ok"
    except Exception as exc:  # optional dependencies may raise ImportError with guidance
        return False, f"{type(exc).__name__}: {exc}"


def _check_optional_backends(results: list[dict[str, Any]], require: bool) -> None:
    modules = {
        "plotlymap": "geemap.plotlymap",
        "deck": "geemap.deck",
        "kepler": "geemap.kepler",
        "maplibregl": "geemap.maplibregl",
    }
    missing: list[str] = []
    for label, module_name in modules.items():
        ok, detail = _optional_import(module_name)
        if ok:
            _record(results, f"optional_{label}", "ok", detail)
        else:
            missing.append(label)
            _record(results, f"optional_{label}", "missing", detail)

    if missing and require:
        raise AssertionError(f"Required optional backend(s) missing: {', '.join(missing)}")


def run(args: argparse.Namespace) -> tuple[int, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    checks = [
        ("chart_helpers", lambda: _check_chart_helpers(results)),
        ("colormaps", lambda: _check_colormaps(results, args.colorbar_out)),
        ("cartoee_palette", lambda: _check_cartoee_palette(results)),
        ("plot_helpers", lambda: _check_plot_helpers(results)),
    ]

    failed = False
    for name, func in checks:
        try:
            func()
        except Exception as exc:  # keep running to report all failures
            failed = True
            _record(
                results,
                name,
                "failed",
                f"{type(exc).__name__}: {exc}",
                traceback=traceback.format_exc(limit=5),
            )

    if args.check_optional_backends or args.require_optional_backends:
        try:
            _check_optional_backends(results, args.require_optional_backends)
        except Exception as exc:
            failed = True
            _record(
                results,
                "optional_backends_required",
                "failed",
                f"{type(exc).__name__}: {exc}",
            )

    return (1 if failed else 0), results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--colorbar-out",
        type=Path,
        default=None,
        help="Optional PNG path for the generated local matplotlib colorbar.",
    )
    parser.add_argument(
        "--check-optional-backends",
        action="store_true",
        help="Report import availability for plotlymap, deck, kepler, and maplibregl without failing on missing extras.",
    )
    parser.add_argument(
        "--require-optional-backends",
        action="store_true",
        help="Fail if any optional visualization backend import is unavailable.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to write the JSON result list.",
    )
    args = parser.parse_args(argv)

    code, results = run(args)
    payload = {"ok": code == 0, "results": results}
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
