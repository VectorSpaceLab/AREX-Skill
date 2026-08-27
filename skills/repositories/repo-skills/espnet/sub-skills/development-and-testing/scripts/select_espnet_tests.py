#!/usr/bin/env python3
"""Recommend focused ESPnet test commands from changed files; does not run them."""
from __future__ import annotations
import argparse
import json


def suggest(paths: list[str], area: str | None) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    joined = " ".join(paths + ([area] if area else []))
    if "espnet2/bin" in joined:
        out.append({"command": "pytest -q test/espnet2/bin", "reason": "ESPnet2 bin CLI changed."})
        out.append({"command": "python -m espnet2.bin.asr_train --help", "reason": "Parser/import smoke for Task-style CLI modules."})
    if "espnet2/tasks" in joined or "espnet2/asr" in joined:
        out.append({"command": "pytest -q test/espnet2/tasks test/espnet2/asr", "reason": "Task/model component change."})
    if "egs2" in joined or "recipe" in joined:
        out.append({"command": "bash ci/test_configuration_espnet2.sh asr", "reason": "Recipe/config dry-run validation for affected task."})
        out.append({"command": "bash ci/test_shell_espnet2.sh", "reason": "Recipe shell checks when tooling is available."})
    if "espnet3" in joined or area == "espnet3":
        out.append({"command": "pytest -q test/espnet3", "reason": "ESPnet3 utility/System change."})
    if "doc" in joined:
        out.append({"command": "bash ci/doc.sh", "reason": "Documentation generation check; may require doc extras."})
    return out or [{"command": "pytest -q test/espnet2", "reason": "Fallback broad focused suite; narrow further if changed files are known."}]


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest focused ESPnet tests without executing them.")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--area")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = suggest(args.changed_file, args.area)
    if args.json:
        print(json.dumps({"suggestions": data}, indent=2))
    else:
        for item in data:
            print(item["command"])
            print(f"  # {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
