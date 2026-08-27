#!/usr/bin/env python3
"""Parse VAD configs and report structural fields without building a model."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("configs", nargs="+", help="config Python files")
    p.add_argument("--check-plugin", action="store_true", help="require plugin=True and a plugin_dir")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p


def inspect_config(name, check_plugin):
    try:
        from mmcv import Config
    except Exception as exc:
        return {"config": name, "ok": False, "error": "mmcv.Config unavailable: %s" % exc}
    try:
        cfg = Config.fromfile(name)
        required = ["model", "data"]
        missing = [key for key in required if key not in cfg]
        plugin_ok = bool(cfg.get("plugin", False)) and bool(cfg.get("plugin_dir", ""))
        model = cfg.get("model", {})
        data = cfg.get("data", {})
        result = {"config": name, "ok": not missing and (plugin_ok if check_plugin else True),
                  "missing": missing, "plugin": bool(cfg.get("plugin", False)),
                  "plugin_dir": cfg.get("plugin_dir"), "model_type": model.get("type"),
                  "head_type": model.get("pts_bbox_head", {}).get("type") if isinstance(model.get("pts_bbox_head", {}), dict) else None,
                  "dataset_type": data.get("train", {}).get("type") if isinstance(data.get("train", {}), dict) else None,
                  "queue_length": data.get("train", {}).get("queue_length") if isinstance(data.get("train", {}), dict) else None,
                  "load_from": cfg.get("load_from"), "img_norm_cfg": cfg.get("img_norm_cfg")}
        if check_plugin and not plugin_ok:
            result["error"] = "plugin=True and plugin_dir are required for VAD registry loading"
        return result
    except Exception as exc:
        return {"config": name, "ok": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def main(argv=None):
    args = parser().parse_args(argv)
    results = [inspect_config(str(Path(x)), args.check_plugin) for x in args.configs]
    if args.as_json:
        print(json.dumps(results, indent=2, default=str))
    else:
        for r in results:
            print("%s: %s" % (r["config"], "OK" if r["ok"] else "FAIL"))
            for k in ("model_type", "head_type", "dataset_type", "queue_length", "load_from", "plugin_dir", "error"):
                if r.get(k) is not None: print("  %s=%s" % (k, r[k]))
    return 0 if all(r["ok"] for r in results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
