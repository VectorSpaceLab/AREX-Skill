#!/usr/bin/env python3
"""Explain LM Evaluation Harness request-cache paths and maintenance actions.

This helper is advisory only. It does not import lm_eval, create directories,
rewrite cache files, or delete anything.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

HASH_INPUT = "EleutherAI-lm-evaluation-harness"
HASH_PREFIX = hashlib.sha256(HASH_INPUT.encode("utf-8")).hexdigest()
FILE_SUFFIX = f".{HASH_PREFIX}.pickle"
DEFAULT_RELATIVE_CACHE = "lm_eval/caching/.cache"


def cache_flags(cache_requests: str | None) -> dict[str, bool]:
    if cache_requests is None:
        return {
            "cache_requests": False,
            "rewrite_requests_cache": False,
            "delete_requests_cache": False,
        }
    if cache_requests not in {"true", "refresh", "delete"}:
        raise ValueError("cache_requests must be one of: true, refresh, delete")
    return {
        "cache_requests": cache_requests in {"true", "refresh"},
        "rewrite_requests_cache": cache_requests == "refresh",
        "delete_requests_cache": cache_requests == "delete",
    }


def explain_action(cache_requests: str | None) -> str:
    if cache_requests is None:
        return "No request-cache action requested; evaluations will build requests normally unless config sets caching elsewhere."
    if cache_requests == "true":
        return "Read existing request-cache entries when present and write missing entries."
    if cache_requests == "refresh":
        return "Rewrite request-cache entries; use after task, prompt, tokenizer, model identity, rank/world-size, or chat-template changes."
    if cache_requests == "delete":
        return "Delete matching request-cache entries; use only when stale cache removal is intentional."
    raise AssertionError("unreachable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Advisory request-cache path helper for LM Evaluation Harness.")
    parser.add_argument("--path", help="Explicit cache path to describe. If omitted, LM_HARNESS_CACHE_PATH or the default relative path is used.")
    parser.add_argument("--cache-requests", choices=["true", "refresh", "delete"], help="Explain CLI cache request behavior.")
    parser.add_argument("--repo-root", default=".", help="Repository root used only to display the default relative cache path.")
    args = parser.parse_args(argv)

    env_path = os.getenv("LM_HARNESS_CACHE_PATH")
    if args.path:
        source = "--path argument"
        effective = Path(args.path)
    elif env_path:
        source = "LM_HARNESS_CACHE_PATH environment variable"
        effective = Path(env_path)
    else:
        source = "default relative package cache path"
        effective = Path(args.repo_root) / DEFAULT_RELATIVE_CACHE

    flags = cache_flags(args.cache_requests)

    print("LM Evaluation Harness request-cache advisor")
    print(f"Effective path source: {source}")
    print(f"Effective path: {effective}")
    print(f"Cache file suffix: {FILE_SUFFIX}")
    print("Evaluator flags:")
    for key, value in flags.items():
        print(f"  {key}: {value}")
    print(f"Action: {explain_action(args.cache_requests)}")
    print("Safety: advisory only; no files were created, rewritten, or deleted.")

    if args.cache_requests == "refresh":
        print("Tip: isolate branch or prompt experiments with a dedicated LM_HARNESS_CACHE_PATH.")
    elif args.cache_requests == "delete":
        print("Tip: confirm the path before running a real delete operation in lm-eval.")
    elif args.cache_requests == "true":
        print("Tip: use refresh instead of true after changing request construction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
