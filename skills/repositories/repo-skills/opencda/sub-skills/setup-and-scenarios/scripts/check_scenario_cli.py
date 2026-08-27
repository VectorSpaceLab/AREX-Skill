#!/usr/bin/env python3
"""Safely inspect OpenCDA scenario/CLI files without launching simulation.

This checker intentionally uses only the standard library. It does not import
OpenCDA, CARLA, OmegaConf, scenario modules, or execute repository code.
"""

from __future__ import print_function

import argparse
import ast
import json
import sys
from pathlib import Path


SCRIPT_NAME = "check_scenario_cli.py"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Static OpenCDA scenario/CLI inspection; never launches CARLA, "
            "SUMO, or a scenario."
        )
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="OpenCDA repository root to inspect (may be absolute or relative).",
    )
    parser.add_argument(
        "--scenario",
        help="Optional exact scenario stem to validate instead of all pairs.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit a machine-readable report.",
    )
    return parser.parse_args()


def has_run_scenario(path):
    """Return (has_function, syntax_error) using AST only."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run_scenario":
            return True, None
    return False, None


def inspect_repo(root, requested):
    result = {
        "repo_root": str(root),
        "cli": {"path": "opencda.py", "exists": False, "syntax_ok": False},
        "scenarios": [],
        "errors": [],
        "warnings": [],
        "safe": True,
    }

    cli = root / "opencda.py"
    result["cli"]["exists"] = cli.is_file()
    if not cli.is_file():
        result["errors"].append("missing opencda.py")
    else:
        try:
            ast.parse(cli.read_text(encoding="utf-8"), filename=str(cli))
            result["cli"]["syntax_ok"] = True
        except (OSError, SyntaxError, UnicodeError) as exc:
            result["errors"].append("opencda.py is not parseable: %s" % exc)

    scenario_dir = root / "opencda" / "scenario_testing"
    config_dir = scenario_dir / "config_yaml"
    if not scenario_dir.is_dir():
        result["errors"].append("missing opencda/scenario_testing")
        return result
    if not config_dir.is_dir():
        result["errors"].append("missing opencda/scenario_testing/config_yaml")
        return result

    modules = {
        path.stem: path
        for path in scenario_dir.glob("*.py")
        if path.name != "__init__.py"
    }
    configs = {
        path.stem: path
        for path in config_dir.glob("*.yaml")
        if path.name != "default.yaml"
    }
    names = [requested] if requested else sorted(set(modules) | set(configs))

    for name in names:
        if not name or Path(name).name != name or "/" in name or "\\" in name:
            result["errors"].append("invalid scenario name: %r" % name)
            continue
        module = modules.get(name)
        config = configs.get(name)
        entry = {
            "name": name,
            "module": module is not None,
            "config": config is not None,
            "run_scenario": False,
            "module_syntax_error": None,
        }
        if module is not None:
            entry["run_scenario"], entry["module_syntax_error"] = has_run_scenario(module)
            if entry["module_syntax_error"]:
                result["errors"].append(
                    "%s module parse failure: %s" % (name, entry["module_syntax_error"])
                )
            elif not entry["run_scenario"]:
                result["errors"].append("%s module lacks run_scenario" % name)
        if module is None or config is None:
            missing = []
            if module is None:
                missing.append("module")
            if config is None:
                missing.append("config")
            result["errors"].append("%s missing %s" % (name, " and ".join(missing)))
        result["scenarios"].append(entry)

    if requested and requested not in modules and requested not in configs:
        result["errors"].append("unknown scenario: %s" % requested)
    else:
        orphan_modules = sorted(set(modules) - set(configs))
        orphan_configs = sorted(set(configs) - set(modules))
        if not requested:
            if orphan_modules:
                result["warnings"].append("module without YAML: %s" % ", ".join(orphan_modules))
            if orphan_configs:
                result["warnings"].append("YAML without module: %s" % ", ".join(orphan_configs))

    result["safe"] = not result["errors"]
    return result


def main():
    args = parse_args()
    root = args.repo_root.expanduser().resolve()
    if not root.is_dir():
        report = {
            "repo_root": str(root),
            "scenarios": [],
            "errors": ["repository root is not a directory: %s" % root],
            "warnings": [],
            "safe": False,
        }
    else:
        report = inspect_repo(root, args.scenario)

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OpenCDA static scenario check: %s" % report["repo_root"])
        cli = report.get("cli")
        if cli:
            print("CLI: exists=%s syntax_ok=%s" % (cli["exists"], cli["syntax_ok"]))
        for entry in report.get("scenarios", []):
            print(
                "SCENARIO %-42s module=%s config=%s run_scenario=%s"
                % (entry["name"], entry["module"], entry["config"], entry["run_scenario"])
            )
        for warning in report.get("warnings", []):
            print("WARNING: %s" % warning)
        for error in report.get("errors", []):
            print("ERROR: %s" % error, file=sys.stderr)
        if report.get("safe"):
            print("PASS: static inspection only; no simulation was launched.")
        else:
            print("FAIL: repair the reported static issues before running a scenario.")
    return 0 if report.get("safe") else 1


if __name__ == "__main__":
    sys.exit(main())
