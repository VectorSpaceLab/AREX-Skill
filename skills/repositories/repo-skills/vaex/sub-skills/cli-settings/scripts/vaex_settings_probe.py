#!/usr/bin/env python3
"""Read-only Vaex settings probe with explicit opt-in persistence.

By default this script imports the installed public Vaex package, prints effective
settings plus a field/environment-variable map, and optionally applies runtime
only `--set dotted.path=value` overrides for the current process. It does not
write Vaex user configuration unless both `--save` and `--yes` are supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_KEYS = [
    "main.thread_count",
    "main.thread_count_io",
    "display.max_columns",
    "display.max_rows",
    "cache.type",
    "cache.memory_size_limit",
    "cache.disk_size_limit",
    "cache.path",
    "data.path",
    "fs.path",
    "main.progress.type",
    "main.logging.setup",
    "server.add_example",
    "server.graphql",
]


PREFIX_HINTS = {
    "main": "vaex_",
    "display": "vaex_display_",
    "cache": "vaex_cache_",
    "chunk": "vaex_chunk_",
    "data": "vaex_data_",
    "fs": "vaex_fs_",
    "progress": "vaex_progress_",
    "logging": "vaex_logging_",
    "memory_tracker": "vaex_memory_tracker_",
    "task_tracker": "vaex_task_tracker_",
    "server": "vaex_server_",
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect effective Vaex settings and env-var mappings; read-only unless --save --yes is provided."
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        default=DEFAULT_KEYS,
        help="Dotted setting keys to summarize. Default: common execution/display/cache/server keys.",
    )
    parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Apply a runtime-only setting override before printing, e.g. --set main.thread_count=4. Repeatable. Does not persist unless --save --yes is used.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist effective settings with vaex.settings.save(exclude_defaults=True). Requires --yes. Mutates Vaex home YAML.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm that --save is allowed to mutate Vaex user configuration.",
    )
    parser.add_argument(
        "--include-full",
        action="store_true",
        help="Include the full effective settings dictionary in the JSON report.",
    )
    parser.add_argument(
        "--include-environ-values",
        action="store_true",
        help="Include current values of VAEX_* environment variables in the report. Off by default to avoid leaking private paths/tokens.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args(argv)


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return str(value)


def settings_dict(settings_obj: Any) -> Dict[str, Any]:
    try:
        return settings_obj.dict(by_alias=True)
    except TypeError:
        return settings_obj.dict()


def get_child(root: Any, key: str) -> Any:
    if key == "main":
        import vaex  # imported lazily after env is fixed by caller

        return vaex.settings.main
    if key == "server":
        import vaex

        return getattr(vaex.settings, "server", getattr(vaex.settings.main, "server", None))
    return getattr(root, key)


def resolve_dotted(key: str) -> Tuple[Any, str, Any]:
    import vaex

    parts = key.split(".")
    if not parts or not parts[0]:
        raise ValueError(f"Invalid setting key {key!r}")
    obj: Any = get_child(vaex.settings, parts[0])
    if obj is None:
        raise AttributeError(f"Settings object {parts[0]!r} is not available")
    for part in parts[1:-1]:
        obj = getattr(obj, part)
    leaf = parts[-1]
    return obj, leaf, getattr(obj, leaf)


def convert_like(current: Any, raw: str) -> Any:
    if current is None:
        if raw.lower() in {"none", "null"}:
            return None
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        if raw.lower() in {"true", "false"}:
            return raw.lower() == "true"
        return raw
    if isinstance(current, bool):
        if raw.lower() in {"true", "1", "yes", "on"}:
            return True
        if raw.lower() in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"Cannot parse boolean value {raw!r}")
    if isinstance(current, int) and not isinstance(current, bool):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    if isinstance(current, (dict, list)):
        return json.loads(raw)
    return raw


def apply_sets(assignments: Iterable[str]) -> List[Dict[str, Any]]:
    applied: List[Dict[str, Any]] = []
    for assignment in assignments:
        if "=" not in assignment:
            raise ValueError(f"Expected KEY=VALUE for --set, got {assignment!r}")
        key, raw = assignment.split("=", 1)
        obj, leaf, old = resolve_dotted(key)
        new_value = convert_like(old, raw)
        setattr(obj, leaf, new_value)
        applied.append({"key": key, "old": old, "new": new_value, "persisted": False})
    return applied


def field_env_name(settings_obj: Any, field_name: str, group: str) -> Optional[str]:
    fields = getattr(settings_obj, "__fields__", {}) or {}
    field = fields.get(field_name)
    if field is None:
        return None
    extra = getattr(getattr(field, "field_info", field), "extra", {}) or {}
    env_names = list(extra.get("env_names") or [])
    if env_names:
        return str(env_names[0]).upper()
    explicit = getattr(field, "env", None)
    if explicit:
        return str(explicit).upper()
    prefix = getattr(getattr(settings_obj, "Config", None), "env_prefix", PREFIX_HINTS.get(group, "vaex_"))
    alias = getattr(field, "alias", field_name) or field_name
    return f"{prefix}{alias}".upper()


def env_map_for_object(group: str, settings_obj: Any, python_prefix: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    fields = getattr(settings_obj, "__fields__", {}) or {}
    for name, field in fields.items():
        try:
            value = getattr(settings_obj, name)
        except Exception as exc:  # noqa: BLE001
            result[name] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        if hasattr(value, "__fields__"):
            continue
        result[name] = {
            "env": field_env_name(settings_obj, name, group),
            "title": getattr(field, "title", None),
            "value": value,
            "python": f"vaex.settings.{python_prefix}.{name}",
        }
    return result


def build_env_map() -> Dict[str, Dict[str, Dict[str, Any]]]:
    import vaex

    groups: Dict[str, Tuple[Any, str]] = {
        "main": (vaex.settings.main, "main"),
        "display": (getattr(vaex.settings, "display", None), "display"),
        "cache": (getattr(vaex.settings, "cache", None), "cache"),
        "data": (getattr(vaex.settings, "data", None), "data"),
        "fs": (getattr(vaex.settings, "fs", None), "fs"),
    }
    for nested_name in ["chunk", "progress", "logging", "memory_tracker", "task_tracker"]:
        groups[nested_name] = (getattr(vaex.settings.main, nested_name, None), f"main.{nested_name}")
    groups["server"] = (getattr(vaex.settings, "server", getattr(vaex.settings.main, "server", None)), "server")

    return {
        name: env_map_for_object(name, obj, python_prefix)
        for name, (obj, python_prefix) in groups.items()
        if obj is not None
    }


def summarize_keys(keys: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    summary: Dict[str, Dict[str, Any]] = {}
    for key in keys:
        try:
            obj, leaf, value = resolve_dotted(key)
            group = key.split(".")[0]
            summary[key] = {
                "value": value,
                "env": field_env_name(obj, leaf, group),
                "type": type(value).__name__,
            }
        except Exception as exc:  # noqa: BLE001
            summary[key] = {"error": f"{type(exc).__name__}: {exc}"}
    return summary


def current_vaex_environ(include_values: bool) -> Any:
    names = sorted(name for name in os.environ if name.upper().startswith("VAEX_"))
    if include_values:
        return {name: os.environ.get(name) for name in names}
    return names


def run_probe(args: argparse.Namespace) -> Dict[str, Any]:
    if args.save and not args.yes:
        raise SystemExit("Refusing to save settings without --yes. Default mode is read-only.")

    import vaex

    applied = apply_sets(args.sets)
    report: Dict[str, Any] = {
        "ok": True,
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "read_only": not args.save,
        "applied_runtime_sets": applied,
        "selected": summarize_keys(args.keys),
        "env_map": build_env_map(),
        "vaex_environ": current_vaex_environ(args.include_environ_values),
        "vaex_home_env_set": "VAEX_HOME" in os.environ,
        "legacy_vaex_path_home_env_set": "VAEX_PATH_HOME" in os.environ,
        "settings_notes": [
            "Environment variables must be set before importing Vaex or launching a vaex CLI process.",
            "The implementation reads/writes main.yml in Vaex home; some older docs say main.yaml.",
            "Use --save --yes only after approving mutation of Vaex user configuration.",
        ],
    }
    if args.include_full:
        report["effective_settings"] = settings_dict(vaex.settings.main)

    if args.save:
        # This intentionally calls the public save helper. It may fail in Vaex
        # versions whose lightweight settings object does not support
        # exclude_defaults; surface that failure to the caller instead of falling
        # back to a silent custom writer.
        vaex.settings.save(exclude_defaults=True, verbose=False)
        for item in applied:
            item["persisted"] = True
        report["read_only"] = False
        report["saved"] = True
    else:
        report["saved"] = False
    return report


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = run_probe(args)
        if args.json:
            print(json.dumps(report, default=json_default, indent=2 if args.pretty else None, sort_keys=True))
        else:
            print("Vaex settings probe", "passed" if report.get("ok") else "failed")
            print(json.dumps(report, default=json_default, indent=2, sort_keys=True))
        return 0 if report.get("ok") else 1
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        failure = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(failure, indent=2 if args.pretty else None, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
