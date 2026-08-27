#!/usr/bin/env python3
"""
Safe Graphify graph-building smoke test.

Creates a temporary one-file Python corpus, finds a `graphify` executable (or
falls back to `python -m graphify`), runs code-only extraction with
`--no-cluster` into a temporary output directory, and verifies that graph.json
contains both nodes and edges.

Examples:
  python build_tiny_graph.py
  python build_tiny_graph.py --keep-temp
  python build_tiny_graph.py --json
  python build_tiny_graph.py --python /path/to/python

This helper does not read or write the user's repository, make network calls,
require credentials, or depend on the original Graphify checkout.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KEY_VARS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_BASE_URL",
    "MOONSHOT_API_KEY",
    "DEEPSEEK_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
)


@dataclass
class CommandResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str], verbose: bool) -> CommandResult:
    if verbose:
        print("$ " + " ".join(shlex.quote(part) for part in cmd))
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )
    if verbose and result.stdout:
        print(result.stdout, end="")
    if verbose and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return CommandResult(cmd, result.returncode, result.stdout, result.stderr)


def _candidate_commands(args: argparse.Namespace) -> list[list[str]]:
    candidates: list[list[str]] = []
    if args.graphify:
        candidates.append(shlex.split(args.graphify))
    else:
        exe = shutil.which("graphify")
        if exe:
            candidates.append([exe])
    candidates.append([args.python, "-m", "graphify"])
    # Preserve order while removing exact duplicates.
    unique: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for cmd in candidates:
        key = tuple(cmd)
        if key not in seen:
            seen.add(key)
            unique.append(cmd)
    return unique


def _find_graphify(args: argparse.Namespace, *, cwd: Path, env: dict[str, str], verbose: bool) -> tuple[list[str], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for base in _candidate_commands(args):
        check = _run(base + ["--help"], cwd=cwd, env=env, verbose=verbose)
        attempts.append(
            {
                "cmd": check.cmd,
                "returncode": check.returncode,
                "stdout_tail": _tail(check.stdout, 1000),
                "stderr_tail": _tail(check.stderr, 1000),
            }
        )
        if check.returncode == 0:
            return base, attempts
    raise RuntimeError(
        "could not run Graphify via `graphify --help` or `python -m graphify --help`; "
        "install the public package `graphifyy` in the selected environment"
    )


def _write_tiny_corpus(corpus: Path) -> None:
    corpus.mkdir(parents=True, exist_ok=True)
    (corpus / "app.py").write_text(
        "def helper(value: int) -> int:\n"
        "    return value + 1\n\n"
        "def caller() -> int:\n"
        "    return helper(41)\n\n"
        "class Runner:\n"
        "    def run(self) -> int:\n"
        "        return caller()\n",
        encoding="utf-8",
    )


def _load_graph(graph_path: Path) -> tuple[int, int, int]:
    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - clear smoke-test error surface
        raise RuntimeError(f"could not parse graph.json as JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("graph.json is not a JSON object")
    nodes = data.get("nodes")
    links = data.get("links", data.get("edges"))
    hyperedges = data.get("hyperedges", [])
    if not isinstance(nodes, list):
        raise RuntimeError("graph.json missing list field `nodes`")
    if not isinstance(links, list):
        raise RuntimeError("graph.json missing list field `links` or `edges`")
    if not nodes:
        raise RuntimeError("graph.json has zero nodes")
    if not links:
        raise RuntimeError("graph.json has zero edges")
    return len(nodes), len(links), len(hyperedges) if isinstance(hyperedges, list) else 0


def _emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe tiny Graphify code-only graph build smoke test.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used for the `python -m graphify` fallback (default: current interpreter).",
    )
    parser.add_argument(
        "--graphify",
        default=None,
        help="Explicit Graphify command to try first, e.g. `graphify` or `/path/to/graphify`.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary corpus and output directory for inspection.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human-readable logs.",
    )
    args = parser.parse_args(argv)

    temp_owner = tempfile.TemporaryDirectory(prefix="graphify-tiny-")
    temp_root = Path(temp_owner.name)
    corpus = temp_root / "corpus"
    out_parent = temp_root / "out"
    graph_path = out_parent / "graphify-out" / "graph.json"
    attempts: list[dict[str, Any]] = []
    extract_result: CommandResult | None = None

    env = {k: v for k, v in os.environ.items() if k not in KEY_VARS}
    env["GRAPHIFY_OUT"] = "graphify-out"

    try:
        _write_tiny_corpus(corpus)
        graphify_cmd, attempts = _find_graphify(args, cwd=temp_root, env=env, verbose=not args.json)
        extract_cmd = graphify_cmd + [
            "extract",
            str(corpus),
            "--code-only",
            "--no-cluster",
            "--out",
            str(out_parent),
        ]
        extract_result = _run(extract_cmd, cwd=temp_root, env=env, verbose=not args.json)
        if extract_result.returncode != 0:
            raise RuntimeError("Graphify code-only extraction failed")
        if not graph_path.exists():
            raise RuntimeError(f"expected graph.json was not written at {graph_path}")
        node_count, edge_count, hyperedge_count = _load_graph(graph_path)
        manifest_path = out_parent / "graphify-out" / "manifest.json"
        if not manifest_path.exists():
            raise RuntimeError(f"expected manifest.json was not written at {manifest_path}")

        payload = {
            "ok": True,
            "graphify_command": graphify_cmd,
            "extract_command": extract_cmd,
            "temp_dir": str(temp_root),
            "kept_temp": bool(args.keep_temp),
            "graph_path": str(graph_path),
            "node_count": node_count,
            "edge_count": edge_count,
            "hyperedge_count": hyperedge_count,
            "manifest_path": str(manifest_path),
        }
        if args.json:
            _emit_json(payload)
        else:
            print(
                "Graphify tiny graph smoke passed: "
                f"{node_count} nodes, {edge_count} edges, {hyperedge_count} hyperedges"
            )
            print(f"graph.json: {graph_path}")
            if args.keep_temp:
                print(f"kept temp directory: {temp_root}")
        return 0
    except Exception as exc:  # noqa: BLE001 - this is a CLI smoke-test boundary
        payload = {
            "ok": False,
            "error": str(exc),
            "temp_dir": str(temp_root),
            "kept_temp": bool(args.keep_temp),
            "graph_path": str(graph_path),
            "discovery_attempts": attempts,
        }
        if extract_result is not None:
            payload["extract"] = {
                "cmd": extract_result.cmd,
                "returncode": extract_result.returncode,
                "stdout_tail": _tail(extract_result.stdout),
                "stderr_tail": _tail(extract_result.stderr),
            }
        if args.json:
            _emit_json(payload)
        else:
            print(f"error: {exc}", file=sys.stderr)
            if attempts:
                print("Graphify discovery attempts:", file=sys.stderr)
                for attempt in attempts:
                    print(f"  {' '.join(attempt['cmd'])} -> {attempt['returncode']}", file=sys.stderr)
                    if attempt.get("stderr_tail"):
                        print("    stderr: " + attempt["stderr_tail"].strip().replace("\n", "\n            "), file=sys.stderr)
            if extract_result is not None:
                if extract_result.stdout:
                    print("extract stdout:\n" + _tail(extract_result.stdout), file=sys.stderr)
                if extract_result.stderr:
                    print("extract stderr:\n" + _tail(extract_result.stderr), file=sys.stderr)
            if args.keep_temp:
                print(f"kept temp directory: {temp_root}", file=sys.stderr)
        return 1
    finally:
        if args.keep_temp:
            # Detach the TemporaryDirectory finalizer so the user can inspect it.
            temp_owner._finalizer.detach()  # type: ignore[attr-defined]
        else:
            temp_owner.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
