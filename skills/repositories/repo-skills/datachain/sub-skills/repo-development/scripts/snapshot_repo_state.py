#!/usr/bin/env python3
"""Print a DataChain checkout snapshot for staleness and refresh decisions.

Run from any DataChain repository checkout. The script reports relative dirty
paths, package metadata, and optional extras without mutating the checkout.

Examples:
  python snapshot_repo_state.py
  python snapshot_repo_state.py --json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib  # type: ignore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print git and pyproject metadata for a DataChain checkout."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository directory to inspect (default: current directory).",
    )
    return parser


def run(repo: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def load_pyproject(repo: Path) -> dict:
    path = repo / "pyproject.toml"
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    return {
        "name": project.get("name"),
        "requires_python": project.get("requires-python"),
        "dynamic": project.get("dynamic", []),
        "dependencies_count": len(project.get("dependencies", [])),
        "optional_extras": sorted(project.get("optional-dependencies", {}).keys()),
        "scripts": project.get("scripts", {}),
    }


def snapshot(repo: Path) -> dict:
    repo = repo.resolve()
    status = run(repo, ["status", "--short"])
    dirty_paths = []
    if status:
        for line in status.splitlines():
            if len(line) > 3:
                dirty_paths.append(line[3:])
    return {
        "repo_name": repo.name,
        "git": {
            "commit": run(repo, ["rev-parse", "HEAD"]),
            "branch": run(repo, ["branch", "--show-current"]),
            "tag": run(repo, ["describe", "--tags", "--exact-match", "HEAD"]),
            "dirty": bool(status),
            "dirty_paths": dirty_paths,
        },
        "pyproject": load_pyproject(repo),
    }


def print_human(record: dict) -> None:
    git = record["git"]
    project = record.get("pyproject", {})
    print(f"Repository: {record['repo_name']}")
    print(f"Commit: {git.get('commit') or 'unknown'}")
    print(f"Branch: {git.get('branch') or 'unknown'}")
    print(f"Tag: {git.get('tag') or 'none'}")
    print(f"Dirty: {git.get('dirty')}")
    if git.get("dirty_paths"):
        print("Dirty paths:")
        for path in git["dirty_paths"]:
            print(f"  - {path}")
    if project:
        print(f"Package: {project.get('name')}")
        print(f"Requires Python: {project.get('requires_python')}")
        print("Optional extras: " + ", ".join(project.get("optional_extras", [])))
        scripts = project.get("scripts", {})
        if scripts:
            print("Console scripts:")
            for name, target in scripts.items():
                print(f"  - {name} = {target}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo)
    if not repo.exists():
        print(f"error: repo path does not exist: {repo}", file=sys.stderr)
        return 2
    record = snapshot(repo)
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print_human(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
