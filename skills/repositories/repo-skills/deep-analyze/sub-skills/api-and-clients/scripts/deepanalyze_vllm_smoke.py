#!/usr/bin/env python3
"""Smoke test the DeepAnalyzeVLLM local loop against a mock chat endpoint."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def _locate_repo_root() -> Path:
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "deepanalyze.py").exists():
            return parent
    raise RuntimeError("Could not locate deepanalyze.py from this script")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise DeepAnalyzeVLLM against a mock vLLM endpoint.",
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000/v1/chat/completions",
        help="Chat completions endpoint for the mock or real vLLM server.",
    )
    parser.add_argument("--model-name", default="DeepAnalyze-8B", help="Model name passed into DeepAnalyzeVLLM.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Workspace directory to use. If omitted, a temporary workspace is created.",
    )
    parser.add_argument(
        "--prompt",
        default="Create a tiny workspace artifact and finish with a short answer.",
        help="Prompt sent into DeepAnalyzeVLLM.generate().",
    )
    parser.add_argument("--temperature", type=float, default=0.5, help="Sampling temperature for generate().")
    parser.add_argument("--max-tokens", type=int, default=32768, help="Maximum tokens for generate().")
    parser.add_argument("--top-p", type=float, default=None, help="Optional top-p value for generate().")
    parser.add_argument("--top-k", type=int, default=None, help="Optional top-k value for generate().")
    parser.add_argument("--max-rounds", type=int, default=30, help="Maximum reasoning rounds.")
    parser.add_argument(
        "--expect-file",
        default="smoke_artifact.txt",
        help="File that the mock code is expected to write inside the workspace.",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep the auto-created workspace instead of deleting it on exit.",
    )
    return parser


def _prepare_workspace(workspace_arg: Optional[str]) -> Tuple[Path, Optional[tempfile.TemporaryDirectory[str]]]:
    if workspace_arg:
        workspace = Path(workspace_arg).expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace, None
    temp_dir = tempfile.TemporaryDirectory(prefix="deepanalyze-vllm-smoke-")
    return Path(temp_dir.name), temp_dir


def main() -> int:
    args = build_parser().parse_args()
    repo_root = _locate_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        from deepanalyze import DeepAnalyzeVLLM
    except Exception as exc:  # pragma: no cover - import failure is a user-facing smoke issue
        raise SystemExit(f"Unable to import DeepAnalyzeVLLM: {exc}") from exc

    workspace, temp_dir = _prepare_workspace(args.workspace)
    try:
        runner = DeepAnalyzeVLLM(
            model_name=args.model_name,
            api_url=args.api_url,
            max_rounds=args.max_rounds,
        )

        local_exec = runner.execute_code("print(2 + 2)")
        print("Local execute_code output:")
        print(local_exec.rstrip())
        if local_exec.strip() != "4":
            raise SystemExit("execute_code smoke did not return 4")

        result = runner.generate(
            prompt=args.prompt,
            workspace=str(workspace),
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            top_k=args.top_k,
        )
        reasoning = result.get("reasoning", "")
        print("\nDeepAnalyzeVLLM reasoning preview:")
        print(reasoning[:1200].rstrip())

        required_tags = ["<Analyze>", "<Understand>", "<Execute>", "<Answer>"]
        missing = [tag for tag in required_tags if tag not in reasoning]
        if missing:
            raise SystemExit(f"Missing expected reasoning tags: {', '.join(missing)}")

        expected_path = workspace / args.expect_file
        if not expected_path.exists():
            raise SystemExit(f"Expected workspace artifact missing: {expected_path.name}")
        artifact_text = expected_path.read_text(encoding="utf-8", errors="replace")
        if "mock vLLM ok" not in artifact_text:
            raise SystemExit("Workspace artifact content did not match the mock response")

        print(f"\nWorkspace artifact found: {expected_path.name}")
        print("DeepAnalyzeVLLM smoke passed.")
        return 0
    finally:
        if temp_dir is not None and not args.keep_workspace:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
