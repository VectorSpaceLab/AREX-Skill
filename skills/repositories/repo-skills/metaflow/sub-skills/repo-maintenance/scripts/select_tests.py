#!/usr/bin/env python3
"""Suggest focused Metaflow repository tests for changed paths.

Example:
  python select_tests.py metaflow/runner/metaflow_runner.py metaflow/graph.py
"""
import argparse
import json

RULES = [
    ("metaflow/runner/", ["Run the focused runner/client unit tests nearest the change.", "Run the core harness with dev-local context and a small graph/test selection such as linear plus BasicArtifactTest."]),
    ("metaflow/graph.py", ["Run the graph structure unit tests nearest the change.", "Run the core harness with dev-local context."]),
    ("metaflow/flowspec.py", ["Run the graph structure unit tests nearest the change.", "Run the core harness with dev-local context."]),
    ("metaflow/plugins/cards/", ["Run the card creator unit tests nearest the change.", "Run the core harness card decorator case with dev-local context."]),
    ("metaflow/plugins/aws/batch/", ["Run compute resource attribute unit tests nearest the change.", "Run relevant UX/deployment compile tests if dependencies are installed."]),
    ("metaflow/plugins/kubernetes/", ["Run Kubernetes unit tests nearest the change."]),
    ("metaflow/plugins/datatools/s3/", ["Run the S3/data pytest suite only after S3 or MinIO service configuration is available."]),
    ("metaflow/plugins/pypi/", ["Run focused conda/pypi parser and decorator tests.", "Run focused pypi parser and uv bootstrap unit tests."]),
    ("metaflow/user_configs/", ["Run focused UX config tests if UX dependencies are installed.", "Run focused unit config tests."]),
]


def commands_for(path):
    out = []
    for prefix, commands in RULES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            out.extend(commands)
    if not out and path.startswith("test/"):
        out.append("Run the changed test file directly with pytest or the documented harness from the repository root.")
    if not out:
        out.append("Start with the closest unit test; if behavior crosses flow runtime, add the dev-local core harness.")
    return out


def main():
    parser = argparse.ArgumentParser(description="Suggest focused Metaflow tests for changed paths.")
    parser.add_argument("paths", nargs="*", help="Changed repository-relative paths.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = {path: commands_for(path) for path in args.paths}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for path, commands in result.items():
            print(path)
            for command in commands:
                print(f"  - {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
