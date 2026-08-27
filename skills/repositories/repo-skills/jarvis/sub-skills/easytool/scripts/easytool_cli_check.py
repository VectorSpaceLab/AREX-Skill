#!/usr/bin/env python3
"""Safe EasyTool file/import/help checker.

This helper performs only local filesystem checks and `main.py --help`.
It does not download datasets, call OpenAI, call RapidAPI, or execute
ToolBench external tools.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Dict, List


EXPECTED_FILES = [
    "easytool/README.md",
    "easytool/main.py",
    "easytool/requirements.txt",
    "easytool/data_process.py",
    "easytool/easytool/__init__.py",
    "easytool/easytool/util.py",
    "easytool/easytool/funcQA.py",
    "easytool/easytool/toolbench.py",
    "easytool/easytool/toolbench_retrieve.py",
    "easytool/easytool/restbench.py",
    "easytool/data_funcqa/funchub/math.py",
    "easytool/data_funcqa/tool_instruction/functions_data.json",
    "easytool/data_funcqa/tool_instruction/tool_dic.jsonl",
    "easytool/data_restbench/tool_instruction/tmdb_tool.json",
    "easytool/data_toolbench/tool_instruction/toolbench_tool_instruction.json",
    "easytool/data_toolbench/tool_instruction/API_description_embeddings.zip",
]

OPTIONAL_GENERATED_LAYOUTS = [
    "easytool/data_funcqa/test_data/funcqa_mh.json",
    "easytool/data_funcqa/test_data/funcqa_oh.json",
    "easytool/data_restbench/test_data/tmdb.json",
    "easytool/data_toolbench/test_data/G2_category.json",
    "easytool/data_toolbench/test_data/G3_instruction.json",
    "easytool/data_toolbench/tool_instruction/API_description_embeddings.pkl",
    "easytool/toolenv/tools",
]

_OPTION_RE = re.compile(r"--[A-Za-z0-9][A-Za-z0-9_-]*")
_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{6,}")


def _redact(text: str) -> str:
    return _SECRET_RE.sub("sk-<redacted>", text)


def _detect_options(text: str) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for match in _OPTION_RE.finditer(text):
        option = match.group(0)
        if option not in seen:
            seen.add(option)
            ordered.append(option)
    return ordered


def _python_command(value: str) -> List[str]:
    parts = shlex.split(value)
    return parts if parts else [sys.executable]


def run_help(repo_root: Path, python_value: str, warnings: List[str]) -> Dict[str, object]:
    easytool_dir = repo_root / "easytool"
    main_py = easytool_dir / "main.py"
    if not main_py.is_file():
        warnings.append("Cannot run help check because easytool/main.py is missing.")
        return {
            "returncode": None,
            "detected_options": [],
            "stderr_tail": "",
        }

    env = os.environ.copy()
    env.setdefault("OPENAI_API_KEY", "sk-dummy-for-easytool-help-only")
    inner_pkg = easytool_dir / "easytool"
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(inner_pkg) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")

    cmd = _python_command(python_value) + ["main.py", "--help"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(easytool_dir),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        warnings.append(f"Python command not found: {_redact(str(exc))}")
        return {"returncode": None, "detected_options": [], "stderr_tail": _redact(str(exc))}
    except subprocess.TimeoutExpired:
        warnings.append("Help check timed out after 30 seconds.")
        return {"returncode": None, "detected_options": [], "stderr_tail": "timeout"}

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    stderr_tail = "\n".join((proc.stderr or "").splitlines()[-12:])
    stderr_tail = _redact(stderr_tail)

    if proc.returncode != 0:
        warnings.append("main.py --help returned a nonzero status; inspect stderr_tail in the JSON output.")
        if "No module named 'util'" in combined:
            warnings.append("The util import workaround did not take effect; confirm repo root and easytool/easytool layout.")
        if "OPENAI_API_KEY" in combined:
            warnings.append("OPENAI_API_KEY was still reported missing despite the help-only dummy key.")
        if "No module named" in combined and "util" not in combined:
            warnings.append("A Python dependency appears missing from the active environment.")

    return {
        "returncode": proc.returncode,
        "detected_options": _detect_options(combined),
        "stderr_tail": stderr_tail,
    }


def build_summary(repo_root: Path, python_value: str) -> Dict[str, object]:
    warnings: List[str] = []
    files_present = {rel: (repo_root / rel).exists() for rel in EXPECTED_FILES}
    optional_present = {rel: (repo_root / rel).exists() for rel in OPTIONAL_GENERATED_LAYOUTS}

    missing_required = [rel for rel, present in files_present.items() if not present]
    if missing_required:
        warnings.append("Missing expected EasyTool source files: " + ", ".join(missing_required))

    missing_generated = [rel for rel, present in optional_present.items() if not present]
    if missing_generated:
        warnings.append(
            "Generated data/external-tool layouts are absent or incomplete; this is expected before data preparation or ToolBench setup: "
            + ", ".join(missing_generated)
        )

    help_result = run_help(repo_root, python_value, warnings)

    return {
        "files_present": files_present,
        "optional_layouts_present": optional_present,
        "help_returncode": help_result["returncode"],
        "import_workaround": {
            "applied": True,
            "pythonpath_entry": "easytool/easytool",
            "dummy_openai_key_if_missing": True,
        },
        "detected_options": help_result["detected_options"],
        "warnings": warnings,
        "help_stderr_tail": help_result["stderr_tail"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check EasyTool files and CLI help without network/API calls.")
    parser.add_argument("--repo-root", required=True, help="Path to the repository root containing the easytool/ directory.")
    parser.add_argument("--python", default=sys.executable, help="Python executable or command to use for the help check.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    summary = build_summary(repo_root, args.python)
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not all(summary["files_present"].values()):
        return 2
    if summary["help_returncode"] not in (0, None):
        return 1
    if summary["help_returncode"] is None:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
