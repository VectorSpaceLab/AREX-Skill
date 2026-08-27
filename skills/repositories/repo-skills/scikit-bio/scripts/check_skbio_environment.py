#!/usr/bin/env python3
"""Check public scikit-bio imports and representative API availability."""

from __future__ import annotations

import argparse
import inspect
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import scikit-bio, inspect representative public APIs, run tiny "
            "deterministic smoke checks, and print JSON."
        )
    )
    parser.add_argument("--indent", type=int, default=None, help="Pretty-print JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        import skbio
        from skbio import DNA, DistanceMatrix, TreeNode
        from skbio.diversity import alpha_diversity, beta_diversity
        from skbio.stats.ordination import pcoa
    except ImportError as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "import-error",
                    "message": str(error),
                    "hint": "Install scikit-bio and runtime scientific dependencies before using this skill.",
                },
                sort_keys=True,
                indent=args.indent,
            ),
            file=sys.stderr,
        )
        return 1

    counts = [[1, 0, 2], [0, 3, 1], [2, 1, 0]]
    ids = ["s1", "s2", "s3"]
    alpha = alpha_diversity("sobs", counts, ids)
    beta = beta_diversity("braycurtis", counts, ids)
    ordination = pcoa(DistanceMatrix([[0, 0.2, 0.4], [0.2, 0, 0.3], [0.4, 0.3, 0]], ids))
    tree = TreeNode.read(["((a:1,b:2)c:3,d:4)root;"])

    summary = {
        "ok": True,
        "version": skbio.__version__,
        "api_signatures": {
            "DNA": str(inspect.signature(DNA)),
            "TreeNode": str(inspect.signature(TreeNode)),
            "DistanceMatrix": str(inspect.signature(DistanceMatrix)),
            "alpha_diversity": str(inspect.signature(alpha_diversity)),
            "beta_diversity": str(inspect.signature(beta_diversity)),
            "pcoa": str(inspect.signature(pcoa)),
        },
        "smoke": {
            "dna_gc_content": DNA("ACGT").gc_content(),
            "alpha_sobs": alpha.to_dict(),
            "beta_ids": list(beta.ids),
            "tree_tip_count": tree.count(tips=True),
            "ordination_method": ordination.short_method_name,
            "ordination_sample_ids": list(ordination.samples.index),
            "ordination_first_proportion": float(ordination.proportion_explained.iloc[0]),
        },
    }
    print(json.dumps(summary, sort_keys=True, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
