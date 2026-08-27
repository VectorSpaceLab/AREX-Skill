#!/usr/bin/env python3
"""Plan a KAG benchmark or open-benchmark run without executing it.

The planner understands both the shell-style benchmark workflow and the
`benchmark_config.yaml` style used by `kag benchmark`.

Examples:
  python skills/disco/kag/sub-skills/mcp-and-automation/scripts/plan_benchmark_command.py ./kag/open_benchmark all all
  python skills/disco/kag/sub-skills/mcp-and-automation/scripts/plan_benchmark_command.py ./kag/open_benchmark build sub --json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


SENSITIVE_KEYS = {"api_key", "token", "secret", "password", "passwd", "access_key", "access_token"}


def add_env_constructor() -> None:
    def _env(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        value = loader.construct_scalar(node)
        return os.getenv(value.strip())

    yaml.SafeLoader.add_constructor("!ENV", _env)


add_env_constructor()


def redact(key: str, value: Any) -> Any:
    if isinstance(value, dict):
        return {k: redact(k, v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [redact(key, item) for item in value]
    if isinstance(value, str):
        lower = key.lower()
        if any(token in lower for token in SENSITIVE_KEYS) or any(token in lower for token in ("secret", "token", "password")):
            return "<redacted>"
        if "://" not in value:
            stripped = value.strip()
            if stripped.startswith(("/", "~")) or "/" in stripped or "\\" in stripped:
                return "<path>"
    return value


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_env_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def split_name(split: str) -> Dict[str, str]:
    if split == "all":
        return {"corpus": "corpus.json", "qa": "qa.json"}
    return {"corpus": f"{split}_corpus.json", "qa": f"qa_{split}.json"}


def shell_plan(bench_dir: Path, command: str, split: str) -> Dict[str, Any]:
    corpus = split_name(split)["corpus"]
    qa = split_name(split)["qa"]
    plan: List[str] = []

    plan.append(f'python utils/key_utils.py --yml_file_path "{bench_dir / "kag_config.yaml"}" --env_json_path "{bench_dir / "env.json"}"')
    plan.append(f'cd "{bench_dir}"')
    if command in {"build", "all"}:
        plan.append("knext project restore --proj_path ./")
        plan.append("knext schema commit")
        plan.append(f'cd builder && python indexer.py --corpus_file "./data/{corpus}"')
        if command == "all":
            plan.append("cd ../solver")
            plan.append(f'python eval.py --qa_file "./data/{qa}"')
    elif command == "eval":
        plan.append("cd solver")
        plan.append(f'python eval.py --qa_file "./data/{qa}"')
    return {
        "mode": "shell",
        "bench_dir": str(bench_dir),
        "command": command,
        "split": split,
        "planned_commands": plan,
    }


def config_plan(bench_dir: Path, command: str, split: str, config: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for name, entry in config.items():
        if not isinstance(entry, dict):
            continue
        root_dir = entry.get("root_dir")
        config_file = entry.get("config_file")
        index_builder = entry.get("index_builder", {}) if isinstance(entry.get("index_builder"), dict) else {}
        qa_solver = entry.get("qa_solver", {}) if isinstance(entry.get("qa_solver"), dict) else {}
        entries.append(
            {
                "name": name,
                "root_dir": root_dir,
                "config_file": config_file,
                "index_builder_type": index_builder.get("type"),
                "qa_solver_type": qa_solver.get("type"),
                "selected_split": split,
                "planned_launcher": f"kag benchmark --job_config {bench_dir / 'benchmark_config.yaml'}",
            }
        )
    return {
        "mode": "benchmark-config",
        "bench_dir": str(bench_dir),
        "command": command,
        "split": split,
        "launcher_command": f"kag benchmark --job_config {bench_dir / 'benchmark_config.yaml'}",
        "entries": entries,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a KAG benchmark run without executing it.")
    parser.add_argument("bench_dir", help="Benchmark root directory.")
    parser.add_argument("command", choices=["build", "eval", "all"], help="Workflow stage to plan.")
    parser.add_argument("split", choices=["all", "sub", "train"], help="Dataset split to plan.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    bench_dir = Path(args.bench_dir).expanduser().resolve()
    if not bench_dir.exists():
        print(f"Benchmark directory does not exist: {bench_dir}")
        return 1

    benchmark_cfg = bench_dir / "benchmark_config.yaml"
    kag_cfg = bench_dir / "kag_config.yaml"
    env_json = bench_dir / "env.json"

    result: Dict[str, Any] = {
        "bench_dir": str(bench_dir),
        "command": args.command,
        "split": args.split,
        "env_json_keys": sorted(read_env_json(env_json).keys()) if env_json.exists() else [],
        "env_json": redact("env_json", read_env_json(env_json)) if env_json.exists() else {},
    }

    if benchmark_cfg.exists():
        try:
            result.update(config_plan(bench_dir, args.command, args.split, load_yaml(benchmark_cfg)))
        except Exception as exc:
            print(f"Failed to parse {benchmark_cfg}: {exc}")
            return 1
    elif kag_cfg.exists():
        result.update(shell_plan(bench_dir, args.command, args.split))
        result["kag_config"] = str(kag_cfg)
    else:
        print("Neither benchmark_config.yaml nor kag_config.yaml was found in the benchmark directory.")
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"bench dir: {result['bench_dir']}")
        print(f"command: {result['command']}")
        print(f"split: {result['split']}")
        if result.get("mode") == "shell":
            print("planned commands:")
            for item in result["planned_commands"]:
                print(f"- {item}")
        else:
            print(f"launcher: {result.get('launcher_command')}")
            print("entries:")
            for entry in result.get("entries", []):
                print(f"- {entry['name']}: {entry['root_dir']} ({entry['config_file']})")
                print(f"    builder: {entry['index_builder_type']}")
                print(f"    solver: {entry['qa_solver_type']}")
        if result.get("env_json_keys"):
            print("env json keys: " + ", ".join(result["env_json_keys"]))
        print("This is a dry run only; no files or servers were modified.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
