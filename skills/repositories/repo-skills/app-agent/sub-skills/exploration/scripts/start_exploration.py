#!/usr/bin/env python3
"""Run the AppAgent exploration phase with explicit mode selection.

This wrapper is safer than the source launcher because it accepts the mode as a
command-line argument, resolves paths explicitly, and avoids shell-string
construction. It still delegates to the repository's own exploration scripts so
behavior stays faithful to the source project.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> int:
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch AppAgent exploration.")
    parser.add_argument("--repo-root", default=".", help="Path to the AppAgent checkout.")
    parser.add_argument("--app", required=True, help="Target app name, spaces will be removed.")
    parser.add_argument("--root-dir", default=".", help="Local working directory for apps/ and tasks/ outputs.")
    parser.add_argument(
        "--mode",
        choices=("autonomous", "human"),
        default="autonomous",
        help="Exploration mode to run.",
    )
    parser.add_argument("--demo-name", help="Optional demo name for human demonstration mode.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    app = args.app.replace(" ", "")
    root_dir = args.root_dir

    if not repo_root.exists():
        print(f"ERROR: repo root does not exist: {repo_root}")
        return 1

    if args.mode == "autonomous":
        script = repo_root / "scripts" / "self_explorer.py"
        if not script.exists():
            print(f"ERROR: missing exploration script: {script}")
            return 1
        return _run([sys.executable, "scripts/self_explorer.py", "--app", app, "--root_dir", root_dir], cwd=repo_root)

    demo_name = args.demo_name
    if not demo_name:
        timestamp = int(datetime.now().timestamp())
        demo_name = datetime.fromtimestamp(timestamp).strftime(f"demo_{app}_%Y-%m-%d_%H-%M-%S")

    step_script = repo_root / "scripts" / "step_recorder.py"
    docs_script = repo_root / "scripts" / "document_generation.py"
    if not step_script.exists() or not docs_script.exists():
        print(f"ERROR: missing exploration helper script(s): {step_script}, {docs_script}")
        return 1

    step_recorder = [sys.executable, "scripts/step_recorder.py", "--app", app, "--demo", demo_name, "--root_dir", root_dir]
    doc_generation = [sys.executable, "scripts/document_generation.py", "--app", app, "--demo", demo_name, "--root_dir", root_dir]

    rc = _run(step_recorder, cwd=repo_root)
    if rc != 0:
        return rc
    return _run(doc_generation, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
