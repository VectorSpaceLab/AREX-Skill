#!/usr/bin/env python3
"""Read-only audit for a Deep Researcher project.

This script intentionally has no project-package imports and no write paths.
It audits the supplied project/workspace, renders compact state, and computes
safe derived signals from valid ledger data only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"{exc.__class__.__name__}: {exc}"


def load_json(path: Path) -> tuple[Any, str | None]:
    text, error = read_text(path)
    if error:
        return None, error
    try:
        return json.loads(text or ""), None
    except json.JSONDecodeError as exc:
        return None, f"JSONDecodeError: {exc}"


def parse_ledger(path: Path) -> tuple[list[dict], int, int, str | None]:
    text, error = read_text(path)
    if error:
        return [], 0, 0, error
    entries: list[dict] = []
    malformed = 0
    nonempty = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        nonempty += 1
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(value, dict):
            entries.append(value)
        else:
            malformed += 1
    return entries, malformed, nonempty, None


def metric_values(entries: list[dict], key: str) -> list[float]:
    values: list[float] = []
    if not key:
        return values
    for entry in entries:
        metrics = entry.get("metrics")
        if not isinstance(metrics, dict) or key not in metrics:
            continue
        try:
            values.append(float(metrics[key]))
        except (TypeError, ValueError):
            continue
    return values


def direction_best(values: list[float], direction: str) -> float | None:
    if not values:
        return None
    return max(values) if direction == "higher_better" else min(values)


def stagnation(values: list[float], key: str, direction: str, threshold: int, delta: float) -> dict:
    result: dict[str, Any] = {
        "stagnating": False,
        "metric_key": key,
        "best": None,
        "recent_best": None,
        "cycles_since_improvement": 0,
        "n_points": len(values),
    }
    if not key:
        result["reason"] = "no metric_key configured"
        return result
    if len(values) <= threshold:
        result["reason"] = "not enough metric points yet"
        if values:
            result["best"] = direction_best(values, direction)
        return result
    higher = direction == "higher_better"
    best = values[0]
    since = 0
    for value in values[1:]:
        improved = value > best + delta if higher else value < best - delta
        if improved:
            best = value
            since = 0
        else:
            since += 1
    recent = values[-threshold:] if threshold > 0 else values
    result.update(
        best=best,
        recent_best=direction_best(recent, direction),
        cycles_since_improvement=since,
        stagnating=since >= threshold,
    )
    return result


def phase_gate(values: list[float], key: str, threshold: float, direction: str) -> dict:
    best = direction_best(values, direction)
    if best is None:
        return {
            "gate_met": False,
            "best_metric": None,
            "blocker_reason": "no metric recorded yet",
        }
    met = best >= threshold if direction == "higher_better" else best <= threshold
    reason = "" if met else (
        f"best {key}={best} has not cleared the gate threshold "
        f"{threshold} ({direction})"
    )
    return {"gate_met": met, "best_metric": best, "blocker_reason": reason}


def violation_scan(
    state: Any,
    fail_count: int,
    now: float,
    fail_threshold: int,
    stale_state_hours: float,
) -> list[str]:
    state = state if isinstance(state, dict) else {}
    violations: list[str] = []
    if fail_threshold and fail_count >= fail_threshold:
        violations.append(
            f"{fail_count} consecutive no-progress cycles on the same plan"
        )
    updated = state.get("updated_at")
    if updated is not None and state.get("status") == "running" and stale_state_hours:
        try:
            age_hours = (float(now) - float(updated)) / 3600.0
        except (TypeError, ValueError):
            age_hours = 0.0
        if age_hours > stale_state_hours:
            violations.append(
                f"state is running and {age_hours:.1f}h old "
                f"(limit {stale_state_hours:g}h)"
            )
    return violations


def rate_wait(timestamps: list[float], now: float, cap: int, window: int = 3600) -> float:
    if cap <= 0:
        return 0.0
    recent = [stamp for stamp in timestamps if now - stamp < window]
    if len(recent) < cap:
        return 0.0
    recent.sort()
    target = recent[len(recent) - cap]
    return max(0.0, float(window) - (now - target))


def tail(text: str | None, limit: int) -> str:
    if not text:
        return ""
    return text[-limit:] if len(text) > limit else text


def inspect(args: argparse.Namespace) -> tuple[dict, list[str]]:
    project = Path(args.project).expanduser()
    if not project.is_dir():
        raise ValueError(f"project is not a directory: {project}")
    workspace_arg = Path(args.workspace) if args.workspace else Path("workspace")
    workspace = workspace_arg if workspace_arg.is_absolute() else project / workspace_arg
    if not workspace.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")

    warnings: list[str] = []
    result: dict[str, Any] = {
        "project": str(project),
        "workspace": str(workspace),
        "files": {},
        "warnings": warnings,
    }

    brief, brief_error = read_text(project / "PROJECT_BRIEF.md")
    result["brief"] = {
        "exists": brief is not None,
        "chars": len(brief or ""),
        "preview": tail(brief, args.preview_chars),
    }
    if brief_error:
        warnings.append(f"PROJECT_BRIEF.md: {brief_error}")

    memory, memory_error = read_text(workspace / "MEMORY_LOG.md")
    result["memory_log"] = {
        "exists": memory is not None,
        "chars": len(memory or ""),
        "preview": tail(memory, args.preview_chars),
    }
    if memory_error:
        warnings.append(f"MEMORY_LOG.md: {memory_error}")

    counter_text, counter_error = read_text(workspace / ".cycle_counter")
    counter: int | None = None
    if counter_text is not None:
        try:
            counter = int(counter_text.strip())
        except ValueError:
            warnings.append(".cycle_counter is not an integer")
    elif counter_error:
        warnings.append(f".cycle_counter: {counter_error}")
    result["cycle_counter"] = counter

    state, state_error = load_json(workspace / "state.json")
    if state_error:
        warnings.append(f"state.json: {state_error}")
        state = {}
    if not isinstance(state, dict):
        warnings.append("state.json is valid JSON but not an object")
        state = {}
    result["state"] = state

    ledger_path = workspace / "experiments.jsonl"
    entries, malformed, nonempty, ledger_error = parse_ledger(ledger_path)
    if ledger_error:
        warnings.append(f"experiments.jsonl: {ledger_error}")
    if malformed:
        warnings.append(f"experiments.jsonl: skipped {malformed} malformed/non-object line(s)")
    result["ledger"] = {
        "exists": ledger_error is None,
        "valid_entries": len(entries),
        "nonempty_lines": nonempty,
        "malformed_lines": malformed,
        "tail": entries[-max(0, args.ledger_tail):] if args.ledger_tail else [],
    }

    journal_result: dict[str, Any] = {}
    for name in ("DEAD_ENDS.md", "INSIGHTS.md"):
        path = workspace / name
        content, error = read_text(path)
        archives = sorted(p.name for p in workspace.glob(f"{path.stem}.*.bak"))
        journal_result[name] = {
            "exists": content is not None,
            "chars": len(content or ""),
            "tail": tail(content, args.journal_tail),
            "archives": archives,
        }
        if error:
            warnings.append(f"{name}: {error}")
    result["journals"] = journal_result

    key = args.metric_key or ""
    direction = args.metric_direction
    values = metric_values(entries, key)
    result["metric"] = {
        "key": key,
        "direction": direction,
        "values_seen": len(values),
        "best": direction_best(values, direction),
    }
    result["stagnation"] = stagnation(
        values, key, direction, args.threshold_cycles, args.min_delta
    )
    if args.gate_threshold is None:
        result["phase_gate"] = {"enabled": False}
    else:
        result["phase_gate"] = phase_gate(values, key, args.gate_threshold, direction)

    now = args.now if args.now is not None else time.time()
    result["safety"] = {
        "now": now,
        "fail_count": args.fail_count,
        "violations": violation_scan(
            state, args.fail_count, now, args.fail_threshold, args.stale_state_hours
        ),
    }

    cycle_times, cycle_error = load_json(workspace / ".cycle_times")
    timestamps: list[float] = []
    if cycle_error is None and cycle_times is not None:
        if isinstance(cycle_times, list):
            for value in cycle_times:
                try:
                    timestamps.append(float(value))
                except (TypeError, ValueError):
                    warnings.append(".cycle_times contains a non-numeric timestamp")
        else:
            warnings.append(".cycle_times is valid JSON but not a list")
    elif cycle_error and (workspace / ".cycle_times").exists():
        warnings.append(f".cycle_times: {cycle_error}")
    result["rate_limit"] = {
        "max_per_hour": args.max_cycles_per_hour,
        "timestamps_read": len(timestamps),
        "wait_seconds": rate_wait(timestamps, now, args.max_cycles_per_hour),
    }

    if state.get("status") == "failed":
        terminal = state.get("terminal_state") or "unknown"
        warnings.append(f"known failed state: {terminal}")
    return result, warnings


def render_text(result: dict) -> str:
    state = result["state"]
    ledger = result["ledger"]
    metric = result["metric"]
    safety = result["safety"]
    rate = result["rate_limit"]
    lines = [
        f"Project: {result['project']}",
        f"Workspace: {result['workspace']}",
        f"Cycle counter: {result['cycle_counter']}",
        f"State: {state.get('status', 'missing/unknown')}"
        + (f" (terminal={state.get('terminal_state')})" if state.get("terminal_state") else ""),
        f"Ledger: {ledger['valid_entries']} valid / {ledger['nonempty_lines']} non-empty lines; "
        f"{ledger['malformed_lines']} malformed skipped",
        f"Metric: {metric['key'] or 'not configured'} ({metric['direction']}); "
        f"{metric['values_seen']} points; best={metric['best']}",
        f"Stagnation: {result['stagnation']}",
        f"Phase gate: {result['phase_gate']}",
        f"Violations: {safety['violations'] or 'none'}",
        f"Rate limit: cap={rate['max_per_hour']}, wait={rate['wait_seconds']:.1f}s, "
        f"timestamps={rate['timestamps_read']}",
        "Journals:",
    ]
    for name, info in result["journals"].items():
        lines.append(
            f"  {name}: exists={info['exists']} chars={info['chars']} "
            f"archives={len(info['archives'])}"
        )
    if result["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in result["warnings"])
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Read-only project progress/state audit")
    p.add_argument("--project", required=True, help="Project directory to inspect")
    p.add_argument("--workspace", help="Workspace path, relative to project unless absolute")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--preview-chars", type=int, default=400)
    p.add_argument("--ledger-tail", type=int, default=5)
    p.add_argument("--journal-tail", type=int, default=800)
    p.add_argument("--metric-key", default="")
    p.add_argument("--metric-direction", choices=("higher_better", "lower_better"), default="higher_better")
    p.add_argument("--threshold-cycles", type=int, default=3)
    p.add_argument("--min-delta", type=float, default=0.0)
    p.add_argument("--gate-threshold", type=float)
    p.add_argument("--fail-count", type=int, default=0)
    p.add_argument("--fail-threshold", type=int, default=3)
    p.add_argument("--stale-state-hours", type=float, default=6.0)
    p.add_argument("--max-cycles-per-hour", type=int, default=0)
    p.add_argument("--now", type=float, help="Reference Unix time for deterministic checks")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        result, _ = inspect(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
