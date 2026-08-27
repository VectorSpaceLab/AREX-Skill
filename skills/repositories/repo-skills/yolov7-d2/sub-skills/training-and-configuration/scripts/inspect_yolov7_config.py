#!/usr/bin/env python3
"""Inspect a YOLOv7-d2 Detectron2 config without building a model."""
import argparse
import json
from pathlib import Path


def summarize(cfg):
    return {
        "meta_architecture": cfg.MODEL.META_ARCHITECTURE,
        "weights": str(cfg.MODEL.WEIGHTS),
        "train_datasets": list(cfg.DATASETS.TRAIN),
        "test_datasets": list(cfg.DATASETS.TEST),
        "class_names": list(getattr(cfg.DATASETS, "CLASS_NAMES", [])),
        "yolo_classes": int(cfg.MODEL.YOLO.CLASSES),
        "input_format": str(cfg.INPUT.FORMAT),
        "min_size_train": list(cfg.INPUT.MIN_SIZE_TRAIN),
        "min_size_test": int(cfg.INPUT.MIN_SIZE_TEST),
        "max_size_test": int(cfg.INPUT.MAX_SIZE_TEST),
        "mosaic": bool(cfg.INPUT.MOSAIC.ENABLED),
        "mosaic_and_mixup": bool(cfg.INPUT.MOSAIC_AND_MIXUP.ENABLED),
        "distortion": bool(cfg.INPUT.DISTORTION.ENABLED),
        "grid_mask": bool(cfg.INPUT.GRID_MASK.ENABLED),
        "optimizer": str(cfg.SOLVER.OPTIMIZER),
        "amp": bool(cfg.SOLVER.AMP.ENABLED),
        "ims_per_batch": int(cfg.SOLVER.IMS_PER_BATCH),
        "base_lr": float(cfg.SOLVER.BASE_LR),
        "max_iter": int(cfg.SOLVER.MAX_ITER),
        "output_dir": str(cfg.OUTPUT_DIR),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge and summarize a YOLOv7-d2 config.")
    parser.add_argument("--config", required=True, help="YAML config file to inspect.")
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Optional KEY VALUE config overrides.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    path = Path(args.config)
    if not path.is_file():
        raise SystemExit(f"config not found: {path}")
    if len(args.opts) % 2:
        raise SystemExit("--opts must contain KEY VALUE pairs for Yacs configs")

    from detectron2.config import get_cfg
    from yolov7.config import add_yolo_config

    cfg = get_cfg()
    add_yolo_config(cfg)
    cfg.merge_from_file(str(path))
    cfg.merge_from_list(args.opts)
    out = summarize(cfg)
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for k, v in out.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
