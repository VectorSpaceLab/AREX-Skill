#!/usr/bin/env python3
"""Check that KAG is installed and its public entry points are usable.

Safe from any working directory. The script creates a temporary minimal
`kag_config.yaml` before importing `kag`, because the package initializes its
config loader on import.

Examples:
  python skills/disco/kag/scripts/check_kag_install.py
  python skills/disco/kag/scripts/check_kag_install.py --pip-check --cli-help --registry-list
  python skills/disco/kag/scripts/check_kag_install.py --json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List


MINIMAL_CONFIG = """project:\n  id: 1\n  namespace: KagTemp\n  host_addr: http://127.0.0.1:8887\n  biz_scene: default\n  language: en\nlog:\n  level: INFO\n"""


@contextlib.contextmanager
def chdir(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


@contextlib.contextmanager
def temporary_kag_config():
    with tempfile.TemporaryDirectory(prefix="kag-install-check-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "kag_config.yaml").write_text(MINIMAL_CONFIG, encoding="utf-8")
        with chdir(tmp_path):
            yield tmp_path


def run_command(argv: List[str], cwd: Path | None = None) -> Dict[str, Any]:
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    return {
        "argv": argv,
        "cwd": str(cwd) if cwd else None,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def run_cli_help(name: str, fallback_snippet: str) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kag-cli-check-") as tmp:
        tmp_path = Path(tmp)
        exe = shutil.which(name)
        if exe:
            argv = [exe, "--help"]
        else:
            argv = [sys.executable, "-c", fallback_snippet, "--help"]
        return run_command(argv, cwd=tmp_path)


def run_pip_check() -> Dict[str, Any]:
    return run_command([sys.executable, "-m", "pip", "check"])


def import_runtime_packages() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kag-install-import-") as tmp:
        child_code = "\n".join(
            [
                "from importlib import metadata",
                "from pathlib import Path",
                "import json",
                "",
                "Path('kag_config.yaml').write_text(",
                "    'project:\\n  id: 1\\n  namespace: KagTemp\\n  host_addr: http://127.0.0.1:8887\\n  biz_scene: default\\n  language: en\\nlog:\\n  level: INFO\\n',",
                "    encoding='utf-8',",
                ")",
                "",
                "import kag  # type: ignore",
                "import knext  # type: ignore",
                "from kag.common.registry import Registrable",
                "",
                "registered = Registrable.list_all_registered(with_leaf_classes=False)",
                "registry_names = sorted({cls.__name__ for cls in registered})",
                "payload = {",
                "    'kag_module': getattr(kag, '__file__', None),",
                "    'knext_module': getattr(knext, '__file__', None),",
                "    'kag_version': getattr(kag, '__version__', None),",
                "    'knext_version': getattr(knext, '__version__', None),",
                "    'distribution_version': metadata.version('openspg-kag'),",
                "    'registries': registry_names,",
                "}",
                "print(json.dumps(payload))",
            ]
        )
        proc = subprocess.run(
            [sys.executable, "-I", "-c", child_code],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr.strip() or proc.stdout.strip() or "installed package import check failed"))
        return json.loads(proc.stdout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check KAG installation and entry points.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    parser.add_argument("--pip-check", action="store_true", help="Run `python -m pip check`.")
    parser.add_argument("--cli-help", action="store_true", help="Run `kag --help` and `knext --help`.")
    parser.add_argument(
        "--registry-list",
        action="store_true",
        help="Import KAG and list registered interface families.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    report: Dict[str, Any] = {
        "distribution": None,
        "imports": {},
        "commands": {},
        "pip_check": None,
        "errors": [],
    }

    try:
        dist_version = metadata.version("openspg-kag")
        report["distribution"] = {
            "name": "openspg-kag",
            "version": dist_version,
            "requires_python": metadata.metadata("openspg-kag").get("Requires-Python"),
        }
    except Exception as exc:
        report["errors"].append(f"distribution metadata: {exc}")

    try:
        import_info = import_runtime_packages()
        report["imports"] = import_info
    except Exception as exc:
        report["errors"].append(f"import kag/knext: {exc}")

    if args.pip_check:
        report["pip_check"] = run_pip_check()
        if report["pip_check"]["returncode"] != 0:
            report["errors"].append("pip check failed")

    if args.cli_help:
        report["commands"]["kag_help"] = run_cli_help(
            "kag",
            "from kag.bin.kag_cmds import main; main()",
        )
        report["commands"]["knext_help"] = run_cli_help(
            "knext",
            "from knext.command.knext_cli import _main; _main()",
        )
        for name, result in report["commands"].items():
            if result["returncode"] != 0:
                report["errors"].append(f"{name} failed")

    if args.registry_list:
        if report["imports"]:
            report["registry_list"] = {
                "count": len(report["imports"].get("registries", [])),
                "names": report["imports"].get("registries", []),
            }
        else:
            report["registry_list"] = {"count": 0, "names": []}
            report["errors"].append("registry list unavailable because imports failed")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        if report.get("distribution"):
            dist = report["distribution"]
            print(f"{dist['name']} {dist['version']}")
        if report.get("imports"):
            print(f"kag module: {report['imports'].get('kag_module')}")
            print(f"knext module: {report['imports'].get('knext_module')}")
            print(f"kag version: {report['imports'].get('kag_version')}")
            print(f"knext version: {report['imports'].get('knext_version')}")
        if args.registry_list and report.get("imports"):
            print("registered interfaces:")
            for name in report["imports"].get("registries", []):
                print(f"- {name}")
        if args.pip_check and report.get("pip_check"):
            rc = report["pip_check"]["returncode"]
            print(f"pip check: {'passed' if rc == 0 else 'failed'}")
        if args.cli_help and report.get("commands"):
            for name, result in report["commands"].items():
                print(f"{name}: {'passed' if result['returncode'] == 0 else 'failed'}")
        if report["errors"]:
            print("errors:")
            for error in report["errors"]:
                print(f"- {error}")

    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
