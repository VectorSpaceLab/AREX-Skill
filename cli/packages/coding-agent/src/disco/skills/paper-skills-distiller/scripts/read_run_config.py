#!/usr/bin/env python3
"""Validate and normalize a Distiller TOML run config."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any


DEFAULT_ITERATION_BUDGET = 10


def infer_distiller_skills_root() -> Path:
    """Infer the bundled Distiller skills root from this script location."""
    return Path(__file__).resolve().parents[2]


def default_run_root(workspace_root: Path, slug: str) -> Path:
    return workspace_root / slug


DEFAULTS: dict[str, Any] = {
    "original_repo_source": "unknown",
    "source_acquisition": (
        "If paper_source or original_repo_source are not local paths, resolve and download/clone them first "
        "with bounded network commands. If a paper title or repo discovery search is ambiguous, ask the user "
        "to choose from candidates."
    ),
    "repo_discovery_mode": "ask",
    "network_timeout_seconds": 120,
    "command_timeout_seconds": 20,
    "allow_title_top_hit": False,
    "recovery_target": "Choose the fastest faithful target and ask before expensive recovery.",
    "ask_before_expensive_recovery": True,
    "recovery_mode": "hard",
    "runtime_constraints": (
        "Do not mutate shared conda envs; use isolated env only. Create/reuse private recovery envs under "
        "$DISCO_CODING_AGENT_DIR/envs/ or ~/.disco/agent/envs/. Missing packages, model caches, datasets, "
        "or credentials are setup work to attempt before marking blocked. Reduced recovery is allowed if full "
        "model stack is unavailable."
    ),
    "iteration_budget": DEFAULT_ITERATION_BUDGET,
    "language_preference": "Chinese summary",
    "test_root": "",
    "skills_root": "",
    "generated_skills_root": "",
    "distiller_skills_root": "",
    "attempt_dir": "",
    "notes": "",
}

INHERIT_IF_BLANK = {
    "original_repo_source",
    "source_acquisition",
    "repo_discovery_mode",
    "recovery_target",
    "recovery_mode",
    "runtime_constraints",
    "language_preference",
    "test_root",
    "skills_root",
    "generated_skills_root",
    "distiller_skills_root",
    "attempt_dir",
}


class ConfigError(ValueError):
    pass


def config_path_value(value: Any, default: Path, workspace_root: Path) -> str:
    path = Path(str(value or default)).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    return str(path.resolve())


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "paper"


def read_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_timeout(value: Any, field: str, errors: list[str]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        errors.append(f"{field} must be a positive integer")
        return 1
    return value


def normalize_iteration_budget(value: Any, errors: list[str]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append("iteration_budget must be a non-negative integer")
        return DEFAULT_ITERATION_BUDGET
    return value


def normalize_recovery_mode(value: Any, errors: list[str]) -> str:
    mode = str(value or DEFAULTS["recovery_mode"]).strip().lower()
    if mode not in {"hard", "soft"}:
        errors.append("recovery_mode must be 'hard' or 'soft'")
        return DEFAULTS["recovery_mode"]
    return mode


def normalize_repo_discovery_mode(value: Any, errors: list[str]) -> str:
    mode = str(value or DEFAULTS["repo_discovery_mode"]).strip().lower()
    if mode not in {"ask", "auto", "disabled"}:
        errors.append("repo_discovery_mode must be 'ask', 'auto', or 'disabled'")
        return DEFAULTS["repo_discovery_mode"]
    return mode


def merge_defaults(defaults: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    merged = dict(DEFAULTS)
    merged.update(defaults)
    for key, value in run.items():
        if key in INHERIT_IF_BLANK and value == "":
            continue
        merged[key] = value
    return merged


def normalize_run(raw: dict[str, Any], index: int, config_path: Path, defaults: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    run = merge_defaults(defaults, raw)

    if not non_empty_string(run.get("paper_source")):
        errors.append(f"runs[{index}].paper_source is required")
    if not non_empty_string(run.get("paper_slug")):
        errors.append(f"runs[{index}].paper_slug is required")
        slug = f"run_{index + 1}"
    else:
        slug = slugify(str(run["paper_slug"]))

    workspace_value = run.get("workspace_root")
    if not non_empty_string(workspace_value):
        errors.append("workspace_root is required in [defaults] or each [[runs]] entry")
        workspace_root = Path(".").resolve()
    else:
        workspace_root = Path(str(workspace_value)).expanduser().resolve()

    network_timeout = normalize_timeout(run.get("network_timeout_seconds"), "network_timeout_seconds", errors)
    command_timeout = normalize_timeout(run.get("command_timeout_seconds"), "command_timeout_seconds", errors)
    iteration_budget = normalize_iteration_budget(run.get("iteration_budget"), errors)
    recovery_mode = normalize_recovery_mode(run.get("recovery_mode"), errors)
    repo_discovery_mode = normalize_repo_discovery_mode(run.get("repo_discovery_mode"), errors)

    allow_title_top_hit = run.get("allow_title_top_hit")
    if not isinstance(allow_title_top_hit, bool):
        errors.append("allow_title_top_hit must be true or false")
        allow_title_top_hit = False

    ask_before_expensive_recovery = run.get("ask_before_expensive_recovery")
    if not isinstance(ask_before_expensive_recovery, bool):
        errors.append("ask_before_expensive_recovery must be true or false")
        ask_before_expensive_recovery = True

    run_root = default_run_root(workspace_root, slug)
    test_root = config_path_value(run.get("test_root"), run_root, workspace_root)
    skills_root = config_path_value(run.get("skills_root"), run_root / "skills", workspace_root)
    generated_skills_root = config_path_value(
        run.get("generated_skills_root"),
        Path(skills_root),
        workspace_root,
    )
    distiller_skills_root = config_path_value(
        run.get("distiller_skills_root"),
        infer_distiller_skills_root(),
        workspace_root,
    )
    attempt_dir = config_path_value(run.get("attempt_dir"), run_root / "distillation", workspace_root)

    normalized = {
        "config_path": str(config_path),
        "config_run_index": index,
        "workspace_root": str(workspace_root),
        "paper_slug": slug,
        "paper_source": str(run.get("paper_source", "")).strip(),
        "original_repo_source": str(run.get("original_repo_source") or "unknown").strip(),
        "source_acquisition": str(run.get("source_acquisition") or DEFAULTS["source_acquisition"]).strip(),
        "repo_discovery_mode": repo_discovery_mode,
        "network_timeout_seconds": network_timeout,
        "command_timeout_seconds": command_timeout,
        "allow_title_top_hit": allow_title_top_hit,
        "recovery_target": str(run.get("recovery_target") or DEFAULTS["recovery_target"]).strip(),
        "ask_before_expensive_recovery": ask_before_expensive_recovery,
        "recovery_mode": recovery_mode,
        "runtime_constraints": str(run.get("runtime_constraints") or DEFAULTS["runtime_constraints"]).strip(),
        "iteration_budget": iteration_budget,
        "language_preference": str(run.get("language_preference") or DEFAULTS["language_preference"]).strip(),
        "run_root": str(run_root),
        "distillation_root": attempt_dir,
        "test_root": test_root,
        "skills_root": skills_root,
        "generated_skills_root": generated_skills_root,
        "distiller_skills_root": distiller_skills_root,
        "attempt_dir": attempt_dir,
        "paper_cache_dir": str(Path(attempt_dir) / "source"),
        "source_resolution_path": str(Path(attempt_dir) / "source" / "source_resolution.json"),
        "notes": str(run.get("notes") or "").strip(),
    }
    return normalized, errors


def normalize_config(config_path: Path, selector_slug: str = "", selector_index: int | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    data = read_config(config_path)
    errors: list[str] = []

    schema_version = data.get("schema_version")
    if schema_version != 1:
        errors.append("schema_version must be 1")

    defaults = data.get("defaults") or {}
    if not isinstance(defaults, dict):
        errors.append("[defaults] must be a table")
        defaults = {}

    raw_runs = data.get("runs")
    if not isinstance(raw_runs, list) or not raw_runs:
        errors.append("config must contain at least one [[runs]] entry")
        raw_runs = []

    runs: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_runs):
        if not isinstance(raw, dict):
            errors.append(f"runs[{index}] must be a table")
            continue
        normalized, run_errors = normalize_run(raw, index, config_path, defaults)
        runs.append(normalized)
        errors.extend(run_errors)

    if selector_slug:
        slug = slugify(selector_slug)
        runs = [run for run in runs if run["paper_slug"] == slug]
        if not runs:
            errors.append(f"no run matched --slug {selector_slug!r}")

    if selector_index is not None:
        if selector_index < 1:
            errors.append("--index is 1-based and must be at least 1")
            runs = []
        elif selector_index > len(runs):
            errors.append(f"--index {selector_index} is out of range for {len(runs)} run(s)")
            runs = []
        else:
            runs = [runs[selector_index - 1]]

    return runs, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Path to a Distiller TOML run config.")
    parser.add_argument("--slug", default="", help="Select one run by paper_slug.")
    parser.add_argument("--index", type=int, default=None, help="Select one run by 1-based index after slug filtering.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    parser.add_argument(
        "--run-only",
        action="store_true",
        help="Emit the selected normalized run object instead of the wrapper report. Requires exactly one selected run.",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser().resolve()
    runs, errors = normalize_config(config_path, selector_slug=args.slug, selector_index=args.index)
    if args.run_only and len(runs) != 1:
        errors.append("--run-only requires exactly one selected run; use --slug or --index")
    result = {
        "schema_version": 1,
        "ok": not errors,
        "config_path": str(config_path),
        "count": len(runs),
        "runs": runs,
        "errors": errors,
    }
    if len(runs) == 1:
        result["run"] = runs[0]
    output_data: dict[str, Any] = runs[0] if args.run_only and len(runs) == 1 and not errors else result

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output_data, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
