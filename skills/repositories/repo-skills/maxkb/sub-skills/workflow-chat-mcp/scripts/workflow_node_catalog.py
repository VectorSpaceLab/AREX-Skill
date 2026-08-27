#!/usr/bin/env python3
"""Static catalog for MaxKB workflow node families."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[6]
NODE_INIT = REPO_ROOT / "apps" / "application" / "flow" / "step_node" / "__init__.py"
NODE_ROOT = REPO_ROOT / "apps" / "application" / "flow" / "step_node"


def parse_node_list(text: str) -> list[str]:
    match = re.search(r"node_list\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        return []
    items = []
    for part in match.group(1).split(","):
        name = part.strip()
        if name:
            items.append(name)
    return items


def main() -> int:
    text = NODE_INIT.read_text(encoding="utf-8") if NODE_INIT.exists() else ""
    node_list = parse_node_list(text)
    subdirs = sorted([p.name for p in NODE_ROOT.iterdir() if p.is_dir() and not p.name.startswith("__")]) if NODE_ROOT.exists() else []
    report = {
        "node_init": str(NODE_INIT.relative_to(REPO_ROOT)) if NODE_INIT.exists() else None,
        "node_count": len(node_list),
        "nodes": node_list,
        "directories": subdirs,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
