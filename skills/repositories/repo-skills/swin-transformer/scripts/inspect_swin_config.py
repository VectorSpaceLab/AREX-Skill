#!/usr/bin/env python3
"""Summarize a Swin-Transformer YAML config without running training."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path


def load_with_repo_config(repo_root: Path, cfg: Path, opts: list[str]):
    root = repo_root.resolve()
    cfg_path = cfg if cfg.is_absolute() else root / cfg
    sys.path.insert(0, str(root))
    os.environ.setdefault("LOCAL_RANK", "0")
    from config import get_config

    class Args:
        batch_size = None
        data_path = None
        zip = False
        cache_mode = None
        pretrained = None
        resume = None
        accumulation_steps = None
        use_checkpoint = False
        amp_opt_level = None
        disable_amp = False
        output = "output"
        tag = "inspect"
        eval = False
        throughput = False
        fused_window_process = False
        fused_layernorm = False
        optim = None
        enable_amp = False
        local_rank = 0

    a = Args()
    a.cfg = str(cfg_path)
    a.opts = opts or None
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        c = get_config(a)
    summary = {
        "MODEL.TYPE": c.MODEL.TYPE,
        "MODEL.NAME": c.MODEL.NAME,
        "DATA.DATASET": c.DATA.DATASET,
        "DATA.IMG_SIZE": c.DATA.IMG_SIZE,
        "DATA.ZIP_MODE": c.DATA.ZIP_MODE,
        "TRAIN.EPOCHS": c.TRAIN.EPOCHS,
        "TRAIN.BASE_LR": float(c.TRAIN.BASE_LR),
        "TRAIN.ACCUMULATION_STEPS": c.TRAIN.ACCUMULATION_STEPS,
        "TRAIN.USE_CHECKPOINT": c.TRAIN.USE_CHECKPOINT,
        "AMP_ENABLE": getattr(c, "AMP_ENABLE", None),
        "ENABLE_AMP": getattr(c, "ENABLE_AMP", None),
        "OUTPUT": c.OUTPUT,
    }
    captured = stream.getvalue().strip()
    if captured:
        summary["messages"] = captured.splitlines()[:5]
    return summary


def fallback_yaml(cfg: Path):
    import yaml
    data = yaml.safe_load(cfg.read_text()) or {}
    model = data.get("MODEL", {}) or {}
    data_node = data.get("DATA", {}) or {}
    train = data.get("TRAIN", {}) or {}
    return {
        "MODEL.TYPE": model.get("TYPE"),
        "MODEL.NAME": model.get("NAME"),
        "DATA.DATASET": data_node.get("DATASET"),
        "DATA.IMG_SIZE": data_node.get("IMG_SIZE"),
        "TRAIN.EPOCHS": train.get("EPOCHS"),
        "TRAIN.BASE_LR": train.get("BASE_LR"),
        "note": "fallback YAML parse; defaults and BASE files were not fully merged",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect a Swin-Transformer config safely.")
    ap.add_argument("--repo-root", type=Path, help="Checkout root; enables exact config.py merging.")
    ap.add_argument("--cfg", type=Path, required=True, help="YAML config to inspect.")
    ap.add_argument("--opts", nargs="*", default=[], help="Optional KEY VALUE overrides, as accepted by config.py.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    cfg = args.cfg.resolve()
    if not cfg.exists():
        raise SystemExit(f"config not found: {cfg}")
    if len(args.opts) % 2:
        raise SystemExit("--opts must contain KEY VALUE pairs")
    try:
        summary = load_with_repo_config(args.repo_root, cfg, args.opts) if args.repo_root else fallback_yaml(cfg)
    except Exception as exc:
        summary = fallback_yaml(cfg)
        summary["config_py_error"] = f"{type(exc).__name__}: {exc}"
    warnings = []
    mt = summary.get("MODEL.TYPE")
    if mt == "swin_moe":
        warnings.append("Swin-MoE requires Tutel and multi-GPU/multi-node planning; CPU config parsing is not runtime verification.")
    if summary.get("DATA.DATASET") == "imagenet22K":
        warnings.append("ImageNet-22K expects JSON map files and a fall11_whole-style image tree.")
    if summary.get("TRAIN.USE_CHECKPOINT"):
        warnings.append("Gradient checkpointing saves memory but changes compute time; use it intentionally.")
    out = {"config": str(cfg.name), "summary": summary, "warnings": warnings}
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"Config: {cfg.name}")
        for k, v in summary.items():
            print(f"{k}: {v}")
        for w in warnings:
            print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
