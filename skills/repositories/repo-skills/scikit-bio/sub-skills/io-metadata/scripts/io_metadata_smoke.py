#!/usr/bin/env python3
"""Smoke-check public scikit-bio IO and metadata APIs."""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO


class NonClosingStringIO(StringIO):
    """StringIO variant for APIs that close file-like outputs."""

    def close(self) -> None:
        self.seek(0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read/write a Newick tree, stream FASTA records, construct "
            "SampleMetadata, and print a compact JSON summary."
        )
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Pretty-print JSON with this indentation level.",
    )
    return parser


def run_smoke() -> dict[str, object]:
    try:
        import pandas as pd
        from skbio import DNA, TreeNode, read, write
        from skbio.io import FileFormatError, UnrecognizedFormatError, sniff
        from skbio.metadata import IntervalMetadata, SampleMetadata
    except ImportError as error:
        raise RuntimeError(
            "Unable to import public scikit-bio IO/metadata APIs. Install "
            "scikit-bio with pandas and its runtime dependencies before running this smoke check."
        ) from error

    try:
        newick_handle = StringIO("((a:1,b:2)c:3,d:4)root;")
        sniffed_format, sniffed_kwargs = sniff(newick_handle, into=TreeNode)
        newick_handle.seek(0)
        tree = read(newick_handle, format="newick", into=TreeNode)
        tree_out = StringIO()
        write(tree, format="newick", into=tree_out)

        oo_tree = TreeNode.read(StringIO("(x,y)root;"), format="newick")
        oo_out = StringIO()
        oo_tree.write(oo_out, format="newick")

        fasta_text = ">seq1 description\nACGTACGT\n"
        single_record = read(StringIO(fasta_text), format="fasta", into=DNA)
        records = list(read(StringIO(fasta_text), format="fasta", constructor=DNA))
        if not records:
            raise ValueError("FASTA smoke input yielded no records")

        dataframe = pd.DataFrame(
            {
                "body_site": ["gut", "skin"],
                "age": [34.0, 29.0],
                "collection_note": ["missing", "not collected"],
            },
            index=pd.Index(["sample-1", "sample-2"], name="id"),
        )
        metadata = SampleMetadata(
            dataframe,
            column_missing_schemes={"collection_note": "INSDC:missing"},
        )
        metadata_frame = metadata.to_dataframe()
        metadata_out = NonClosingStringIO()
        metadata.write(metadata_out, format="sample_metadata")

        intervals = IntervalMetadata(8)
        feature = intervals.add(
            bounds=[(1, 4)],
            metadata={"type": "gene", "ID": "gene-1"},
        )
    except (FileFormatError, UnrecognizedFormatError, TypeError, ValueError) as error:
        raise RuntimeError(f"scikit-bio IO/metadata smoke validation failed: {error}") from error

    first_record = records[0]
    return {
        "newick": {
            "sniffed_format": sniffed_format,
            "sniffed_kwargs": sniffed_kwargs,
            "tip_count": tree.count(tips=True),
            "tips": sorted(tip.name for tip in tree.tips()),
            "roundtrip_prefix": tree_out.getvalue().strip()[:24],
            "object_api_tip_count": oo_tree.count(tips=True),
        },
        "fasta": {
            "record_count": len(records),
            "first_id": first_record.metadata.get("id"),
            "first_length": len(first_record),
            "first_type": type(first_record).__name__,
            "single_id": single_record.metadata.get("id"),
            "single_length": len(single_record),
        },
        "metadata": {
            "id_header": metadata.id_header,
            "ids": list(metadata.ids),
            "columns": sorted(metadata.columns),
            "column_types": {name: props.type for name, props in metadata.columns.items()},
            "missing_schemes": {
                name: props.missing_scheme for name, props in metadata.columns.items()
            },
            "dataframe_shape": list(metadata_frame.shape),
            "serialized_header": metadata_out.getvalue().splitlines()[0],
        },
        "interval_metadata": {
            "upper_bound": intervals.upper_bound,
            "interval_count": len(list(intervals.query())),
            "feature_bounds": feature.bounds,
            "feature_type": feature.metadata.get("type"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_smoke()
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
