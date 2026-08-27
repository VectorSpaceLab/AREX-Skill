#!/usr/bin/env python3
"""Inspect Bindu agent-authoring surface without starting a server."""
from __future__ import annotations
import argparse, importlib, inspect, json, sys
from importlib.metadata import PackageNotFoundError, version

TARGETS = [
    ("bindu.penguin.bindufy", "bindufy"),
    ("bindu.penguin.manifest", "create_manifest"),
    ("bindu.penguin.manifest", "validate_agent_function"),
    ("bindu.penguin.config_validator", "ConfigValidator"),
    ("bindu.server.applications", "BinduApplication"),
    ("bindu.server.task_manager", "TaskManager"),
    ("bindu.utils.skills.loader", "load_skills"),
]

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    out = {"ok": True, "python": sys.version.split()[0], "targets": {}}
    try: out["bindu_version"] = version("bindu")
    except PackageNotFoundError as e: out.update(ok=False, bindu_version_error=str(e))
    for mod, name in TARGETS:
        key = f"{mod}.{name}"
        try:
            obj = getattr(importlib.import_module(mod), name)
            out["targets"][key] = {"import": "ok", "signature": str(inspect.signature(obj)) if callable(obj) else "class"}
        except Exception as e:
            out["ok"] = False
            out["targets"][key] = {"import": "error", "error": f"{type(e).__name__}: {e}"}
    if args.json: print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"ok={out['ok']} bindu_version={out.get('bindu_version','<missing>')}")
        for k, v in out["targets"].items(): print(f"{k}: {v}")
    return 0 if out["ok"] else 1
if __name__ == "__main__": raise SystemExit(main())
