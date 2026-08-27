#!/usr/bin/env python3
"""Index Scenic project configs and requirements without importing Scenic.

This helper is intentionally read-only. It scans a user-supplied Scenic checkout,
Scenic package directory, or scenic/projects directory and summarizes project
names, config files, requirement files, main/eval modules, and optionally tool
script names. It never imports project code and never executes project tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Iterable

_SKIP_DIRS = {"__pycache__", ".git", ".hg", ".svn", ".mypy_cache", ".pytest_cache"}
_ASSIGNMENT_RE = re.compile(
    r"config(?:\.model)?\.(model_name|trainer_name|dataset_name)\s*=\s*['\"]([^'\"]+)['\"]"
)
_MODEL_MODEL_RE = re.compile(r"config\.model\.model_name\s*=\s*['\"]([^'\"]+)['\"]")


def _is_under_skipped_dir(path: Path) -> bool:
  return any(part in _SKIP_DIRS for part in path.parts)


def find_projects_root(root: Path) -> Path:
  """Returns scenic/projects for a checkout, scenic package, or projects dir."""
  root = root.expanduser().resolve()
  candidates = [
      root,
      root / "scenic" / "projects",
      root / "projects",
  ]
  for candidate in candidates:
    if candidate.is_dir() and (candidate / "README.md").exists():
      # The projects root contains many project directories and its own README.
      if any((candidate / name).is_dir() for name in ("baselines", "vivit", "owl_vit")):
        return candidate
  raise FileNotFoundError(
      f"Could not find scenic/projects under {root}. Provide a Scenic checkout, "
      "the scenic package directory, or the scenic/projects directory."
  )


def read_requirements(path: Path) -> list[str]:
  lines: list[str] = []
  try:
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
      stripped = raw.strip()
      if not stripped or stripped.startswith("#"):
        continue
      lines.append(stripped)
  except OSError as exc:
    lines.append(f"<unreadable: {exc}>")
  return lines


def rel(path: Path, base: Path) -> str:
  return path.relative_to(base).as_posix()


def iter_project_dirs(projects_root: Path, include_baseline_subprojects: bool) -> Iterable[Path]:
  for child in sorted(projects_root.iterdir()):
    if not child.is_dir() or child.name in _SKIP_DIRS:
      continue
    yield child
    if include_baseline_subprojects and child.name == "baselines":
      for sub in sorted(child.iterdir()):
        if sub.is_dir() and sub.name not in _SKIP_DIRS and not sub.name.startswith("."):
          if (sub / "README.md").exists() or (sub / "main.py").exists() or (sub / "configs").is_dir():
            yield sub


def collect_configs(project_dir: Path, max_configs: int) -> tuple[list[Path], int]:
  config_root = project_dir / "configs"
  if not config_root.is_dir():
    return [], 0
  configs = [
      p for p in sorted(config_root.rglob("*.py"))
      if p.name != "__init__.py" and not _is_under_skipped_dir(p)
  ]
  return configs[:max_configs], len(configs)


def collect_main_modules(project_dir: Path) -> list[str]:
  patterns = ("main.py", "*_main.py", "*evaluator.py", "evaluate.py")
  found: set[Path] = set()
  for pattern in patterns:
    for path in project_dir.glob(pattern):
      if path.is_file() and not _is_under_skipped_dir(path):
        found.add(path)
  return sorted(path.name for path in found)


def collect_requirements(project_dir: Path, projects_root: Path) -> list[dict[str, object]]:
  out: list[dict[str, object]] = []
  for path in sorted(project_dir.rglob("requirements.txt")):
    if _is_under_skipped_dir(path):
      continue
    out.append({"path": rel(path, projects_root), "requirements": read_requirements(path)})
  return out


def collect_tools(project_dir: Path, projects_root: Path) -> list[str]:
  tools_root = project_dir / "tools"
  if not tools_root.is_dir():
    return []
  tool_files = []
  for suffix in ("*.py", "*.ipynb", "*.sh"):
    tool_files.extend(tools_root.rglob(suffix))
  return [rel(path, projects_root) for path in sorted(tool_files) if not _is_under_skipped_dir(path)]


def extract_config_keys(config_paths: Iterable[Path]) -> dict[str, list[str]]:
  values: dict[str, set[str]] = {
      "model_name": set(),
      "model.model_name": set(),
      "trainer_name": set(),
      "dataset_name": set(),
  }
  for path in config_paths:
    try:
      text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
      continue
    for key, value in _ASSIGNMENT_RE.findall(text):
      values[key].add(value)
    for value in _MODEL_MODEL_RE.findall(text):
      values["model.model_name"].add(value)
  return {key: sorted(val) for key, val in values.items() if val}


def build_index(args: argparse.Namespace) -> dict[str, object]:
  projects_root = find_projects_root(Path(args.scenic_path))
  projects: list[dict[str, object]] = []

  for project_dir in iter_project_dirs(projects_root, args.include_baseline_subprojects):
    config_paths, config_total = collect_configs(project_dir, args.max_configs_per_project)
    project_info: dict[str, object] = {
        "name": rel(project_dir, projects_root),
        "main_modules": collect_main_modules(project_dir),
        "config_count": config_total,
        "configs_sample": [rel(path, projects_root) for path in config_paths],
        "requirements": collect_requirements(project_dir, projects_root),
    }
    if args.extract_keys:
      # Extract from the sampled configs only, so --max-configs-per-project bounds file reads.
      project_info["config_keys_sample"] = extract_config_keys(config_paths)
    if args.include_tools:
      project_info["tools"] = collect_tools(project_dir, projects_root)
    projects.append(project_info)

  return {
      "projects_root": str(projects_root),
      "project_count": len(projects),
      "include_baseline_subprojects": args.include_baseline_subprojects,
      "max_configs_per_project": args.max_configs_per_project,
      "projects": projects,
  }


def print_text(index: dict[str, object]) -> None:
  print(f"Scenic projects root: {index['projects_root']}")
  print(f"Projects indexed: {index['project_count']}")
  print(f"Baseline subprojects included: {index['include_baseline_subprojects']}")
  print()
  for project in index["projects"]:  # type: ignore[index]
    print(f"## {project['name']}")
    mains = project.get("main_modules") or []
    print("main/eval modules: " + (", ".join(mains) if mains else "<none found>"))
    print(f"configs: {project['config_count']}")
    for cfg in project.get("configs_sample", []):
      print(f"  - {cfg}")
    reqs = project.get("requirements") or []
    if reqs:
      print("requirements:")
      for req in reqs:
        print(f"  - {req['path']}: " + ("; ".join(req["requirements"]) or "<empty>"))
    else:
      print("requirements: <none found>")
    keys = project.get("config_keys_sample")
    if keys:
      print("config keys sample:")
      for key, values in keys.items():
        print(f"  - {key}: {', '.join(values)}")
    tools = project.get("tools")
    if tools is not None:
      print("tools: " + (", ".join(tools) if tools else "<none found>"))
    print()


def parse_args(argv: list[str]) -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description=(
          "Safely index Scenic project configs, requirements, and optional tool "
          "names without importing or executing project code."
      )
  )
  parser.add_argument(
      "scenic_path",
      help="Path to a Scenic checkout, the scenic package directory, or scenic/projects.",
  )
  parser.add_argument(
      "--include-baseline-subprojects",
      action="store_true",
      help="Also list baselines/bert, baselines/detr, baselines/centernet, etc. as separate entries.",
  )
  parser.add_argument(
      "--include-tools",
      action="store_true",
      help="Include names of files under each project's tools/ directory. Does not run them.",
  )
  parser.add_argument(
      "--extract-keys",
      action="store_true",
      help="Regex-extract common config assignment values from sampled config files.",
  )
  parser.add_argument(
      "--max-configs-per-project",
      type=int,
      default=20,
      help="Maximum config files to list and inspect per project (default: 20).",
  )
  parser.add_argument(
      "--json",
      action="store_true",
      help="Emit JSON instead of text.",
  )
  args = parser.parse_args(argv)
  if args.max_configs_per_project < 0:
    parser.error("--max-configs-per-project must be non-negative")
  return args


def main(argv: list[str]) -> int:
  args = parse_args(argv)
  try:
    index = build_index(args)
  except Exception as exc:  # Keep CLI helper friendly and dependency-free.
    print(f"project_config_index.py: error: {exc}", file=sys.stderr)
    return 2
  if args.json:
    print(json.dumps(index, indent=2, sort_keys=True))
  else:
    print_text(index)
  return 0


if __name__ == "__main__":
  raise SystemExit(main(sys.argv[1:]))
