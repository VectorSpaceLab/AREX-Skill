#!/usr/bin/env python3
"""Offline smoke check for Lux Clause, Vis, VisList, and chart export APIs.

The script uses only an in-memory dataframe. It is intended for users who have
installed lux-api and want to verify direct visualization construction/export
without relying on repository fixtures, network data, or notebook widgets.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
from typing import Any, Dict, List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny offline Lux visualization/export smoke test."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print marks, collection size, and short export-token diagnostics.",
    )
    return parser


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Make Matplotlib export safe in headless shells and CI.
    os.environ.setdefault("MPLBACKEND", "Agg")

    import lux  # noqa: F401 - importing Lux patches pandas DataFrame/Series classes.
    import pandas as pd
    from lux.vis.Clause import Clause
    from lux.vis.Vis import Vis
    from lux.vis.VisList import VisList

    df = pd.DataFrame(
        {
            "special.value": [1.0, 2.0, 3.0, 4.0],
            "group.name": ["alpha", "beta", "alpha", "gamma"],
            "normal": [2.0, 4.0, 3.0, 5.0],
            "score": [10.0, 20.0, 15.0, 30.0],
        }
    )

    require(type(df).__module__.startswith("lux."), "DataFrame was not patched by Lux")

    # Clause construction and stringification.
    metric_clause = Clause(attribute="normal", channel="x")
    dotted_clause = Clause(attribute="special.value", channel="y")
    filter_clause = Clause(attribute="group.name", value="alpha")
    require(metric_clause.get_attr() == "normal", "Clause.get_attr returned wrong field")
    require(filter_clause.to_string() == "group.name=alpha", "Clause.to_string failed")

    # Single Vis export, using a dotted column in a scatterplot so standalone
    # Altair output should embed a pd.DataFrame payload. Lux may print the
    # inferred dataframe variable name while generating code, so suppress that
    # incidental output and keep the script's CLI output stable.
    with contextlib.redirect_stdout(io.StringIO()):
        scatter_vis = Vis([metric_clause, dotted_clause], df)
        altair_code = scatter_vis.to_altair(standalone=True)
        mpl_code = Vis([Clause("group.name")], df).to_matplotlib()
        vegaspec_text = Vis([Clause("group.name")], df).to_vegalite(prettyOutput=True)
        vegaspec_dict: Dict[str, Any] = Vis([Clause("group.name")], df).to_vegalite(prettyOutput=False)
        python_code = Vis([Clause("normal"), Clause("score")], df).to_code(language="python")
    require(scatter_vis.mark == "scatter", f"Expected scatter mark, saw {scatter_vis.mark!r}")
    require("alt.Chart(pd.DataFrame" in altair_code, "Standalone Altair code lacks embedded data")
    require("mark_circle" in altair_code, "Altair code lacks scatter mark token")
    require("specialvalue" in altair_code, "Altair code did not sanitize dotted field token")
    require("special.value" in altair_code, "Altair code lost original dotted title token")

    # Recreate the Vis before each export family because Lux renderers may mutate
    # compiled field names for dotted columns.
    require("matplotlib.pyplot" in mpl_code, "Matplotlib code lacks pyplot import")
    require("ax.barh" in mpl_code or "ax.bar" in mpl_code, "Matplotlib code lacks bar token")
    require("group.name" in mpl_code, "Matplotlib code lost dotted column title")

    require("Vega Editor" in vegaspec_text, "Pretty Vega-Lite output lacks editor preamble")
    require('"vislib": "vegalite"' in vegaspec_text, "Pretty Vega-Lite output lacks vislib token")

    require(vegaspec_dict.get("vislib") == "vegalite", "Raw Vega-Lite dict lacks vislib marker")
    require("datasets" in vegaspec_dict, "Raw Vega-Lite dict lacks embedded datasets")
    require(
        any("groupname" in row for rows in vegaspec_dict["datasets"].values() for row in rows),
        "Raw Vega-Lite datasets lack sanitized dotted field",
    )

    require("def create_chart_data" in python_code, "Python code export lacks create_chart_data")
    require("PandasExecutor" in python_code, "Python code export lacks executor token")

    # Collection construction and wildcard enumeration.
    vislist = VisList([Clause("normal"), Clause(attribute="?", data_model="measure")], df)
    require(len(vislist) >= 2, "Wildcard VisList did not enumerate multiple visualizations")
    require(all(hasattr(v, "to_altair") for v in vislist), "VisList members are not Vis objects")
    require("scatter" in list(vislist.get("mark")), "Expected at least one scatter in wildcard VisList")
    vislist.refresh_source(df[df["normal"] >= 3.0])
    require(len(vislist) >= 1, "VisList.refresh_source dropped all visualizations")
    marks_after_refresh = list(vislist.map(lambda v: v.mark))
    require(marks_after_refresh, "VisList.map returned no marks")

    try:
        Vis(["normal", "?"], df)
    except TypeError as exc:
        require("VisList" in str(exc), "Multi-visualization error did not mention VisList")
    else:
        raise AssertionError("Vis accepted wildcard intent that should require VisList")

    if args.verbose:
        print("Lux visualization/export smoke passed")
        print(f"single mark: {scatter_vis.mark}")
        print(f"vislist length after refresh: {len(vislist)}")
        print(f"vislist marks after refresh: {marks_after_refresh}")
        print("tokens: alt.Chart(pd.DataFrame), matplotlib.pyplot, vislib=vegalite")
    else:
        print("Lux visualization/export smoke passed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
