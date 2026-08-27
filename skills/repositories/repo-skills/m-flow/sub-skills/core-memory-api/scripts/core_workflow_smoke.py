#!/usr/bin/env python3
"""Safe smoke checker for M-flow core memory APIs.

Default mode is non-mutating: it imports m_flow, checks expected public exports,
reports whether common LLM credential environment variables are present, and
prints the live workflow plan. Use --run-live to actually call add(),
memorize(), and query(); live mode writes local M-flow data for the selected
dataset and may require LLM/database credentials.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from typing import Any

SAMPLE_TEXT = (
    "Machine learning is a branch of artificial intelligence that enables "
    "systems to learn patterns from data and improve their performance "
    "without being explicitly programmed for each task."
)

EXPECTED_EXPORTS = [
    "add",
    "memorize",
    "ingest",
    "search",
    "query",
    "learn",
    "datasets",
    "delete",
    "update",
    "prune",
    "config",
    "RecallMode",
    "QueryResult",
    "SearchConfig",
    "IngestResult",
    "IngestStatus",
    "ContentType",
    "manual_ingest",
    "manual_add_episode",
    "patch_node",
]

LLM_ENV_VARS = [
    "LLM_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check M-flow core API availability safely. By default this performs "
            "no add/memorize/query calls."
        )
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Actually call add(), memorize(), and query(); writes local M-flow data.",
    )
    parser.add_argument(
        "--allow-missing-llm-env",
        action="store_true",
        help=(
            "Permit --run-live even when common LLM credential environment variables "
            "are absent. Use only for local-LLM or process-configured credentials."
        ),
    )
    parser.add_argument(
        "--dataset-name",
        default="skill_smoke_core",
        help="Dataset name to use in live mode. Default: skill_smoke_core.",
    )
    parser.add_argument(
        "--sample-text",
        default=SAMPLE_TEXT,
        help="Text to add in live mode.",
    )
    parser.add_argument(
        "--query",
        default="What is machine learning?",
        help="Query text for live mode.",
    )
    parser.add_argument(
        "--mode",
        choices=["episodic", "triplet", "chunks", "procedural", "cypher"],
        default="episodic",
        help="query() mode for live mode. Default: episodic.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k query limit for live mode. Default: 5.",
    )
    return parser.parse_args(argv)


def import_m_flow() -> Any:
    try:
        import m_flow  # type: ignore
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"IMPORT_FAILED: {exc!r}", file=sys.stderr)
        raise
    return m_flow


def present_llm_env_vars() -> list[str]:
    return [name for name in LLM_ENV_VARS if os.getenv(name)]


def _safe_config_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(k) for k in value)
    return []


def print_static_checks(m_flow: Any) -> bool:
    version = getattr(m_flow, "__version__", "unknown")
    console_found = shutil.which("mflow") is not None
    print(f"m_flow import: ok (version={version})")
    print(f"mflow console on PATH: {console_found}")

    missing = [name for name in EXPECTED_EXPORTS if not hasattr(m_flow, name)]
    if missing:
        print("missing exports: " + ", ".join(missing))
    else:
        print("expected exports: ok")

    llm_present = present_llm_env_vars()
    if llm_present:
        print("LLM credential env present: " + ", ".join(llm_present))
    else:
        print("LLM credential env present: none of " + ", ".join(LLM_ENV_VARS))

    try:
        cfg = m_flow.config.show("llm", as_dict=True)
        print("LLM config visibility: ok")
        keys = _safe_config_keys(cfg)
        if keys:
            print("LLM config keys: " + ", ".join(keys))
    except Exception as exc:
        print(f"LLM config visibility: unavailable ({exc!r})")

    return not missing


def print_guarded_plan(args: argparse.Namespace) -> None:
    print("\nGuarded live plan:")
    print(f"  dataset_name: {args.dataset_name}")
    print("  1. await m_flow.add(sample_text, dataset_name=dataset_name)")
    print("  2. await m_flow.memorize(datasets=[dataset_name], content_type=ContentType.TEXT)")
    print(f"  3. await m_flow.query({args.query!r}, datasets=dataset_name, mode={args.mode!r}, top_k={args.top_k})")
    print("\nDefault mode stopped before live calls. Add --run-live to execute this plan.")
    print("Live mode may create local relational, graph, vector, file-storage, and cache data.")


async def run_live(args: argparse.Namespace, m_flow: Any) -> dict[str, Any]:
    content_type = getattr(getattr(m_flow, "ContentType", object), "TEXT", None)
    memorize_kwargs: dict[str, Any] = {}
    if content_type is not None:
        memorize_kwargs["content_type"] = content_type

    add_result = await m_flow.add(args.sample_text, dataset_name=args.dataset_name)
    memorize_result = await m_flow.memorize(datasets=[args.dataset_name], **memorize_kwargs)
    query_result = await m_flow.query(
        args.query,
        datasets=args.dataset_name,
        mode=args.mode,
        top_k=args.top_k,
    )

    if hasattr(query_result, "to_dict"):
        query_payload = query_result.to_dict()
    else:
        query_payload = query_result

    return {
        "dataset_name": args.dataset_name,
        "add_result_type": type(add_result).__name__,
        "memorize_result_type": type(memorize_result).__name__,
        "query_result": query_payload,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        m_flow = import_m_flow()
    except Exception:
        return 1

    exports_ok = print_static_checks(m_flow)
    print_guarded_plan(args)

    if not args.run_live:
        return 0 if exports_ok else 1

    if not present_llm_env_vars() and not args.allow_missing_llm_env:
        print(
            "\nRefusing live run because no common LLM credential environment variable is present. "
            "Set LLM_API_KEY or pass --allow-missing-llm-env if credentials are provided another way.",
            file=sys.stderr,
        )
        return 2

    print("\nRUN_LIVE enabled: executing guarded workflow now.")
    try:
        payload = asyncio.run(run_live(args, m_flow))
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"LIVE_WORKFLOW_FAILED: {exc!r}", file=sys.stderr)
        return 1

    print("LIVE_WORKFLOW_COMPLETED")
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
