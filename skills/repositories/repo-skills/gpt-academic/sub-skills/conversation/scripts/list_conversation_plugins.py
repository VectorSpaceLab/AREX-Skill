#!/usr/bin/env python3
"""List GPT Academic conversation plugins and core buttons from a checkout.

Example:
  python sub-skills/conversation/scripts/list_conversation_plugins.py --repo-root <checkout> --group 对话
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def add_repo(root: str | None) -> Path:
    repo = Path(root or os.getcwd()).resolve()
    if not (repo / "crazy_functional.py").exists():
        raise SystemExit(f"Not a GPT Academic checkout: {repo}")
    sys.path.insert(0, str(repo))
    os.chdir(repo)
    return repo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", help="GPT Academic checkout root; defaults to current working directory")
    parser.add_argument("--group", default="对话", help="plugin group to list, e.g. 对话, 编程, 学术, 智能体")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    repo = add_repo(args.repo_root)
    import core_functional
    import crazy_functional

    core = list(core_functional.get_core_functions().keys())
    plugins = []
    for name, meta in crazy_functional.get_crazy_functions().items():
        groups = str(meta.get("Group", "")).split("|")
        if args.group in groups:
            plugins.append({
                "name": name,
                "groups": groups,
                "as_button": bool(meta.get("AsButton")),
                "advanced_args": bool(meta.get("AdvancedArgs")),
                "info": str(meta.get("Info", ""))[:160],
            })
    try:
        multiplex = crazy_functional.get_multiplex_button_functions()
    except Exception as exc:  # noqa: BLE001
        multiplex = {"error": f"{type(exc).__name__}: {exc}"}

    payload = {"repo_root": str(repo), "group": args.group, "core_buttons": core, "plugins": plugins, "multiplex": multiplex}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Core buttons ({len(core)}): " + ", ".join(core))
        print(f"\nPlugins in group {args.group} ({len(plugins)}):")
        for item in plugins:
            mark = "button" if item["as_button"] else "dropdown"
            print(f"- {item['name']} [{mark}] {item['info']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
