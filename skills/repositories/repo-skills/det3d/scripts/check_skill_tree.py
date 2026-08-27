#!/usr/bin/env python3
"""Static check for the self-contained Det3D skill tree."""
from __future__ import annotations
import argparse
import re
from pathlib import Path

IDS = ["configuration-and-models", "datasets-and-preprocessing", "training-and-evaluation", "runtime-ops", "visualization-and-analysis"]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    root = p.parse_args().root
    errors = []
    for rel in ["SKILL.md", "references/repo-provenance.md", "references/repo-routing-metadata.json"]:
        if not (root / rel).is_file(): errors.append(f"missing {rel}")
    for ident in IDS:
        path = root / "sub-skills" / ident / "SKILL.md"
        if not path.is_file(): errors.append(f"missing {path.relative_to(root)}"); continue
        text = path.read_text()
        if not re.search(rf"^name: {re.escape(ident)}$", text, re.M): errors.append(f"bad name {ident}")
        if "metadata:\n  disco-role: operating" not in text: errors.append(f"missing role {ident}")
        if "disable-model-invocation: true" not in text: errors.append(f"missing visibility {ident}")
    forbidden = ["/" + "root/", "production" + "_batches", "../" + "../examples", "../" + "tools"]
    for path in root.rglob("*.md"):
        text = path.read_text(errors="replace")
        if any(marker in text for marker in forbidden):
            errors.append(f"possible source/private path in {path.relative_to(root)}")
    print("PASS" if not errors else "FAIL")
    for error in errors: print(error)
    return 0 if not errors else 1

if __name__ == "__main__": raise SystemExit(main())
