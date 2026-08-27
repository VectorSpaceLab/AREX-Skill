#!/usr/bin/env python3
"""Inspect a PaddleDetection exported inference model directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

REQUIRED = ["infer_cfg.yml", "model.pdmodel", "model.pdiparams"]
OPTIONAL = ["model.pdiparams.info"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect exported PaddleDetection model artifacts.")
    parser.add_argument("model_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.model_dir)
    report = {"model_dir": str(root), "files": {}, "infer_cfg": None, "ok": True}
    if not root.exists():
        report["ok"] = False
        report["error"] = "model_dir does not exist"
    else:
        for name in REQUIRED + OPTIONAL:
            p = root / name
            report["files"][name] = {"exists": p.exists(), "size": p.stat().st_size if p.exists() else None}
            if name in REQUIRED and not p.exists():
                report["ok"] = False
        cfg = root / "infer_cfg.yml"
        if cfg.exists():
            try:
                data = yaml.safe_load(cfg.read_text()) or {}
                report["infer_cfg"] = {
                    "arch": data.get("arch"),
                    "Preprocess": data.get("Preprocess"),
                    "label_list_len": len(data.get("label_list", []) or []),
                    "min_subgraph_size": data.get("min_subgraph_size"),
                    "use_dynamic_shape": data.get("use_dynamic_shape"),
                }
            except Exception as exc:
                report["ok"] = False
                report["infer_cfg_error"] = f"{type(exc).__name__}: {exc}"
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(json.dumps(report, indent=2, default=str))
        print("OK" if report["ok"] else "NOT READY")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
