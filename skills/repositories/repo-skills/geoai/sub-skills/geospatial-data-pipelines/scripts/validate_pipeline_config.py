#!/usr/bin/env python3
"""Validate a GeoAI pipeline config without running it.

Safe by default:
- no downloads
- no model loading or inference
- no file writes
- no credential use

The script parses a JSON/YAML pipeline config, loads it through the bundled
GeoAI pipeline loader, prints the registered step types, and can compare the
config against an existing checkpoint file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _load_raw_config(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text())
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "PyYAML is required to read YAML pipeline configs. "
                "Install pyyaml or use JSON."
            ) from exc

        data = yaml.safe_load(path.read_text())
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError("Pipeline config must be a mapping at the top level")
        return data
    raise ValueError("Unsupported config format. Use .json, .yaml, or .yml")


def _get_step_types(raw_config: Dict[str, Any]) -> List[str]:
    steps = raw_config.get("steps", [])
    if not isinstance(steps, list):
        return []
    result = []
    for step in steps:
        if isinstance(step, dict) and "type" in step:
            result.append(str(step["type"]))
    return result


def _read_checkpoint(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Checkpoint file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Checkpoint file is not valid JSON: {path}") from exc


def _format_step_summary(step: Dict[str, Any]) -> str:
    step_type = step.get("type", "<missing>")
    name = step.get("name", step_type)
    extras = []
    for key in sorted(step):
        if key in {"type", "name"}:
            continue
        value = step[key]
        if isinstance(value, (str, int, float, bool)):
            extras.append(f"{key}={value!r}")
        elif isinstance(value, list):
            extras.append(f"{key}=[{', '.join(repr(v) for v in value[:4])}{'...' if len(value) > 4 else ''}]")
        else:
            extras.append(f"{key}=<{type(value).__name__}>")
    extra_text = ", ".join(extras)
    if extra_text:
        return f"- {name}: {step_type} ({extra_text})"
    return f"- {name}: {step_type}"


def _summarize_pipeline(pipe: Any) -> Dict[str, Any]:
    return {
        "name": getattr(pipe, "name", None),
        "max_workers": getattr(pipe, "max_workers", None),
        "on_error": getattr(getattr(pipe, "on_error", None), "value", None),
        "checkpoint_dir": getattr(pipe, "checkpoint_dir", None),
        "step_types": [step.__class__.__name__ for step in getattr(pipe, "steps", [])],
        "steps": [
            {
                "type": step.__class__.__name__,
                "name": getattr(step, "name", step.__class__.__name__),
                "fields": {
                    key: value
                    for key, value in vars(step).items()
                    if not key.startswith("_") and key != "name"
                },
            }
            for step in getattr(pipe, "steps", [])
        ],
        "config_hash": pipe._config_hash() if hasattr(pipe, "_config_hash") else None,
    }


def _compare_checkpoint(pipe: Any, checkpoint_path: Path) -> Dict[str, Any]:
    checkpoint = _read_checkpoint(checkpoint_path)
    config_hash = pipe._config_hash() if hasattr(pipe, "_config_hash") else None
    stored_hash = checkpoint.get("config_hash")
    entries = checkpoint.get("entries", {}) if isinstance(checkpoint, dict) else {}

    counts = {"pending": 0, "completed": 0, "failed": 0, "skipped": 0}
    if isinstance(entries, dict):
        for entry in entries.values():
            if isinstance(entry, dict):
                status = str(entry.get("status", "")).lower()
                if status in counts:
                    counts[status] += 1

    return {
        "checkpoint_path": str(checkpoint_path),
        "stored_config_hash": stored_hash,
        "current_config_hash": config_hash,
        "hash_matches": bool(stored_hash) and stored_hash == config_hash,
        "counts": counts,
        "entry_count": len(entries) if isinstance(entries, dict) else 0,
    }


def _print_text_report(summary: Dict[str, Any]) -> None:
    print(f"Pipeline: {summary.get('name') or '<unnamed>'}")
    print(f"Workers: {summary.get('max_workers')}")
    print(f"On error: {summary.get('on_error')}")
    if summary.get("checkpoint_dir"):
        print(f"Checkpoint dir: {summary.get('checkpoint_dir')}")
    print(f"Step count: {len(summary.get('step_types', []))}")
    for step in summary.get("steps", []):
        print(_format_step_summary(step))


def _print_checkpoint_report(info: Dict[str, Any]) -> None:
    print(f"Checkpoint: {info['checkpoint_path']}")
    print(f"Entries: {info['entry_count']}")
    print(
        "Status counts: "
        f"pending={info['counts']['pending']} "
        f"completed={info['counts']['completed']} "
        f"failed={info['counts']['failed']} "
        f"skipped={info['counts']['skipped']}"
    )
    if info["stored_config_hash"]:
        print(f"Stored config hash: {info['stored_config_hash']}")
    if info["current_config_hash"]:
        print(f"Current config hash: {info['current_config_hash']}")
    print(f"Checkpoint matches config: {info['hash_matches']}")


def _print_unknown_step_help(step_types: Iterable[str], registered: Iterable[str]) -> None:
    step_types = list(step_types)
    registered = list(registered)
    unknown = [name for name in step_types if name not in registered]

    if not unknown:
        return

    print("\nUnknown or unsupported step types detected:", file=sys.stderr)
    for name in unknown:
        print(f"- {name}", file=sys.stderr)
    print("Registered config step types:", file=sys.stderr)
    for name in registered:
        print(f"- {name}", file=sys.stderr)
    if "FunctionStep" in unknown:
        print(
            "Note: FunctionStep is a Python helper but is not registered for JSON/YAML configs.",
            file=sys.stderr,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a GeoAI JSON/YAML pipeline config without running it.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        type=Path,
        help="Path to a JSON or YAML GeoAI pipeline config.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Optional checkpoint JSON file to compare against the config hash.",
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="Print the registered config step types and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the validation summary as JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a nonzero exit code if warnings are emitted.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config is None and not args.list_steps:
        parser.error("the following arguments are required: config")

    # Import GeoAI only after argument parsing so --help stays dependency-light.
    try:
        from geoai.pipeline import _STEP_REGISTRY, load_pipeline
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Error: could not import geoai.pipeline: {exc}", file=sys.stderr)
        return 1

    registered_steps = sorted(_STEP_REGISTRY)

    if args.list_steps:
        for name in registered_steps:
            print(name)
        return 0

    try:
        raw_config = _load_raw_config(args.config)
        pipe = load_pipeline(str(args.config))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        try:
            raw_config = _load_raw_config(args.config)
        except Exception:
            raw_config = {}
        step_types = _get_step_types(raw_config)
        _print_unknown_step_help(step_types, registered_steps)
        return 2

    summary = _summarize_pipeline(pipe)
    if args.checkpoint:
        try:
            checkpoint_info = _compare_checkpoint(pipe, args.checkpoint)
        except Exception as exc:
            print(f"Error reading checkpoint: {exc}", file=sys.stderr)
            return 2
        summary["checkpoint"] = checkpoint_info

    step_types = summary.get("step_types", [])
    unknown_steps = [name for name in step_types if name not in registered_steps]

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        _print_text_report(summary)
        if args.checkpoint:
            print()
            _print_checkpoint_report(summary["checkpoint"])
        if unknown_steps:
            _print_unknown_step_help(step_types, registered_steps)

    if args.strict and (unknown_steps or (args.checkpoint and not summary["checkpoint"]["hash_matches"])):
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
