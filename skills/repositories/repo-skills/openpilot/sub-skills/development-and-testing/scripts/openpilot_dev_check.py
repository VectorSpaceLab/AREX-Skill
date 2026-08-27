#!/usr/bin/env python3
"""Read-only development checker for an openpilot checkout."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

REQUIRED_FILES = ["pyproject.toml", ".python-version", "uv.lock", "SConstruct", "tools/test_runner.py", "scripts/lint/lint.sh"]
SUBMODULES = ["msgq_repo", "opendbc_repo", "panda", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"]
NATIVE = ["openpilot/common/libparams_c.so", "msgq_repo/msgq/ipc_pyx.so", "msgq_repo/msgq/visionipc/visionipc_pyx.so"]


def run(cmd: list[str], cwd: Path) -> str:
  try:
    return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.STDOUT, timeout=15).strip()
  except Exception as exc:
    return f"ERROR: {exc}"


def main() -> int:
  parser = argparse.ArgumentParser(description="Check openpilot development prerequisites without mutating the checkout")
  parser.add_argument("--repo-root", default=".")
  parser.add_argument("--test-runner-help", action="store_true")
  args = parser.parse_args()
  root = Path(args.repo_root).resolve()

  failures = 0
  def check(name: str, ok: bool, detail: str = ""):
    nonlocal failures
    if not ok:
      failures += 1
    print(f"[{'OK' if ok else 'WARN'}] {name}{': ' + detail if detail else ''}")

  check("repo root exists", root.is_dir(), str(root))
  for rel in REQUIRED_FILES:
    check(rel, (root / rel).exists())
  for rel in SUBMODULES:
    d = root / rel
    check(f"submodule {rel}", d.is_dir() and any(d.iterdir()), "populated" if d.is_dir() and any(d.iterdir()) else "missing/empty")
  for rel in NATIVE:
    check(f"native output {rel}", (root / rel).exists())

  pyver = (root / ".python-version").read_text().strip() if (root / ".python-version").exists() else "missing"
  check("declared python", pyver != "missing", pyver)
  print("git submodule status:\n" + run(["git", "submodule", "status"], root))

  if args.test_runner_help and (root / "tools/test_runner.py").exists():
    out = run([sys.executable, "tools/test_runner.py", "-h"], root)
    check("test_runner help", "targets" in out and "--jobs" in out, out.splitlines()[0] if out else "no output")

  return 0 if failures == 0 else 2


if __name__ == "__main__":
  raise SystemExit(main())
