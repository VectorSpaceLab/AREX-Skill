#!/usr/bin/env python3
"""Check whether the current Python environment can use Snips NLU safely.

This helper performs read-only checks: imports, package/model version, CLI help,
and optional local language-resource availability. It never downloads resources,
trains an engine, or mutates the environment.

Example:
    python scripts/check_snips_nlu_environment.py --resource en --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional


def _run(cmd: List[str], timeout: int = 20) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError as exc:
        return {"command": cmd, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "returncode": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": "command timed out",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Snips NLU environment/import/CLI/resource check."
    )
    parser.add_argument(
        "--resource",
        action="append",
        default=[],
        help=(
            "Optional language/resource name to check with snips_nlu.resources.load_resources, "
            "for example en. Repeat for multiple resources. No download is attempted."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON report instead of a short human summary.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report: Dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "imports": {},
        "versions": {},
        "cli": {},
        "resources": {},
        "warnings": [],
        "next_steps": [],
    }

    try:
        import snips_nlu
        from snips_nlu.__about__ import __model_version__, __version__
        from snips_nlu import SnipsNLUEngine
        from snips_nlu.dataset import Dataset
        from snips_nlu.resources import MissingResource, load_resources

        report["imports"]["snips_nlu"] = True
        report["versions"]["package"] = __version__
        report["versions"]["model"] = __model_version__
        report["api"] = {
            "SnipsNLUEngine": SnipsNLUEngine.__name__,
            "Dataset": Dataset.__name__,
        }
    except Exception as exc:  # pylint: disable=broad-except
        report["ok"] = False
        report["imports"]["snips_nlu"] = False
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        report["next_steps"].append(
            "Install snips-nlu in a compatible Python environment; for 0.20.x, Python 3.8 is a safe target."
        )
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("Snips NLU import failed: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2

    module_help = _run([sys.executable, "-m", "snips_nlu", "--help"])
    report["cli"]["python_m_snips_nlu_help"] = module_help
    if module_help["returncode"] != 0:
        report["ok"] = False
        report["next_steps"].append("Check whether the snips_nlu module CLI imports correctly.")

    console = shutil.which("snips-nlu")
    report["cli"]["console_script_path_visible"] = bool(console)
    if console:
        report["cli"]["snips_nlu_help"] = _run([console, "--help"])
    else:
        report["warnings"].append(
            "The snips-nlu console script is not on PATH; use python -m snips_nlu or fix the environment PATH."
        )

    version = _run([sys.executable, "-m", "snips_nlu", "version"])
    model_version = _run([sys.executable, "-m", "snips_nlu", "model-version"])
    report["cli"]["version"] = version
    report["cli"]["model_version"] = model_version

    for resource in args.resource:
        try:
            load_resources(resource)
            report["resources"][resource] = {"available": True}
        except MissingResource as exc:
            report["resources"][resource] = {
                "available": False,
                "error": str(exc),
                "next_step": f"Run: python -m snips_nlu download {resource}",
            }
            report["warnings"].append(
                f"Resource '{resource}' is not available locally; training/parsing may fail until it is downloaded or linked."
            )
        except Exception as exc:  # pylint: disable=broad-except
            report["resources"][resource] = {
                "available": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["warnings"].append(
                f"Resource '{resource}' could not be loaded; inspect compatibility with this package/model version."
            )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Snips NLU import: ok")
        print("Package version: %s" % report["versions"].get("package"))
        print("Model version: %s" % report["versions"].get("model"))
        print("python -m snips_nlu --help: rc=%s" % module_help["returncode"])
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print("- " + warning)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
