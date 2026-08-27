#!/usr/bin/env python3
"""Read-only NVIDIA GPU status and conservative availability report.

This standalone helper intentionally does not import PyTorch, allocate CUDA
memory, launch processes, or start the optional keeper. Missing or unusable
nvidia-smi is reported as no detected GPU, with empty usable/free lists.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from typing import Any, Sequence

_QUERY_FIELDS = (
    "index",
    "name",
    "memory.used",
    "memory.total",
    "utilization.gpu",
    "temperature.gpu",
)
_DEFAULT_THRESHOLD_MB = 1000
_TIMEOUT_SECONDS = 10


def _run_nvidia_smi(args: Sequence[str]) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    """Run one bounded, read-only nvidia-smi command.

    Returns the completed process and no error, or ``(None, reason)`` for a
    missing executable/timeout/OS failure. No shell is used.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return None, "nvidia-smi is not installed or is not on PATH"
    except subprocess.TimeoutExpired:
        return None, f"nvidia-smi timed out after {_TIMEOUT_SECONDS} seconds"
    except OSError as exc:
        return None, f"could not execute nvidia-smi: {exc}"
    return result, None


def _failure(reason: str, threshold_mb: int, reserve_last: bool) -> dict[str, Any]:
    """Build the safe no-GPU shape used for all failed probes."""
    return {
        "detected": False,
        "reason": reason,
        "gpus": [],
        "usable_gpus": [],
        "free_gpus": [],
        "reserve_last": reserve_last,
        "last_gpu": None,
        "excluded_last_gpu": None,
        "memory_threshold_mb": threshold_mb,
    }


def _parse_status(stdout: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse the six-field nvidia-smi query, rejecting incomplete rows."""
    rows: list[dict[str, Any]] = []
    for line_number, fields in enumerate(csv.reader(stdout.splitlines()), start=1):
        if not any(field.strip() for field in fields):
            continue
        if len(fields) < len(_QUERY_FIELDS):
            return [], f"nvidia-smi returned an incomplete status row at line {line_number}"
        try:
            row = {
                "gpu_id": int(fields[0].strip()),
                "name": fields[1].strip(),
                "memory_used_mb": int(fields[2].strip()),
                "memory_total_mb": int(fields[3].strip()),
                "utilization_pct": int(fields[4].strip()),
                "temperature_c": int(fields[5].strip()),
            }
        except (TypeError, ValueError):
            return [], f"nvidia-smi returned non-numeric status data at line {line_number}"
        rows.append(row)
    if not rows:
        return [], "nvidia-smi returned no GPU status rows"
    return rows, None


def probe(threshold_mb: int = _DEFAULT_THRESHOLD_MB, reserve_last: bool = True) -> dict[str, Any]:
    """Return a detailed, read-only status and selection report.

    ``threshold_mb`` uses the package's strict predicate: a GPU is free only
    when reported used memory is less than this value. ``reserve_last`` keeps
    the only GPU usable, but excludes the final enumerated GPU when multiple
    GPUs are detected.
    """
    discovery, error = _run_nvidia_smi(["-L"])
    if error:
        return _failure(error, threshold_mb, reserve_last)
    assert discovery is not None
    if discovery.returncode != 0:
        detail = (discovery.stderr or discovery.stdout or "non-zero exit").strip()
        return _failure(f"nvidia-smi GPU discovery failed: {detail[:240]}", threshold_mb, reserve_last)
    discovery_lines = [line for line in discovery.stdout.splitlines() if line.strip()]
    if not discovery_lines:
        return _failure("nvidia-smi reported no GPUs", threshold_mb, reserve_last)

    query_args = [
        "--query-gpu=" + ",".join(_QUERY_FIELDS),
        "--format=csv,noheader,nounits",
    ]
    status, error = _run_nvidia_smi(query_args)
    if error:
        return _failure(error, threshold_mb, reserve_last)
    assert status is not None
    if status.returncode != 0:
        detail = (status.stderr or status.stdout or "non-zero exit").strip()
        return _failure(f"nvidia-smi status query failed: {detail[:240]}", threshold_mb, reserve_last)
    rows, parse_error = _parse_status(status.stdout)
    if parse_error:
        return _failure(parse_error, threshold_mb, reserve_last)

    # Match the package detector: discovery enumerates non-empty -L lines as
    # zero-based IDs. Status rows remain authoritative for the free predicate.
    detected_ids = list(range(len(discovery_lines)))
    last_gpu = detected_ids[-1]
    excluded_last_gpu = last_gpu if reserve_last and len(detected_ids) > 1 else None
    usable = detected_ids[:-1] if excluded_last_gpu is not None else detected_ids
    status_by_id = {row["gpu_id"]: row for row in rows}
    free = [
        gpu_id
        for gpu_id in usable
        if gpu_id in status_by_id
        and status_by_id[gpu_id]["memory_used_mb"] < threshold_mb
    ]
    return {
        "detected": True,
        "reason": "ok",
        "gpus": rows,
        "usable_gpus": usable,
        "free_gpus": free,
        "reserve_last": reserve_last,
        "last_gpu": last_gpu,
        "excluded_last_gpu": excluded_last_gpu,
        "memory_threshold_mb": threshold_mb,
    }


def _human(report: dict[str, Any]) -> str:
    """Render a stable human-readable report without probing again."""
    if not report["detected"]:
        return "\n".join(
            [
                f"No GPU detected: {report['reason']}",
                "Usable GPUs: []",
                "Free GPUs: []",
            ]
        )

    lines = ["GPU Status", "GPU  Name                         Memory (MB)       Util  Temp (C)"]
    lines.append("-" * 72)
    for gpu in report["gpus"]:
        memory = f"{gpu['memory_used_mb']}/{gpu['memory_total_mb']}"
        lines.append(
            f"{gpu['gpu_id']:>3}  {gpu['name']:<28.28} {memory:>15}"
            f" {gpu['utilization_pct']:>5}% {gpu['temperature_c']:>8}"
        )
    if report["excluded_last_gpu"] is None:
        reserve_note = "none (one-GPU edge case or reserve_last=false)"
    else:
        reserve_note = str(report["excluded_last_gpu"])
    lines.extend(
        [
            f"Usable GPUs: {report['usable_gpus']}",
            f"Free GPUs (< {report['memory_threshold_mb']} MB used): {report['free_gpus']}",
            f"Excluded last GPU: {reserve_note}",
            "Note: selection is advisory; it is not an OS/scheduler reservation.",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only NVIDIA GPU status; no CUDA allocation or keeper is started."
    )
    parser.add_argument(
        "--memory-threshold-mb",
        type=int,
        default=_DEFAULT_THRESHOLD_MB,
        metavar="MB",
        help="free if used memory is strictly below MB (default: 1000)",
    )
    parser.add_argument(
        "--no-reserve-last",
        action="store_true",
        help="include the last GPU when multiple GPUs are visible",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the report as JSON instead of a table",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.memory_threshold_mb < 0:
        parser.error("--memory-threshold-mb must be non-negative")
    report = probe(
        threshold_mb=args.memory_threshold_mb,
        reserve_last=not args.no_reserve_last,
    )
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(_human(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
