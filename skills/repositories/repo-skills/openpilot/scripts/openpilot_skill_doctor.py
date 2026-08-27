#!/usr/bin/env python3
"""Read-only diagnostics for an openpilot checkout.

This helper checks the layout and common build/import prerequisites that this
skill references. It does not run uv sync, build, tests, or live device tools.

Example:
  python openpilot_skill_doctor.py --repo-root /path/to/openpilot
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

REQUIRED = [
  "pyproject.toml",
  ".python-version",
  "uv.lock",
  "SConstruct",
  "openpilot/__init__.py",
  "tools/test_runner.py",
  "tools/op.sh",
]
SUBMODULE_DIRS = ["msgq_repo", "opendbc_repo", "panda", "rednose_repo", "teleoprtc_repo", "tinygrad_repo"]
NATIVE_OUTPUTS = [
  "openpilot/common/libparams_c.so",
  "msgq_repo/msgq/ipc_pyx.so",
  "msgq_repo/msgq/visionipc/visionipc_pyx.so",
]


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
  try:
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
    return p.returncode, p.stdout.strip()
  except Exception as exc:  # pragma: no cover - diagnostic path
    return 1, repr(exc)


def main() -> int:
  parser = argparse.ArgumentParser(description="Read-only openpilot checkout diagnostic")
  parser.add_argument("--repo-root", default=".", help="target openpilot checkout")
  parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
  parser.add_argument("--check-test-runner-help", action="store_true", help="also run tools/test_runner.py -h")
  args = parser.parse_args()

  root = Path(args.repo_root).resolve()
  result: dict[str, object] = {"repo_root": str(root), "ok": True, "checks": []}

  def add(name: str, ok: bool, detail: str):
    if not ok:
      result["ok"] = False
    result["checks"].append({"name": name, "ok": ok, "detail": detail})

  add("repo root exists", root.is_dir(), str(root))
  for rel in REQUIRED:
    add(f"required file {rel}", (root / rel).exists(), rel)

  for rel in SUBMODULE_DIRS:
    d = root / rel
    populated = d.is_dir() and any(d.iterdir())
    add(f"submodule {rel} populated", populated, rel)

  for rel in NATIVE_OUTPUTS:
    add(f"native output {rel}", (root / rel).exists(), rel)

  if (root / ".python-version").exists():
    add(".python-version", True, (root / ".python-version").read_text().strip())

  code, out = run(["git", "submodule", "status"], root)
  add("git submodule status", code == 0, out[:2000])

  code, out = run([sys.executable, "--version"], root)
  add("current python", code == 0, out)

  if args.check_test_runner_help and (root / "tools/test_runner.py").exists():
    code, out = run([sys.executable, "tools/test_runner.py", "-h"], root)
    add("test_runner help", code == 0 and "targets" in out, out[:2000])

  if args.json:
    print(json.dumps(result, indent=2))
  else:
    for item in result["checks"]:  # type: ignore[index]
      mark = "OK" if item["ok"] else "WARN"
      print(f"[{mark}] {item['name']}: {item['detail']}")
    print("overall:", "ok" if result["ok"] else "needs attention")

  return 0 if result["ok"] else 2


if __name__ == "__main__":
  raise SystemExit(main())
