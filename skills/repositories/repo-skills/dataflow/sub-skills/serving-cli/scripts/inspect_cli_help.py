#!/usr/bin/env python3
"""Print safe DataFlow CLI help for the main command groups.

This helper does not download models or start services. It only spawns
`python -m dataflow.cli ... --help` and captures the output.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "dataflow" / "__init__.py").is_file() and (parent / "pyproject.toml").is_file():
            return parent
    return None


COMMANDS = {
    "root": ["--help"],
    "init": ["init", "--help"],
    "init-repo": ["init", "repo", "--help"],
    "chat": ["chat", "--help"],
    "eval": ["eval", "--help"],
    "eval-init": ["eval", "init", "--help"],
    "eval-api": ["eval", "api", "--help"],
    "eval-local": ["eval", "local", "--help"],
    "pdf2model": ["pdf2model", "--help"],
    "pdf2model-init": ["pdf2model", "init", "--help"],
    "pdf2model-train": ["pdf2model", "train", "--help"],
    "text2model": ["text2model", "--help"],
    "text2model-init": ["text2model", "init", "--help"],
    "text2model-train": ["text2model", "train", "--help"],
    "webui": ["webui", "--help"],
}


def _write_shims() -> Path:
    shim_dir = Path(tempfile.mkdtemp(prefix="dataflow-cli-help-shims-"))
    (shim_dir / "colorlog.py").write_text(
        "import logging\n"
        "class ColoredFormatter(logging.Formatter):\n"
        "    def __init__(self, fmt=None, datefmt=None, log_colors=None, secondary_log_colors=None, style='%', **kwargs):\n"
        "        super().__init__(fmt=fmt, datefmt=datefmt, style=style)\n"
        "    def format(self, record):\n"
        "        for key in ('asctime_log_color', 'levelname_log_color', 'name_log_color', 'funcName_log_color', 'lineno_log_color', 'message_log_color', 'reset'):\n"
        "            if not hasattr(record, key):\n"
        "                setattr(record, key, '')\n"
        "        return super().format(record)\n",
        encoding="utf-8",
    )
    (shim_dir / "colorama.py").write_text(
        "class _Ansi:\n"
        "    def __getattr__(self, name):\n"
        "        return ''\n"
        "Fore = _Ansi()\n"
        "Style = _Ansi()\n"
        "def init(*args, **kwargs):\n"
        "    return None\n",
        encoding="utf-8",
    )
    (shim_dir / "appdirs.py").write_text(
        "from pathlib import Path\n"
        "def user_data_dir(appname=None, appauthor=None, roaming=False):\n"
        "    return str(Path.home() / '.local' / 'share' / (appname or 'app'))\n",
        encoding="utf-8",
    )
    return shim_dir


def _run_help(args: list[str], shim_dir: Path, repo_root: Path | None) -> int:
    env = os.environ.copy()
    pythonpath_parts = [str(shim_dir)]
    if repo_root is not None:
        pythonpath_parts.append(str(repo_root))
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(p for p in pythonpath_parts if p)

    cmd = [sys.executable, "-m", "dataflow.cli", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    print("=" * 80)
    print(f"$ {' '.join(cmd)}")
    print(f"exit={proc.returncode}")
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Print DataFlow CLI help safely.")
    parser.add_argument(
        "keys",
        nargs="*",
        help="Optional help keys to run. Defaults to the full help catalog.",
    )
    ns = parser.parse_args()

    shim_dir = _write_shims()
    repo_root = _find_repo_root()
    keys = ns.keys or list(COMMANDS.keys())

    bad_keys = [key for key in keys if key not in COMMANDS]
    if bad_keys:
        print(f"Unknown help key(s): {', '.join(bad_keys)}", file=sys.stderr)
        print(f"Known keys: {', '.join(COMMANDS)}", file=sys.stderr)
        return 2

    failures = 0
    for key in keys:
        failures += 1 if _run_help(COMMANDS[key], shim_dir, repo_root) != 0 else 0

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
