#!/usr/bin/env python3
"""Check a Sweetviz installation without depending on the source checkout.

Default checks import Sweetviz, inspect key public signatures, and verify that
package assets are present. With --render-smoke, the script also creates a tiny
HTML report with show_html(open_browser=False).
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any


REQUIRED_SIGNATURES = [
    "analyze",
    "compare",
    "compare_intra",
    "FeatureConfig",
    "DataframeReport",
]
ASSET_PROBES = [
    "sweetviz.templates",
    "sweetviz.fonts",
    "sweetviz.mpl_styles",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Sweetviz import, public signatures, packaged assets, and optional tiny HTML rendering."
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable lines.")
    parser.add_argument(
        "--render-smoke",
        action="store_true",
        help="Also generate a tiny Sweetviz HTML report without opening a browser.",
    )
    parser.add_argument(
        "--output",
        default="sweetviz_install_smoke.html",
        help="Output path for --render-smoke. Default: %(default)s.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing --output file.")
    return parser


def import_sweetviz(report: dict[str, Any]):
    try:
        import sweetviz as sv  # type: ignore
    except Exception as exc:
        report["ok"] = False
        report["errors"].append(f"could not import sweetviz: {exc}")
        return None
    report["sweetviz_version"] = getattr(sv, "__version__", None)
    report["module_file"] = getattr(sv, "__file__", None)
    return sv


def inspect_signatures(sv, report: dict[str, Any]) -> None:  # noqa: ANN001 - imported module
    signatures: dict[str, str] = {}
    for name in REQUIRED_SIGNATURES:
        obj = getattr(sv, name, None)
        if obj is None:
            report["ok"] = False
            report["errors"].append(f"missing public attribute: sweetviz.{name}")
            continue
        target = obj.__init__ if name in {"FeatureConfig", "DataframeReport"} else obj
        try:
            signatures[name] = str(inspect.signature(target))
        except Exception as exc:
            report["warnings"].append(f"could not inspect signature for {name}: {exc}")
    report["signatures"] = signatures

    analyze_sig = signatures.get("analyze", "")
    compare_sig = signatures.get("compare", "")
    if "verbosity" in analyze_sig or "verbosity" in compare_sig:
        report["warnings"].append("public analyze/compare signatures include verbosity in this install; refresh guidance")
    else:
        report["notes"].append("public analyze/compare do not accept verbosity; use config defaults or DataframeReport")


def probe_assets(report: dict[str, Any]) -> None:
    assets: dict[str, bool] = {}
    for module_name in ASSET_PROBES:
        try:
            importlib.import_module(module_name)
            assets[module_name] = True
        except Exception as exc:
            assets[module_name] = False
            report["ok"] = False
            report["errors"].append(f"could not import asset package {module_name}: {exc}")
    report["asset_packages"] = assets

    try:
        import importlib.resources as resources

        import sweetviz  # type: ignore

        candidates = [
            resources.files(sweetviz).joinpath("sweetviz_defaults.ini"),
            resources.files(sweetviz).joinpath("templates", "dataframe_page.html"),
            resources.files(sweetviz).joinpath("templates", "sweetviz.css"),
            resources.files(sweetviz).joinpath("mpl_styles", "graph_base.mplstyle"),
        ]
        asset_files = {str(path.name): path.is_file() for path in candidates}
        report["asset_files"] = asset_files
        for name, present in asset_files.items():
            if not present:
                report["ok"] = False
                report["errors"].append(f"missing package asset file: {name}")
    except Exception as exc:
        report["ok"] = False
        report["errors"].append(f"could not inspect package asset files: {exc}")


def disable_optional_comet() -> None:
    try:
        import sweetviz.comet_ml_logger as comet_ml_logger  # type: ignore

        comet_ml_logger.comet_installed = False
    except Exception:
        pass


def render_smoke(sv, output: Path, overwrite: bool, report: dict[str, Any]) -> None:  # noqa: ANN001
    if output.exists() and not overwrite:
        report["ok"] = False
        report["errors"].append(f"output already exists; pass --overwrite to replace it: {output}")
        return
    if output.parent and not output.parent.exists():
        report["ok"] = False
        report["errors"].append(f"output parent directory does not exist: {output.parent}")
        return

    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import pandas as pd

        disable_optional_comet()
        sv.config_parser["General"]["default_verbosity"] = "off"
        df = pd.DataFrame(
            {
                "score": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 10.1, 11.2],
                "target": [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
                "segment": ["A", "B", "A", "B", "A", "B", "C", "C", "A", "B", "C"],
            }
        )
        feat_cfg = sv.FeatureConfig(force_num=["score"])
        sweetviz_report = sv.analyze([df, "Install smoke"], target_feat="target", feat_cfg=feat_cfg, pairwise_analysis="off")
        sweetviz_report.show_html(str(output), open_browser=False, layout="vertical", scale=0.8)
        size = output.stat().st_size if output.exists() else 0
        if size <= 1000:
            report["ok"] = False
            report["errors"].append(f"rendered HTML is unexpectedly small: {output} ({size} bytes)")
        else:
            report["render_smoke"] = {"output": str(output), "size_bytes": size}
    except Exception as exc:
        report["ok"] = False
        report["errors"].append(f"render smoke failed: {exc}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {"ok": True, "errors": [], "warnings": [], "notes": []}

    sv = import_sweetviz(report)
    if sv is not None:
        inspect_signatures(sv, report)
        probe_assets(report)
        if args.render_smoke:
            render_smoke(sv, Path(args.output), args.overwrite, report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "FAILED"
        print(f"Sweetviz install check: {status}")
        if report.get("sweetviz_version"):
            print(f"version: {report['sweetviz_version']}")
        for note in report["notes"]:
            print(f"note: {note}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        for error in report["errors"]:
            print(f"error: {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
