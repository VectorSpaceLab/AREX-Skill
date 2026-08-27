#!/usr/bin/env python3
"""Check OWL web-UI module names and a dotenv-like file without mutating it."""
from __future__ import annotations

import argparse
from pathlib import Path

# The checked-in English UI currently advertises these names. The list is kept
# here as an explicit preflight contract because a checkout may not ship each.
DEFAULT_MODULES = [
    "run", "run_mini", "run_gemini", "run_claude", "run_deepseek_zh",
    "run_mistral", "run_openai_compatible_model", "run_ollama",
    "run_qwen_mini_zh", "run_qwen_zh", "run_azure_openai", "run_groq",
    "run_ppio", "run_together_ai", "run_novita_ai",
]
PLACEHOLDER_MARKERS = ("your_key", "your-api-key", "your_id")


def env_status(path: Path | None) -> str:
    if path is None:
        return "not inspected"
    if not path.is_file():
        return "missing"
    names = []
    placeholders = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        names.append(key.strip())
        normalized = value.strip().strip("\"'").lower()
        if not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS):
            placeholders.append(key.strip())
    detail = f"{len(names)} named values"
    if placeholders:
        detail += f"; placeholder/blank names: {', '.join(placeholders)}"
    return detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples-dir", type=Path, required=True)
    parser.add_argument("--module", help="check only one UI module name")
    parser.add_argument("--env-file", type=Path, help="inspect names/status only; never prints values")
    parser.add_argument("--modules", nargs="*", help="override advertised module names")
    args = parser.parse_args()
    modules = args.modules or ([args.module] if args.module else DEFAULT_MODULES)
    if args.module and args.modules:
        parser.error("use --module or --modules, not both")
    present, missing = [], []
    for name in modules:
        target = args.examples_dir / f"{name}.py"
        (present if target.is_file() else missing).append(name)
    print(f"examples_dir: {args.examples_dir}")
    print(f"present: {', '.join(present) if present else '(none)'}")
    print(f"missing: {', '.join(missing) if missing else '(none)'}")
    print(f"env_file: {env_status(args.env_file)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
