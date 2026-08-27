#!/usr/bin/env python3
"""Perform a no-build, no-data static check of a VAD training/evaluation config."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", help="VAD config Python file")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args(argv)
    try:
        from mmcv import Config
        cfg = Config.fromfile(args.config)
    except Exception as exc:
        result = {"ok": False, "config": args.config, "error": "%s: %s" % (type(exc).__name__, exc)}
        print(json.dumps(result, indent=2) if args.as_json else "FAIL: %s" % result["error"])
        return 1
    model = cfg.get("model", {})
    data = cfg.get("data", {})
    train = data.get("train", {}) if isinstance(data, dict) else {}
    required = [k for k in ("model", "data", "evaluation") if k not in cfg]
    result = {"ok": not required and bool(cfg.get("plugin", False)), "config": args.config,
              "missing_top_level": required, "plugin": bool(cfg.get("plugin", False)),
              "plugin_dir": cfg.get("plugin_dir"), "model_type": model.get("type"),
              "head_type": model.get("pts_bbox_head", {}).get("type") if isinstance(model.get("pts_bbox_head", {}), dict) else None,
              "dataset_type": train.get("type") if isinstance(train, dict) else None,
              "ann_file": train.get("ann_file") if isinstance(train, dict) else None,
              "queue_length": train.get("queue_length") if isinstance(train, dict) else None,
              "load_from": cfg.get("load_from"), "img_norm_cfg": cfg.get("img_norm_cfg"),
              "evaluation": cfg.get("evaluation")}
    if not result["ok"] and not required:
        result["error"] = "VAD training contract expects plugin=True"
    if args.as_json: print(json.dumps(result, indent=2, default=str))
    else:
        print("%s: %s" % (args.config, "OK" if result["ok"] else "FAIL"))
        for k in ("model_type", "head_type", "dataset_type", "ann_file", "queue_length", "load_from", "plugin_dir", "error"):
            if result.get(k) is not None: print("  %s=%s" % (k, result[k]))
    return 0 if result["ok"] else 1

if __name__ == "__main__": raise SystemExit(main())
