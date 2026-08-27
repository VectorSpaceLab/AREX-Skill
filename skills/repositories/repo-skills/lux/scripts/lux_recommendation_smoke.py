#!/usr/bin/env python3
"""Run an offline integrated Lux recommendation/export smoke check.

The helper verifies the core routes of this skill with in-memory data only:
Pandas monkeypatching, semantic data-type metadata, dataframe intent,
recommendations, and `Vis` export. It is safe for arbitrary current working
directories and does not need repository fixtures or network access.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from typing import Any, Dict, List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny offline Lux recommendation/export smoke check.")
    parser.add_argument("--json", action="store_true", help="Print detailed JSON instead of a short success line.")
    return parser


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    os.environ.setdefault("MPLBACKEND", "Agg")

    import lux
    import pandas as pd
    from lux.vis.Vis import Vis
    from lux.vis.Clause import Clause

    lux.config.default_display = "pandas"
    lux.config.plotting_backend = "vegalite"
    lux.config.topk = 5

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05", "2020-01-06"]),
            "region": ["West", "West", "East", "East", "North", "South"],
            "sales": [10, 12, 8, 15, 7, 9],
            "profit": [2, 3, 1, 4, 1, 2],
        }
    )
    require(type(df).__module__.startswith("lux."), "DataFrame was not patched by Lux")

    df.maintain_metadata()
    require(df.data_type["date"] == "temporal", "date should be temporal")
    require(df.data_type["sales"] == "quantitative", "sales should be quantitative")
    require(df.data_type["region"] == "nominal", "region should be nominal")

    default_keys = list(df.recommendation.keys())
    require(default_keys, "default recommendations were not generated")

    df.intent = ["sales", "profit"]
    require(len(df.current_vis) == 1, "two-measure intent should compile to one current Vis")
    intent_keys = list(df.recommendation.keys())
    require("Generalize" in intent_keys, "intent recommendations should include Generalize")

    vis = Vis([Clause("region"), Clause("sales", aggregation="mean")], df)
    with contextlib.redirect_stdout(io.StringIO()):
        altair_code = vis.to_altair()
        vega_spec = vis.to_vegalite(prettyOutput=False)
    require("alt.Chart" in altair_code, "Altair export did not contain alt.Chart")
    require(vega_spec.get("vislib") == "vegalite", "Vega-Lite export missing vislib marker")

    result: Dict[str, Any] = {
        "ok": True,
        "lux_version": getattr(lux, "__version__", None),
        "dataframe_class": f"{type(df).__module__}.{type(df).__name__}",
        "data_types": dict(df.data_type),
        "default_recommendation_keys": default_keys,
        "intent_recommendation_keys": intent_keys,
        "current_vis_mark": df.current_vis[0].mark,
        "manual_vis_mark": vis.mark,
        "altair_export_contains_alt_chart": "alt.Chart" in altair_code,
        "vegalite_export_keys": sorted(vega_spec.keys()),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Lux integrated recommendation smoke passed")
        print(f"- default recommendations: {default_keys}")
        print(f"- intent recommendations: {intent_keys}")
        print(f"- manual Vis mark: {vis.mark}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
