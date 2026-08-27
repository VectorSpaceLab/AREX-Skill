#!/usr/bin/env python3
"""Smoke-check a YOLOv7-d2 installation and optional Detectron2 config.

This helper is safe: it imports packages and optionally merges a config, but it
never builds a model, downloads weights, opens a GUI, or runs training.
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check yolov7_d2 import and add_yolo_config.")
    parser.add_argument("--config", help="Optional user config file to merge after add_yolo_config.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of text.")
    args = parser.parse_args()

    from importlib.metadata import version
    from detectron2.config import get_cfg
    from yolov7.config import add_yolo_config

    cfg = get_cfg()
    add_yolo_config(cfg)
    merged = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            raise SystemExit(f"config not found: {config_path}")
        cfg.merge_from_file(str(config_path))
        merged = str(config_path)

    summary = {
        "distribution": "yolov7_d2",
        "version": version("yolov7_d2"),
        "merged_config": merged,
        "meta_architecture": cfg.MODEL.META_ARCHITECTURE,
        "train_datasets": list(cfg.DATASETS.TRAIN),
        "test_datasets": list(cfg.DATASETS.TEST),
        "yolo_classes": int(cfg.MODEL.YOLO.CLASSES),
        "optimizer": str(cfg.SOLVER.OPTIMIZER),
        "detr_queries": int(cfg.MODEL.DETR.NUM_OBJECT_QUERIES),
        "output_dir": str(cfg.OUTPUT_DIR),
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
