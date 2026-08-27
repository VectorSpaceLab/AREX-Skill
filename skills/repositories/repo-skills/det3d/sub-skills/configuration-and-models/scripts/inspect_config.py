#!/usr/bin/env python3
"""Read-only summary of a Det3D Python config.

This helper intentionally stops at config loading. It never builds a model or
accesses a dataset, so it is safe for preflight checks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _plain(value):
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a Det3D config without building it")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    from det3d.torchie import Config

    cfg = Config.fromfile(str(args.config))
    keys = ["model", "data", "train_cfg", "test_cfg", "optimizer", "lr_config", "workflow", "work_dir"]
    summary = {key: _plain(cfg.get(key)) for key in keys if key in cfg}
    summary["config_path"] = str(args.config)
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
