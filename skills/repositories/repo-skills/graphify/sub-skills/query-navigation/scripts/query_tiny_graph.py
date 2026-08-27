#!/usr/bin/env python3
"""
Safe Graphify query-navigation smoke test.

Creates a temporary NetworkX node-link-style graph.json, runs Graphify's public
query/path/explain read commands against it, checks edge direction and reverse
arrow rendering, and exercises the deterministic save-result/reflect lesson
loop. It does not read or write the user's repository, call network services,
or depend on the original Graphify checkout.

Examples:
  python query_tiny_graph.py
  python query_tiny_graph.py --python /path/to/python --keep-temp
  python query_tiny_graph.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class StepResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class SmokeFailure(RuntimeError):
    pass


def _manual_node_link_graph() -> dict[str, Any]:
    """Return a small NetworkX node-link JSON object.

    The graph is persisted as undirected (`directed: false`), matching common
    Graphify graph.json output where each link's source/target still carries
    the true relation direction.
    """
    return {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "nodes": [
            {
                "id": "caller",
                "label": "CallerService",
                "source_file": "src/caller.py",
                "source_location": "L10",
                "file_type": "code",
                "community": 0,
                "community_name": "Runtime",
            },
            {
                "id": "target",
                "label": "TargetWorker",
                "source_file": "src/worker.py",
                "source_location": "L20",
                "file_type": "code",
                "community": 0,
                "community_name": "Runtime",
            },
            {
                "id": "hub",
                "label": "AuthHub",
                "source_file": "src/auth.py",
                "source_location": "L1",
                "file_type": "code",
                "community": 1,
                "community_name": "Auth",
            },
        ],
        "links": [
            {
                "source": "caller",
                "target": "target",
                "relation": "calls",
                "confidence": "EXTRACTED",
                "context": "call",
                "source_file": "src/caller.py",
                "source_location": "L12",
            },
            {
                "source": "caller",
                "target": "hub",
                "relation": "uses",
                "confidence": "INFERRED",
                "context": "call",
                "source_file": "src/caller.py",
                "source_location": "L14",
            },
        ],
    }


def _print_result(result: StepResult) -> None:
    print("$ " + " ".join(result.command))
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)


def _run(
    name: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    quiet: bool,
) -> StepResult:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        result = StepResult(
            name=name,
            command=command,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nerror: timed out after {timeout:g}s",
        )
        if not quiet:
            _print_result(result)
        return result
    result = StepResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if not quiet:
        _print_result(result)
    return result


def _require(condition: bool, message: str, result: StepResult | None = None) -> None:
    if condition:
        return
    details = [f"error: {message}"]
    if result is not None:
        details.append(f"step: {result.name}")
        details.append("command: " + " ".join(result.command))
        details.append(f"returncode: {result.returncode}")
        if result.stdout:
            details.append("stdout:\n" + result.stdout.rstrip())
        if result.stderr:
            details.append("stderr:\n" + result.stderr.rstrip())
    raise SmokeFailure("\n".join(details))


def _run_graphify(
    python_cmd: str,
    args: list[str],
    *,
    name: str,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    quiet: bool,
) -> StepResult:
    return _run(
        name,
        [python_cmd, "-m", "graphify", *args],
        cwd=cwd,
        env=env,
        timeout=timeout,
        quiet=quiet,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe tiny Graphify query/path/explain smoke test.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used for `-m graphify` (default: current interpreter).",
    )
    parser.add_argument(
        "--keep-temp",
        "--keep",
        dest="keep_temp",
        action="store_true",
        help="Keep the temporary work directory for inspection.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a compact JSON result instead of command transcripts.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds allowed per Graphify command (default: 30).",
    )
    args = parser.parse_args(argv)

    python_cmd = args.python
    if not Path(python_cmd).exists() and shutil.which(python_cmd) is None:
        print(f"error: Python executable not found: {python_cmd}", file=sys.stderr)
        return 2

    temp_owner: tempfile.TemporaryDirectory[str] | None
    if args.keep_temp:
        temp_owner = None
        root = Path(tempfile.mkdtemp(prefix="graphify-query-tiny-"))
    else:
        temp_owner = tempfile.TemporaryDirectory(prefix="graphify-query-tiny-")
        root = Path(temp_owner.name)
    graph_dir = root / "graphify-out"
    graph_dir.mkdir(parents=True)
    graph_path = graph_dir / "graph.json"
    graph_path.write_text(json.dumps(_manual_node_link_graph(), indent=2), encoding="utf-8")

    env = os.environ.copy()
    env["GRAPHIFY_OUT"] = "graphify-out"
    env["GRAPHIFY_QUERY_LOG_DISABLE"] = "1"
    env.setdefault("PYTHONIOENCODING", "utf-8")

    quiet = bool(args.json)
    steps: list[StepResult] = []
    error: str | None = None
    kept = bool(args.keep_temp)

    try:
        check = _run(
            "import graphify",
            [python_cmd, "-c", "import graphify; print('graphify import ok')"],
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(check)
        _require(check.returncode == 0, "could not import graphify with the selected Python", check)

        query = _run_graphify(
            python_cmd,
            ["query", "TargetWorker", "--graph", str(graph_path)],
            name="query callee",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(query)
        _require(query.returncode == 0, "graphify query failed", query)
        _require("Traversal: BFS" in query.stdout, "query output did not include BFS traversal header", query)
        _require("NODE TargetWorker" in query.stdout, "query output omitted the target node label", query)
        _require(
            "CallerService --calls [EXTRACTED context=call]--> TargetWorker" in query.stdout,
            "query output did not preserve caller -> callee edge direction",
            query,
        )
        _require(
            "TargetWorker --calls" not in query.stdout,
            "query output rendered the calls edge backwards",
            query,
        )

        path_forward = _run_graphify(
            python_cmd,
            ["path", "CallerService", "TargetWorker", "--graph", str(graph_path)],
            name="path forward",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(path_forward)
        _require(path_forward.returncode == 0, "graphify path forward failed", path_forward)
        _require(
            "CallerService --calls [EXTRACTED]--> TargetWorker" in path_forward.stdout,
            "forward path did not render CallerService -> TargetWorker",
            path_forward,
        )

        path_reverse = _run_graphify(
            python_cmd,
            ["path", "TargetWorker", "CallerService", "--undirected", "--graph", str(graph_path)],
            name="path reverse arrow",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(path_reverse)
        _require(path_reverse.returncode == 0, "graphify undirected reverse path failed", path_reverse)
        _require(
            "TargetWorker <--calls [EXTRACTED]-- CallerService" in path_reverse.stdout,
            "reverse path did not show the stored edge as a reverse arrow",
            path_reverse,
        )
        _require(
            "TargetWorker --calls [EXTRACTED]--> CallerService" not in path_reverse.stdout,
            "reverse path incorrectly inverted the stored relation",
            path_reverse,
        )

        explain = _run_graphify(
            python_cmd,
            ["explain", "TargetWorker", "--graph", str(graph_path)],
            name="explain target",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(explain)
        _require(explain.returncode == 0, "graphify explain failed", explain)
        _require("Node: TargetWorker" in explain.stdout, "explain omitted node header", explain)
        _require("<-- CallerService [calls] [EXTRACTED]" in explain.stdout, "explain did not show inbound caller", explain)
        _require("src/caller.py:L12" in explain.stdout, "explain omitted edge call-site location", explain)

        affected = _run_graphify(
            python_cmd,
            ["affected", "TargetWorker", "--graph", str(graph_path)],
            name="affected target",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(affected)
        _require(affected.returncode == 0, "graphify affected failed", affected)
        _require("Affected nodes for TargetWorker" in affected.stdout, "affected omitted header", affected)
        _require("- CallerService [calls] src/caller.py:L12" in affected.stdout, "affected omitted caller impact line", affected)

        gods = _run_graphify(
            python_cmd,
            ["god-nodes", "--graph", str(graph_path), "--json"],
            name="god-nodes json",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(gods)
        _require(gods.returncode == 0, "graphify god-nodes failed", gods)
        try:
            god_data = json.loads(gods.stdout)
        except json.JSONDecodeError as exc:
            raise SmokeFailure(f"error: god-nodes --json did not emit JSON: {exc}\nstdout:\n{gods.stdout}") from exc
        _require(isinstance(god_data, list) and god_data, "god-nodes JSON was empty", gods)
        _require(god_data[0].get("label") == "CallerService", "god-nodes did not rank CallerService first", gods)
        _require(god_data[0].get("degree") == 2, "god-nodes degree for CallerService was not 2", gods)

        save = _run_graphify(
            python_cmd,
            [
                "save-result",
                "--question",
                "who calls TargetWorker?",
                "--answer",
                "CallerService calls TargetWorker via src/caller.py:L12.",
                "--type",
                "query",
                "--nodes",
                "TargetWorker",
                "CallerService",
                "--outcome",
                "useful",
            ],
            name="save-result useful",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(save)
        _require(save.returncode == 0, "graphify save-result failed", save)
        _require("Saved to" in save.stdout, "save-result did not report a saved memory file", save)

        reflect = _run_graphify(
            python_cmd,
            ["reflect", "--graph", str(graph_path)],
            name="reflect lessons",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(reflect)
        _require(reflect.returncode == 0, "graphify reflect failed", reflect)
        _require("Reflected 1" in reflect.stdout, "reflect did not aggregate the saved result", reflect)
        lessons = graph_dir / "reflections" / "LESSONS.md"
        _require(lessons.exists(), "reflect did not write graphify-out/reflections/LESSONS.md")
        lesson_text = lessons.read_text(encoding="utf-8")
        _require("TargetWorker" in lesson_text and "CallerService" in lesson_text, "lessons did not mention saved source nodes")

        explain_after = _run_graphify(
            python_cmd,
            ["explain", "TargetWorker", "--graph", str(graph_path)],
            name="explain lesson overlay",
            cwd=root,
            env=env,
            timeout=args.timeout,
            quiet=quiet,
        )
        steps.append(explain_after)
        _require(explain_after.returncode == 0, "graphify explain after reflect failed", explain_after)
        _require("Lesson:" in explain_after.stdout, "explain did not display the reflected lesson overlay", explain_after)

        summary = {
            "ok": True,
            "workdir": str(root),
            "kept": kept,
            "graph": str(graph_path),
            "steps": [
                {"name": s.name, "returncode": s.returncode} for s in steps
            ],
        }
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("Graphify query-navigation tiny graph smoke passed")
            print(f"workdir: {root}" + (" (kept)" if kept else " (temporary)"))
        return 0
    except SmokeFailure as exc:
        error = str(exc)
        kept = True if args.keep_temp else False
        if args.json:
            print(json.dumps({
                "ok": False,
                "error": error,
                "workdir": str(root),
                "kept": kept,
                "steps": [asdict(s) for s in steps],
            }, indent=2))
        else:
            print(error, file=sys.stderr)
            print(f"workdir: {root}" + (" (kept)" if kept else " (temporary)"), file=sys.stderr)
        return 1
    finally:
        if temp_owner is not None:
            temp_owner.cleanup()
        elif error is None and not args.json:
            print(f"kept temporary directory: {root}")


if __name__ == "__main__":
    raise SystemExit(main())
