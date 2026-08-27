#!/usr/bin/env python3
"""Validate an FCOS config by merging it into fcos_core.config.cfg when available."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def yaml_fallback(path: Path):
    try:
        import yaml  # type: ignore
    except Exception as exc:
        return {"ok": False, "mode": "yaml-fallback", "error": f"PyYAML unavailable: {exc}"}
    try:
        data = yaml.safe_load(path.read_text())
        return {"ok": True, "mode": "yaml-fallback", "top_level_keys": sorted((data or {}).keys())}
    except Exception as exc:
        return {"ok": False, "mode": "yaml-fallback", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    p = argparse.ArgumentParser(description="Validate an FCOS YAML config safely")
    p.add_argument("config")
    p.add_argument("--opts", nargs="*", default=[], help="Optional cfg.merge_from_list tokens")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    path = Path(args.config)
    if not path.exists():
        p.error(f"config not found: {path}")
    result = {"path": str(path), "ok": False}
    try:
        from fcos_core.config import cfg  # type: ignore
        c = cfg.clone()
        c.merge_from_file(str(path))
        if args.opts:
            if len(args.opts) % 2:
                raise ValueError("--opts must contain key/value pairs")
            c.merge_from_list(args.opts)
        result.update({
            "ok": True,
            "mode": "fcos_core.config",
            "model": {"fcos_on": bool(c.MODEL.FCOS_ON), "device": str(c.MODEL.DEVICE), "num_classes": int(c.MODEL.FCOS.NUM_CLASSES)},
            "datasets": {"train": list(c.DATASETS.TRAIN), "test": list(c.DATASETS.TEST)},
            "solver": {"max_iter": int(c.SOLVER.MAX_ITER), "ims_per_batch": int(c.SOLVER.IMS_PER_BATCH)},
        })
    except Exception as exc:
        result = yaml_fallback(path)
        result["path"] = str(path)
        result["full_schema_error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
