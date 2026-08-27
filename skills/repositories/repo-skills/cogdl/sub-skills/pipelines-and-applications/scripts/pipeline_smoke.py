#!/usr/bin/env python3
"""Inspect CogDL pipeline apps and optionally run a tiny no-download embedding smoke."""

from __future__ import annotations

import argparse
import json
from pprint import pprint


EMBEDDING_MODELS = [
    "prone",
    "netmf",
    "netsmf",
    "deepwalk",
    "line",
    "node2vec",
    "hope",
    "sdne",
    "grarep",
    "dngr",
    "spectral",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-apps", action="store_true", help="show the available CogDL pipeline apps")
    parser.add_argument("--run", action="store_true", help="run the tiny generate-emb smoke")
    parser.add_argument("--model", choices=EMBEDDING_MODELS, default="prone")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a pretty dict")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    from cogdl import pipeline
    from cogdl.pipelines import SUPPORTED_APPS

    payload = {"supported_apps": sorted(SUPPORTED_APPS)}
    if args.list_apps:
        payload["app_count"] = len(SUPPORTED_APPS)

    if args.run:
        import numpy as np

        generator = pipeline("generate-emb", model=args.model)
        edge_index = np.array(
            [[0, 1], [0, 2], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]],
            dtype=np.int64,
        )
        emb = generator(edge_index)
        payload["smoke"] = {
            "model": args.model,
            "edge_count": int(edge_index.shape[0]),
            "embedding_shape": list(emb.shape),
        }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        pprint(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
