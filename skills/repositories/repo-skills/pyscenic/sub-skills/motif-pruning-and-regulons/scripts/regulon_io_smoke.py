#!/usr/bin/env python3
"""Safe pySCENIC motif/regulon I/O smoke test.

This script creates a tiny in-memory enriched motif table, exports it through
pySCENIC's motif/regulon serializers, and reloads the formats that pySCENIC
supports as signatures. It does not open ranking databases, download resources,
train models, or require a specific current working directory.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate pySCENIC motif/regulon I/O helpers with a tiny local "
            "fixture; no ranking databases or network access are used."
        )
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Optional directory for generated fixtures. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated files when using the default temporary directory.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only errors and the final JSON summary.",
    )
    return parser.parse_args()


def import_runtime():
    try:
        import pandas as pd
        from pyscenic.cli.utils import load_signatures, save_enriched_motifs
        from pyscenic.prune import df2regulons
        from pyscenic.transform import (
            COLUMN_NAME_AUC,
            COLUMN_NAME_CONTEXT,
            COLUMN_NAME_NES,
            COLUMN_NAME_RANK_AT_MAX,
            COLUMN_NAME_TARGET_GENES,
        )
        from pyscenic.utils import (
            ACTIVATING_MODULE,
            COLUMN_NAME_ANNOTATION,
            COLUMN_NAME_MOTIF_ID,
            COLUMN_NAME_MOTIF_SIMILARITY_QVALUE,
            COLUMN_NAME_ORTHOLOGOUS_IDENTITY,
            COLUMN_NAME_TF,
            load_motifs,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"Missing import {exc.name!r}. Install pySCENIC and its runtime dependencies "
            "in the Python environment used to run this script."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Unable to import pySCENIC motif/regulon I/O helpers: {exc}"
        ) from exc

    return {
        "pd": pd,
        "load_signatures": load_signatures,
        "save_enriched_motifs": save_enriched_motifs,
        "df2regulons": df2regulons,
        "load_motifs": load_motifs,
        "ACTIVATING_MODULE": ACTIVATING_MODULE,
        "COLUMN_NAME_AUC": COLUMN_NAME_AUC,
        "COLUMN_NAME_CONTEXT": COLUMN_NAME_CONTEXT,
        "COLUMN_NAME_NES": COLUMN_NAME_NES,
        "COLUMN_NAME_RANK_AT_MAX": COLUMN_NAME_RANK_AT_MAX,
        "COLUMN_NAME_TARGET_GENES": COLUMN_NAME_TARGET_GENES,
        "COLUMN_NAME_ANNOTATION": COLUMN_NAME_ANNOTATION,
        "COLUMN_NAME_MOTIF_ID": COLUMN_NAME_MOTIF_ID,
        "COLUMN_NAME_MOTIF_SIMILARITY_QVALUE": COLUMN_NAME_MOTIF_SIMILARITY_QVALUE,
        "COLUMN_NAME_ORTHOLOGOUS_IDENTITY": COLUMN_NAME_ORTHOLOGOUS_IDENTITY,
        "COLUMN_NAME_TF": COLUMN_NAME_TF,
    }


def build_fixture(runtime):
    pd = runtime["pd"]
    index = pd.MultiIndex.from_tuples(
        [("TF_TEST", "motif_test_1")],
        names=(runtime["COLUMN_NAME_TF"], runtime["COLUMN_NAME_MOTIF_ID"]),
    )
    columns = pd.MultiIndex.from_tuples(
        [
            ("Enrichment", runtime["COLUMN_NAME_AUC"]),
            ("Enrichment", runtime["COLUMN_NAME_NES"]),
            ("Enrichment", runtime["COLUMN_NAME_MOTIF_SIMILARITY_QVALUE"]),
            ("Enrichment", runtime["COLUMN_NAME_ORTHOLOGOUS_IDENTITY"]),
            ("Enrichment", runtime["COLUMN_NAME_ANNOTATION"]),
            ("Enrichment", runtime["COLUMN_NAME_CONTEXT"]),
            ("Enrichment", runtime["COLUMN_NAME_TARGET_GENES"]),
            ("Enrichment", runtime["COLUMN_NAME_RANK_AT_MAX"]),
        ]
    )
    row = [
        0.25,
        4.2,
        0.0,
        math.nan,
        "direct motif annotation for TF_TEST",
        frozenset({runtime["ACTIVATING_MODULE"], "fixture_database"}),
        [("GeneA", 1.0), ("GeneB", 0.5), ("TF_TEST", 0.75)],
        2,
    ]
    return pd.DataFrame([row], index=index, columns=columns)


def validate_regulons(regulons, source: str) -> dict:
    if len(regulons) != 1:
        raise AssertionError(f"{source}: expected 1 regulon, found {len(regulons)}")
    regulon = regulons[0]
    expected_genes = {"GeneA", "GeneB", "TF_TEST"}
    observed_genes = set(regulon.gene2weight.keys())
    if not expected_genes.issubset(observed_genes):
        raise AssertionError(
            f"{source}: expected genes {sorted(expected_genes)}, found {sorted(observed_genes)}"
        )
    if not regulon.name.startswith("TF_TEST"):
        raise AssertionError(f"{source}: unexpected regulon name {regulon.name!r}")
    return {"name": regulon.name, "genes": sorted(observed_genes)}


def run_smoke(work_dir: Path, quiet: bool) -> dict:
    runtime = import_runtime()
    work_dir.mkdir(parents=True, exist_ok=True)

    motif_df = build_fixture(runtime)
    direct_regulons = runtime["df2regulons"](motif_df)
    direct_summary = validate_regulons(direct_regulons, "df2regulons")

    outputs = {}
    format_warnings = {}
    for suffix in ("csv", "tsv", "gmt", "yaml", "dat", "json"):
        path = work_dir / f"motif_fixture.{suffix}"
        try:
            runtime["save_enriched_motifs"](motif_df, str(path))
        except Exception as exc:
            format_warnings[suffix] = f"save failed: {exc}"
            if not quiet:
                print(f"warning: could not write {path}: {exc}")
            continue
        outputs[suffix] = {"path": str(path), "bytes": path.stat().st_size}
        if not quiet:
            print(f"wrote {path} ({outputs[suffix]['bytes']} bytes)")

    for required_suffix in ("csv", "tsv", "gmt", "yaml", "json"):
        if required_suffix not in outputs:
            raise AssertionError(
                f"Required fixture .{required_suffix} was not written: "
                f"{format_warnings.get(required_suffix, 'unknown error')}"
            )

    csv_motifs = runtime["load_motifs"](outputs["csv"]["path"])
    tsv_motifs = runtime["load_motifs"](outputs["tsv"]["path"], sep="\t")
    if csv_motifs.shape != motif_df.shape:
        raise AssertionError(f"CSV motif reload shape mismatch: {csv_motifs.shape}")
    if tsv_motifs.shape != motif_df.shape:
        raise AssertionError(f"TSV motif reload shape mismatch: {tsv_motifs.shape}")

    reloadable_summaries = {}
    for suffix in ("csv", "tsv", "gmt", "yaml", "dat"):
        if suffix not in outputs:
            continue
        try:
            signatures = runtime["load_signatures"](outputs[suffix]["path"])
            reloadable_summaries[suffix] = validate_regulons(
                signatures, f"load_signatures .{suffix}"
            )
        except Exception as exc:
            format_warnings[suffix] = f"load failed: {exc}"
            if suffix in {"csv", "tsv", "gmt", "yaml"}:
                raise
            if not quiet:
                print(f"warning: could not reload .{suffix}: {exc}")

    for required_suffix in ("csv", "tsv", "gmt", "yaml"):
        if required_suffix not in reloadable_summaries:
            raise AssertionError(
                f"Required reloadable format .{required_suffix} was not validated"
            )

    with open(outputs["json"]["path"], "r", encoding="utf-8") as handle:
        json_payload = json.load(handle)
    if not any(name.startswith("TF_TEST") for name in json_payload):
        raise AssertionError("JSON export does not contain the expected regulon name")

    return {
        "ok": True,
        "work_dir": str(work_dir),
        "direct_regulon": direct_summary,
        "outputs": outputs,
        "reloadable_formats": sorted(reloadable_summaries),
        "format_warnings": format_warnings,
        "json_regulons": sorted(json_payload),
    }


def main() -> int:
    args = parse_args()
    try:
        if args.work_dir is not None:
            summary = run_smoke(args.work_dir.resolve(), args.quiet)
        elif args.keep:
            work_dir = Path(tempfile.mkdtemp(prefix="pyscenic-regulon-io-"))
            summary = run_smoke(work_dir, args.quiet)
        else:
            with tempfile.TemporaryDirectory(prefix="pyscenic-regulon-io-") as tmpdir:
                summary = run_smoke(Path(tmpdir), args.quiet)
                summary["work_dir"] = "temporary directory removed"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: pySCENIC regulon I/O smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
