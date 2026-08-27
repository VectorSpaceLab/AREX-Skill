#!/usr/bin/env python3
"""LitServe import smoke for the generated repo skill.

Run this from an environment that already has the LitServe package installed.
It prints the package version and a few core signatures without opening the
source repository.
"""

from __future__ import annotations

import argparse
import inspect
import json

import litserve as ls
from litserve import LitAPI, LitServer, OpenAISpec, OpenAIEmbeddingSpec


def build_report() -> dict[str, str]:
    return {
        "version": ls.__version__,
        "module": ls.__file__,
        "litapi_init": str(inspect.signature(LitAPI.__init__)),
        "litserver_run": str(inspect.signature(LitServer.run)),
        "openai_spec": str(inspect.signature(OpenAISpec)),
        "openai_embedding_spec": str(inspect.signature(OpenAIEmbeddingSpec)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a LitServe import smoke report.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"litserve {report['version']}")
    print(f"module: {report['module']}")
    print(f"LitAPI.__init__: {report['litapi_init']}")
    print(f"LitServer.run: {report['litserver_run']}")
    print(f"OpenAISpec: {report['openai_spec']}")
    print(f"OpenAIEmbeddingSpec: {report['openai_embedding_spec']}")


if __name__ == "__main__":
    main()
