#!/usr/bin/env python3
"""Safe parser and registry smoke for CogDL experiment/CLI workflows.

This script does not train, download datasets, or write checkpoints. It only
imports the public parser path, inspects supported registries, and resolves the
requested training arguments.
"""

from __future__ import annotations

import argparse
from pprint import pprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", "-dt", nargs="+", required=True)
    parser.add_argument("--model", "-m", nargs="+", required=True)
    parser.add_argument("--dw", "-t", default=None)
    parser.add_argument("--mw", default=None)
    parser.add_argument("--show-registries", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    from cogdl import options
    from cogdl.datasets import SUPPORTED_DATASETS
    from cogdl.models import SUPPORTED_MODELS
    from cogdl.wrappers.default_match import get_wrappers_name

    parsed = options.get_default_args(dataset=args.dataset, model=args.model, dw=args.dw, mw=args.mw)

    print("Resolved dataset/model/wrapper preview:")
    pprint({"dataset": parsed.dataset, "model": parsed.model, "mw": parsed.mw, "dw": parsed.dw})

    if args.show_registries:
        print("Supported dataset count:", len(SUPPORTED_DATASETS))
        print("Supported model count:", len(SUPPORTED_MODELS))
        print("Default wrapper pair:", get_wrappers_name(args.model[0]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
