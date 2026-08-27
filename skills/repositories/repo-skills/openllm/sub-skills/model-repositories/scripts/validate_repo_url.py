#!/usr/bin/env python3
"""Validate and normalize an OpenLLM model repository URL without cloning it.

Examples:
  python validate_repo_url.py https://github.com/bentoml/openllm-models@main
  python validate_repo_url.py git@github.com:bentoml/openllm-models.git --repo-name nightly

This helper is read-only and only parses the URL form that OpenLLM accepts.
"""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_url", help="Public Git repository URL accepted by OpenLLM.")
    parser.add_argument("--repo-name", help="Optional alias to assign in OpenLLM's config.")
    parser.add_argument("--json", action="store_true", help="Render the result as JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from openllm.repo import parse_repo_url
    except Exception as exc:  # pragma: no cover - exercised manually
        print(f"OpenLLM import failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        info = parse_repo_url(args.repo_url, args.repo_name)
    except Exception as exc:
        print(f"invalid repo url: {exc}", file=sys.stderr)
        return 2

    payload = {
        "name": info.name,
        "url": info.url,
        "server": info.server,
        "owner": info.owner,
        "repo": info.repo,
        "branch": info.branch,
        "path": str(info.path),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
