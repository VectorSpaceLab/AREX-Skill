#!/usr/bin/env python3
"""Read-only project brief/config validator for autonomous experiments.

This checker intentionally does not import the controller or any project code.
It never creates a workspace, launches a process, contacts a service, or writes
back to the supplied project.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


class ConfigParseError(ValueError):
    pass


def _strip_inline_comment(value: str) -> str:
    quoted = False
    quote = ""
    escaped = False
    for i, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted:
            escaped = True
            continue
        if char in ("'", '"'):
            if quoted and char == quote:
                quoted = False
            elif not quoted:
                quoted = True
                quote = char
            continue
        if char == "#" and not quoted and (i == 0 or value[i - 1].isspace()):
            return value[:i].rstrip()
    return value.strip()


def _scalar(value: str) -> Any:
    value = _strip_inline_comment(value).strip()
    lower = value.lower()
    if lower in {"true", "yes"}:
        return True
    if lower in {"false", "no"}:
        return False
    if lower in {"null", "none", "~"}:
        return None
    if value in {"[]", "{}"}:
        return json.loads(value)
    if value[:1] in {"'", '"'}:
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ConfigParseError(f"invalid quoted scalar: {value!r}") from exc
    if value[:1] in {"[", "{"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ConfigParseError(f"invalid inline collection: {value!r}") from exc
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value):
            return float(value)
    except ValueError:
        pass
    return value


def _minimal_yaml(text: str) -> dict[str, Any]:
    """Parse the simple mapping/scalar YAML used by project configs.

    This fallback is intentionally conservative. It rejects lists and complex
    YAML instead of executing or guessing at them. PyYAML, when installed, is
    preferred for a full safe_load parse.
    """
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise ConfigParseError(f"tabs are not supported at line {line_number}")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line.strip()
        if content.startswith("-"):
            raise ConfigParseError(f"list syntax requires PyYAML at line {line_number}")
        key, separator, value = content.partition(":")
        if not separator or not key.strip():
            raise ConfigParseError(f"expected key: value at line {line_number}")
        key = key.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigParseError(f"invalid indentation at line {line_number}")
        parent = stack[-1][1]
        value = _strip_inline_comment(value).strip()
        if not value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _scalar(value)
    return root


def _load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        return _minimal_yaml(text)
    try:
        parsed = yaml.safe_load(text)
    except Exception as exc:  # PyYAML exposes several parser exception types.
        raise ConfigParseError(str(exc)) from exc
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ConfigParseError("top-level config must be a mapping")
    return parsed


def _section(config: dict[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name, {})
    return value if isinstance(value, dict) else {}


def _check_int(
    issues: list[str],
    config: dict[str, Any],
    section: str,
    key: str,
    default: int,
    minimum: int,
) -> None:
    value = _section(config, section).get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        issues.append(f"{section}.{key} must be an integer >= {minimum}; got {value!r}")


def validate(project: Path, config_path: Path, config_is_explicit: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    if not project.exists() or not project.is_dir():
        errors.append(f"project directory does not exist or is not a directory: {project}")
        return {"project": str(project), "config": str(config_path), "ok": False,
                "errors": errors, "warnings": warnings, "checks": checks}
    checks.append({"name": "project_directory", "ok": True, "path": str(project)})

    brief = project / "PROJECT_BRIEF.md"
    if not brief.is_file():
        errors.append(f"missing required PROJECT_BRIEF.md: {brief}")
    else:
        try:
            text = brief.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read PROJECT_BRIEF.md: {exc}")
        else:
            if not text.strip():
                errors.append("PROJECT_BRIEF.md is empty")
            else:
                checks.append({"name": "project_brief", "ok": True,
                               "characters": len(text)})
                if len(text) > 3000:
                    warnings.append(
                        "PROJECT_BRIEF.md exceeds the default 3000-character context cap; "
                        "the controller will truncate it"
                    )
                if not re.search(r"^#{1,6}\s+goal\b", text, flags=re.IGNORECASE | re.MULTILINE):
                    warnings.append("PROJECT_BRIEF.md has no obvious '# Goal' heading")

    if not config_path.is_file():
        if config_is_explicit:
            errors.append(f"explicit config does not exist: {config_path}")
            return {"project": str(project), "config": str(config_path), "ok": False,
                    "errors": errors, "warnings": warnings, "checks": checks}
        config: dict[str, Any] = {}
        warnings.append("config.yaml is absent; built-in defaults will apply")
    else:
        try:
            config = _load_config(config_path)
        except (OSError, UnicodeError, ConfigParseError) as exc:
            errors.append(f"cannot safely parse config {config_path}: {exc}")
            return {"project": str(project), "config": str(config_path), "ok": False,
                    "errors": errors, "warnings": warnings, "checks": checks}
        checks.append({"name": "config_parse", "ok": True, "path": str(config_path)})

    project_cfg = _section(config, "project")
    workspace = project_cfg.get("workspace", "workspace")
    if not isinstance(workspace, str) or not workspace.strip():
        errors.append("project.workspace must be a non-empty string")
    else:
        checks.append({"name": "workspace_setting", "ok": True, "value": workspace})
        if workspace != "workspace":
            warnings.append(
                "non-default project.workspace: state/directives/ledger follow it, but "
                "MEMORY_LOG.md remains under the literal project workspace/"
            )
    brief_setting = project_cfg.get("brief", "PROJECT_BRIEF.md")
    if not isinstance(brief_setting, str):
        errors.append("project.brief must be a string when supplied")
    elif brief_setting != "PROJECT_BRIEF.md":
        warnings.append(
            "project.brief is not PROJECT_BRIEF.md; the controller's memory path is fixed "
            "to PROJECT_BRIEF.md, so validate that file explicitly"
        )

    execution = _section(config, "execution")
    mode = execution.get("mode", "local")
    if mode not in {"local", "ssh", "slurm"}:
        errors.append(f"execution.mode must be local, ssh, or slurm; got {mode!r}")
    elif mode in {"ssh", "slurm"}:
        for key in ("ssh_host", "remote_workspace"):
            if not isinstance(execution.get(key, ""), str) or not execution.get(key, "").strip():
                errors.append(f"execution.{key} is required when mode={mode}")
        if mode == "slurm":
            for key in ("slurm_partition", "slurm_time"):
                if not isinstance(execution.get(key, ""), str) or not execution.get(key, "").strip():
                    errors.append(f"execution.{key} is required when mode=slurm")
            warnings.append("Slurm mode uses a scheduler job id in state.pid; --gpu is ignored")
    checks.append({"name": "execution_mode", "ok": mode in {"local", "ssh", "slurm"},
                   "value": mode})

    _check_int(issues=errors, config=config, section="agent", key="max_cycles",
               default=-1, minimum=-1)
    _check_int(issues=errors, config=config, section="agent", key="max_steps_per_cycle",
               default=3, minimum=1)
    _check_int(issues=errors, config=config, section="agent", key="cooldown_interval",
               default=300, minimum=0)
    _check_int(issues=errors, config=config, section="agent", key="no_progress_fallback_threshold",
               default=3, minimum=0)
    _check_int(issues=errors, config=config, section="agent", key="max_cycles_per_hour",
               default=0, minimum=0)

    experiment = _section(config, "experiment")
    dry_run = experiment.get("mandatory_dry_run", True)
    if dry_run is not True:
        errors.append("experiment.mandatory_dry_run must be true")
    max_parallel = experiment.get("max_parallel", 1)
    if isinstance(max_parallel, bool) or not isinstance(max_parallel, int) or max_parallel < 1:
        errors.append("experiment.max_parallel must be an integer >= 1")
    elif max_parallel != 1:
        warnings.append("only one worker is supported by the operating loop; max_parallel is not a concurrency guarantee")
    checks.append({"name": "dry_run_invariant", "ok": dry_run is True,
                   "mandatory_dry_run": dry_run})

    monitor = _section(config, "monitor")
    if monitor.get("zero_llm", True) is not True:
        warnings.append("monitor.zero_llm is false; training-time monitoring may invoke LLM work")

    result = {
        "project": str(project),
        "config": str(config_path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "effective": {
            "workspace": workspace if isinstance(workspace, str) else "workspace",
            "execution_mode": mode,
            "mandatory_dry_run": dry_run,
            "max_cycles": _section(config, "agent").get("max_cycles", -1),
            "cooldown_interval": _section(config, "agent").get("cooldown_interval", 300),
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only PROJECT_BRIEF/config validator")
    parser.add_argument("--project", required=True, help="Project directory to inspect")
    parser.add_argument("--config", default="config.yaml", help="Config path relative to project")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    project = Path(args.project).expanduser()
    config_arg = Path(args.config).expanduser()
    config_path = config_arg if config_arg.is_absolute() else project / config_arg
    result = validate(project, config_path, config_is_explicit=args.config != "config.yaml")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Project: {result['project']}")
        print(f"Config:  {result['config']}")
        for check in result["checks"]:
            print(f"[OK] {check['name']}")
        for warning in result["warnings"]:
            print(f"[WARN] {warning}")
        for error in result["errors"]:
            print(f"[ERROR] {error}")
        print("Result: " + ("OK" if result["ok"] else "INVALID"))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
