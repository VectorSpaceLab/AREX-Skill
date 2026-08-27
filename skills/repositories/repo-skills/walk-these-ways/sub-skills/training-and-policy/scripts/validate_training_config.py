#!/usr/bin/env python3
"""Read-only PPO/CSE dimension checker with no repository imports.

It accepts explicit numeric dimensions or a small JSON/YAML-like config file.
The YAML-like reader intentionally supports only mappings and scalar values; it
never evaluates Python, imports yaml, or executes configuration code.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ALIASES = {
    "num_obs": ("num_obs", "num_observations"),
    "num_privileged_obs": ("num_privileged_obs", "privileged_obs", "privileged_observations"),
    "history_length": ("history_length", "num_observation_history", "obs_history_length"),
    "num_obs_history": ("num_obs_history", "num_observations_history", "observation_history_width"),
    "num_actions": ("num_actions", "actions", "action_dim"),
}


def error(message: str) -> "NoReturn":
    raise ValueError(message)


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    if value.startswith(("\"", "'")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            error(f"invalid quoted scalar {value!r}: {exc}")
    if value.startswith(("[", "{")):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            error(f"invalid JSON scalar {value!r}: {exc}")
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        number = float(value) if any(c in value for c in ".eE") else int(value)
        return number
    except ValueError:
        return value


def strip_comment(line: str) -> str:
    quote = None
    for index, char in enumerate(line):
        if char in "\"'":
            quote = None if quote == char else (char if quote is None else quote)
        elif char == "#" and quote is None and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
    return line.rstrip()


def parse_yaml_like(text: str) -> Dict[str, Any]:
    """Parse a deliberately small indentation-based mapping format."""
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]
    for lineno, original in enumerate(text.splitlines(), 1):
        if "\t" in original:
            error(f"line {lineno}: tabs are not supported in YAML-like input")
        line = strip_comment(original)
        if not line.strip() or line.lstrip().startswith("---"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if ":" not in content:
            error(f"line {lineno}: expected key: value")
        key, raw = content.split(":", 1)
        key = key.strip().strip("\"'")
        if not key or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key):
            error(f"line {lineno}: invalid key {key!r}")
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if key in parent:
            error(f"line {lineno}: duplicate key {key!r}")
        if raw.strip():
            parent[key] = parse_scalar(raw)
        else:
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def load_config(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        error(f"config is not a regular file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"cannot read config {path}: {exc}")
    if not text.strip():
        error(f"config is empty: {path}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = parse_yaml_like(text)
    if not isinstance(parsed, dict):
        error("config root must be a mapping/object")
    return parsed


def walk_items(value: Any, path: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from walk_items(child, child_path)
    else:
        yield path, value


def find_value(config: Dict[str, Any], names: Iterable[str]) -> Tuple[Any, str] | Tuple[None, None]:
    wanted = {name.lower() for name in names}
    for path, value in walk_items(config):
        if path.rsplit(".", 1)[-1].lower() in wanted:
            return value, path
    return None, None


def positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        error(f"{name} must be a positive integer, got {value!r}")
    if not math.isfinite(float(value)) or int(value) != value or int(value) <= 0:
        error(f"{name} must be a positive integer, got {value!r}")
    return int(value)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate PPO/PPO-CSE observation, history, privileged, and action dimensions without importing the repo."
    )
    parser.add_argument("--config", type=Path, help="JSON or simple indentation-based YAML-like mapping")
    parser.add_argument("--num-obs", type=int, help="current scalar observation width")
    parser.add_argument("--num-privileged-obs", type=int, help="privileged observation/latent width")
    parser.add_argument("--history-length", type=int, help="number of observation frames in history")
    parser.add_argument("--num-obs-history", type=int, help="flattened observation-history width")
    parser.add_argument("--num-actions", type=int, help="action width")
    parser.add_argument("--batch-size", type=int, default=2, help="synthetic batch size to report (default: 2)")
    parser.add_argument("--json", action="store_true", help="emit a JSON summary")
    args = parser.parse_args(argv)

    try:
        config: Dict[str, Any] = load_config(args.config) if args.config else {}
        explicit = {
            "num_obs": args.num_obs,
            "num_privileged_obs": args.num_privileged_obs,
            "history_length": args.history_length,
            "num_obs_history": args.num_obs_history,
            "num_actions": args.num_actions,
        }
        values: Dict[str, int] = {}
        sources: Dict[str, str] = {}
        for name, supplied in explicit.items():
            if supplied is not None:
                values[name] = positive_int(name, supplied)
                sources[name] = "cli"
            else:
                found, source = find_value(config, ALIASES[name])
                if found is not None:
                    values[name] = positive_int(name, found)
                    sources[name] = source or "config"

        # The checked-in CSE recipe is the safe default when no fields were supplied.
        if not values:
            values = {"num_obs": 70, "num_privileged_obs": 2, "history_length": 30,
                      "num_obs_history": 2100, "num_actions": 12}
            sources = {key: "checked-in-default" for key in values}

        if "num_obs" not in values:
            error("missing num_obs/num_observations (use --num-obs or --config)")
        if "num_privileged_obs" not in values:
            error("missing num_privileged_obs (use --num-privileged-obs or --config)")
        if "num_actions" not in values:
            error("missing num_actions (use --num-actions or --config)")
        if "history_length" not in values and "num_obs_history" not in values:
            error("provide history length or flattened history width")

        if "history_length" in values and "num_obs_history" in values:
            expected = values["history_length"] * values["num_obs"]
            if expected != values["num_obs_history"]:
                error(f"history mismatch: {values['history_length']} * {values['num_obs']} = {expected}, not {values['num_obs_history']}")
        elif "history_length" in values:
            width = values["history_length"] * values["num_obs"]
            values["num_obs_history"] = width
            sources["num_obs_history"] = "derived"
        else:
            width = values["num_obs_history"]
            if width % values["num_obs"]:
                error(f"flattened history width {width} is not divisible by num_obs {values['num_obs']}")
            values["history_length"] = width // values["num_obs"]
            sources["history_length"] = "derived"

        batch_size = positive_int("batch_size", args.batch_size)
        summary = {
            "ok": True,
            "dimensions": {
                "num_obs": values["num_obs"],
                "num_privileged_obs": values["num_privileged_obs"],
                "history_length": values["history_length"],
                "num_obs_history": values["num_obs_history"],
                "num_actions": values["num_actions"],
                "batch_size": batch_size,
                "cse_body_input": values["num_obs_history"] + values["num_privileged_obs"],
            },
            "sources": sources,
            "contract": {
                "adaptation_input": [batch_size, values["num_obs_history"]],
                "latent": [batch_size, values["num_privileged_obs"]],
                "body_input": [batch_size, values["num_obs_history"] + values["num_privileged_obs"]],
                "action": [batch_size, values["num_actions"]],
            },
        }
        if args.json:
            print(json.dumps(summary, sort_keys=True))
        else:
            dims = summary["dimensions"]
            print("OK: num_obs={num_obs}, privileged={num_privileged_obs}, history={num_obs_history} ({history_length} frames), actions={num_actions}".format(**dims))
            print("CSE contract: adaptation ({0}, {1}) -> latent ({0}, {2}) -> body ({0}, {3}) -> action ({0}, {4})".format(batch_size, dims["num_obs_history"], dims["num_privileged_obs"], dims["cse_body_input"], dims["num_actions"]))
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
