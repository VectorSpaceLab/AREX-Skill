#!/usr/bin/env python3
"""Read-only checker for AlpaSim single-job and array-job output trees."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from alpasim_utils.logs import async_read_pb_log


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("metadata checking requires PyYAML") from exc
    value = yaml.safe_load(path.read_text())
    return value if isinstance(value, dict) else {}


def _job_dirs(root: Path) -> tuple[str, list[Path]]:
    if (root / "eval-config.yaml").is_file():
        return "single", [root]
    children = sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "eval-config.yaml").is_file()
    )
    if children:
        return "array", children
    return "unknown", []


async def _asl_summary(path: Path, max_messages: int) -> dict[str, Any]:
    count = 0
    kinds: set[str] = set()
    metadata: dict[str, Any] = {}
    malformed = None
    try:
        async for entry in async_read_pb_log(str(path), raise_on_malformed=True):
            kind = entry.WhichOneof("log_entry")
            if kind:
                kinds.add(kind)
            if kind == "rollout_metadata" and not metadata:
                session = entry.rollout_metadata.session_metadata
                metadata = {
                    "scene_id": session.scene_id,
                    "session_uuid": session.session_uuid,
                    "n_sim_steps": session.n_sim_steps,
                    "control_timestep_us": session.control_timestep_us,
                }
            count += 1
            if count >= max_messages:
                break
    except Exception as exc:  # syntax/read errors are reported, not hidden
        malformed = f"{type(exc).__name__}: {exc}"
    return {
        "path": str(path),
        "messages_checked": count,
        "bounded_before_eof": count >= max_messages and malformed is None,
        "message_types": sorted(kinds),
        "metadata": metadata,
        "malformed": malformed,
        "has_metadata": bool(metadata),
    }


async def check(root: Path, max_rollouts: int, max_messages: int) -> tuple[dict[str, Any], int]:
    layout, jobs = _job_dirs(root)
    report: dict[str, Any] = {"root": str(root), "layout": layout, "jobs": []}
    errors: list[str] = []
    if layout == "unknown":
        errors.append("no eval-config.yaml at root or in a child job directory")
    all_rollouts: list[Path] = []
    for job in jobs:
        eval_cfg = _load_yaml(job / "eval-config.yaml")
        wizard_path = job / "wizard-config.yaml"
        wizard_cfg = _load_yaml(wizard_path) if wizard_path.exists() else {}
        asls = sorted((job / "rollouts").glob("**/*.asl")) if (job / "rollouts").exists() else []
        complete = [path for path in asls if (path.parent / "_complete").exists()]
        all_rollouts.extend(asls)
        job_report: dict[str, Any] = {
            "path": str(job),
            "has_eval_config": True,
            "has_wizard_config": wizard_path.exists(),
            "has_run_metadata": (job / "run_metadata.yaml").exists(),
            "eval_config_keys": sorted(eval_cfg),
            "wizard_config_sections": sorted(wizard_cfg),
            "asl_count": len(asls),
            "complete_count": len(complete),
            "metrics_count": len(list((job / "rollouts").glob("**/metrics.parquet"))) if (job / "rollouts").exists() else 0,
        }
        if not wizard_path.exists():
            errors.append(f"{job}: missing wizard-config.yaml")
        if asls and len(complete) != len(asls):
            errors.append(f"{job}: {len(asls) - len(complete)} ASL file(s) lack _complete")
        if not asls:
            errors.append(f"{job}: no ASL files under rollouts/")
        report["jobs"].append(job_report)
    if len(all_rollouts) > max_rollouts:
        errors.append(f"matched {len(all_rollouts)} ASL files, exceeding --max-rollouts={max_rollouts}")
    asl_reports = []
    for path in all_rollouts[:max_rollouts]:
        asl_reports.append(await _asl_summary(path, max_messages))
    report["asl_reports"] = asl_reports
    bad_asls = [row for row in asl_reports if row["malformed"] or not row["has_metadata"]]
    if bad_asls:
        errors.append(f"{len(bad_asls)} checked ASL file(s) lack metadata or are malformed")
    report["errors"] = errors
    report["ok"] = not errors
    return report, 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--max-rollouts", type=int, default=1000)
    parser.add_argument("--max-messages", type=int, default=10000)
    args = parser.parse_args()
    if args.max_rollouts <= 0 or args.max_messages <= 0:
        parser.error("max-rollouts and max-messages must be positive")
    report, code = asyncio.run(check(args.run_root, args.max_rollouts, args.max_messages))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
