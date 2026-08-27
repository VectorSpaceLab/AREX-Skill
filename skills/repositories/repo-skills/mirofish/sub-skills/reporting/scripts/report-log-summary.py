#!/usr/bin/env python3
"""Summarize a MiroFish report artifact directory.

The script is standalone and safe. It reads optional report files such as
progress.json, outline.json, meta.json, agent_log.jsonl, console_log.txt,
section_*.md, and full_report.md, then prints a compact JSON summary. It never
calls the backend or mutates the report directory.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable


def load_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # pragma: no cover - CLI error path
        return None, f"invalid: {exc}"


def count_jsonl(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"exists": path.exists(), "lines": 0, "invalid_lines": 0, "event_counts": {}}
    if not path.exists():
        return result
    counts: dict[str, int] = {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            result["lines"] += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                result["invalid_lines"] += 1
                continue
            event = payload.get("event") or payload.get("type") or payload.get("status") or "unknown"
            counts[str(event)] = counts.get(str(event), 0) + 1
    result["event_counts"] = counts
    return result


def text_tail(path: Path, max_lines: int) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "lines": 0, "tail": []}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"exists": True, "lines": len(lines), "tail": lines[-max_lines:]}


def summarize(report_dir: Path, tail: int = 5) -> dict[str, Any]:
    summary: dict[str, Any] = {"report_dir": str(report_dir), "exists": report_dir.exists()}
    if not report_dir.exists():
        summary["error"] = "report directory does not exist"
        return summary

    for name in ("progress.json", "outline.json", "meta.json"):
        payload, error = load_json(report_dir / name)
        key = name[:-5]
        if error:
            summary[key] = {"present": False, "error": error}
        else:
            summary[key] = {"present": True, "data": payload}

    sections = []
    for path in sorted(report_dir.glob("section_*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        first_heading = next((line.strip() for line in text.splitlines() if line.strip().startswith("#")), "")
        sections.append({"file": path.name, "bytes": path.stat().st_size, "first_heading": first_heading})
    summary["sections"] = sections

    full = report_dir / "full_report.md"
    summary["full_report"] = {"exists": full.exists(), "bytes": full.stat().st_size if full.exists() else 0}
    summary["agent_log"] = count_jsonl(report_dir / "agent_log.jsonl")
    summary["console_log"] = text_tail(report_dir / "console_log.txt", tail)
    return summary


def make_self_test_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="mirofish-report-summary-"))
    (tmp / "progress.json").write_text(json.dumps({"status": "completed", "steps": ["planning_complete", "report_complete"]}), encoding="utf-8")
    (tmp / "outline.json").write_text(json.dumps({"sections": [{"title": "Overview"}]}), encoding="utf-8")
    (tmp / "meta.json").write_text(json.dumps({"report_id": "rep_selftest", "simulation_id": "sim_selftest"}), encoding="utf-8")
    (tmp / "section_01.md").write_text("# Overview\n\nSelf-test section.\n", encoding="utf-8")
    (tmp / "full_report.md").write_text("# Full Report\n\nSelf-test.\n", encoding="utf-8")
    (tmp / "agent_log.jsonl").write_text(json.dumps({"event": "planning_complete"}) + "\n" + json.dumps({"event": "report_complete"}) + "\n", encoding="utf-8")
    (tmp / "console_log.txt").write_text("starting\ncompleted\n", encoding="utf-8")
    return tmp


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a MiroFish report artifact directory.")
    parser.add_argument("report_dir", nargs="?", help="directory containing report files")
    parser.add_argument("--tail", type=int, default=5, help="number of console-log tail lines to include")
    parser.add_argument("--self-test", action="store_true", help="summarize a generated temporary report directory")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.self_test:
        report_dir = make_self_test_dir()
    elif args.report_dir:
        report_dir = Path(args.report_dir)
    else:
        parser.error("provide report_dir or --self-test")

    print(json.dumps(summarize(report_dir, args.tail), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
