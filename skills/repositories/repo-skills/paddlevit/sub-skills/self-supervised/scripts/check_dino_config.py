#!/usr/bin/env python3
"""Read-only validation for a PaddleViT DINO YAML configuration.

This intentionally does not import PaddleViT, instantiate a model, download
anything, or modify the YAML. It merges the source config.py defaults needed
for validation with the supplied YAML, because the repository YAML files are
partial overrides.
"""
from __future__ import print_function

import argparse
import json
import math
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


DEFAULTS = {
    "DATA": {
        "DATASET": "imagenet2012",
        "IMAGE_SIZE": 224,
        "SMALL_CROP_IMAGE_SIZE": 96,
        "GLOBAL_CROPS_SCALE": [0.25, 1.0],
        "LOCAL_CROPS_SCALE": [0.05, 0.25],
        "LOCAL_CROPS_NUMBER": 10,
        "BATCH_SIZE": 16,
        "NUM_WORKERS": 2,
    },
    "MODEL": {
        "OUT_DIM": 65536,
        "DROPPATH": 0.1,
        "TRANS": {
            "PATCH_SIZE": 16,
            "IN_CHANNELS": 3,
            "EMBED_DIM": 768,
            "DEPTH": 12,
            "NUM_HEADS": 12,
        },
    },
    "TRAIN": {
        "NUM_EPOCHS": 400,
        "WARMUP_EPOCHS": 10,
        "WARMUP_TEACHER_TEMP_EPOCHS": 50,
        "WARMUP_TEACHER_TEMP": 0.04,
        "TEACHER_TEMP": 0.07,
        "MOMENTUM_TEACHER": 0.996,
        "FREEZE_LAST_LAYER": 3,
    },
}


def merge(base, override):
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def get(cfg, *keys):
    value = cfg
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def positive(value):
    return number(value) and value > 0


def scale_pair(value, label, errors, warnings):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        errors.append("%s must be a two-value list" % label)
        return
    if not all(number(v) for v in value):
        errors.append("%s must contain finite numbers" % label)
        return
    if not (0 < value[0] <= value[1] <= 1):
        errors.append("%s must satisfy 0 < low <= high <= 1" % label)


def validate(cfg):
    errors = []
    warnings = []
    image = get(cfg, "DATA", "IMAGE_SIZE")
    local = get(cfg, "DATA", "SMALL_CROP_IMAGE_SIZE")
    patch = get(cfg, "MODEL", "TRANS", "PATCH_SIZE")
    embed = get(cfg, "MODEL", "TRANS", "EMBED_DIM")
    heads = get(cfg, "MODEL", "TRANS", "NUM_HEADS")
    local_count = get(cfg, "DATA", "LOCAL_CROPS_NUMBER")
    epochs = get(cfg, "TRAIN", "NUM_EPOCHS")
    temp_epochs = get(cfg, "TRAIN", "WARMUP_TEACHER_TEMP_EPOCHS")

    for label, value in (("DATA.IMAGE_SIZE", image),
                         ("DATA.SMALL_CROP_IMAGE_SIZE", local),
                         ("MODEL.TRANS.PATCH_SIZE", patch),
                         ("MODEL.TRANS.EMBED_DIM", embed),
                         ("MODEL.TRANS.NUM_HEADS", heads),
                         ("MODEL.TRANS.DEPTH", get(cfg, "MODEL", "TRANS", "DEPTH")),
                         ("MODEL.OUT_DIM", get(cfg, "MODEL", "OUT_DIM"))):
        if not positive(value):
            errors.append("%s must be a positive finite number" % label)

    if positive(image) and positive(patch) and image % patch != 0:
        errors.append("DATA.IMAGE_SIZE must be divisible by MODEL.TRANS.PATCH_SIZE")
    if positive(local) and positive(patch) and local % patch != 0:
        errors.append("DATA.SMALL_CROP_IMAGE_SIZE must be divisible by MODEL.TRANS.PATCH_SIZE")
    if positive(local) and positive(patch) and local < patch:
        errors.append("DATA.SMALL_CROP_IMAGE_SIZE must be at least PATCH_SIZE")
    if positive(embed) and positive(heads) and embed % heads != 0:
        errors.append("MODEL.TRANS.EMBED_DIM must be divisible by NUM_HEADS")
    if not isinstance(local_count, int) or isinstance(local_count, bool) or local_count < 1:
        errors.append("DATA.LOCAL_CROPS_NUMBER must be an integer >= 1")

    scale_pair(get(cfg, "DATA", "GLOBAL_CROPS_SCALE"),
               "DATA.GLOBAL_CROPS_SCALE", errors, warnings)
    scale_pair(get(cfg, "DATA", "LOCAL_CROPS_SCALE"),
               "DATA.LOCAL_CROPS_SCALE", errors, warnings)

    dataset = get(cfg, "DATA", "DATASET")
    if dataset != "imagenet2012":
        warnings.append("DATA.DATASET=%r does not use the source ImageNet multi-crop transform; unmodified DINO entrypoints expect imagenet2012" % dataset)
    if positive(epochs) and positive(temp_epochs) and temp_epochs > epochs:
        errors.append("TRAIN.WARMUP_TEACHER_TEMP_EPOCHS cannot exceed TRAIN.NUM_EPOCHS")
    for label in ("TRAIN.WARMUP_TEACHER_TEMP", "TRAIN.TEACHER_TEMP"):
        if not positive(get(cfg, *label.split("."))):
            errors.append("%s must be positive" % label)
    momentum = get(cfg, "TRAIN", "MOMENTUM_TEACHER")
    if not number(momentum) or not (0 <= momentum < 1):
        errors.append("TRAIN.MOMENTUM_TEACHER must be in [0, 1)")
    batch = get(cfg, "DATA", "BATCH_SIZE")
    if not isinstance(batch, int) or isinstance(batch, bool) or batch < 1:
        errors.append("DATA.BATCH_SIZE must be an integer >= 1")
    workers = get(cfg, "DATA", "NUM_WORKERS")
    if not isinstance(workers, int) or isinstance(workers, bool) or workers < 0:
        errors.append("DATA.NUM_WORKERS must be an integer >= 0")
    if positive(epochs) and epochs > 100:
        warnings.append("TRAIN.NUM_EPOCHS=%s is a long-running schedule; use a bounded synthetic or short trial first" % epochs)
    if get(cfg, "MODEL", "NORM_LAST_LAYER") is not None:
        warnings.append("MODEL.NORM_LAST_LAYER is present, but source entrypoints hard-code DINOHead norm_last_layer behavior")
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate PaddleViT DINO YAML invariants without importing models or downloading data.")
    parser.add_argument("--config", required=True, help="DINO YAML file to validate")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    parser.add_argument("--strict", action="store_true", help="treat warnings as a failed check")
    args = parser.parse_args(argv)

    if yaml is None:
        print("ERROR: PyYAML is required to parse DINO YAML", file=sys.stderr)
        return 2
    if not os.path.isfile(args.config):
        print("ERROR: config does not exist: %s" % args.config, file=sys.stderr)
        return 2
    try:
        with open(args.config, "r") as handle:
            supplied = yaml.safe_load(handle) or {}
    except Exception as exc:
        print("ERROR: could not parse %s: %s" % (args.config, exc), file=sys.stderr)
        return 2
    if not isinstance(supplied, dict):
        print("ERROR: top-level YAML value must be a mapping", file=sys.stderr)
        return 2

    cfg = merge(DEFAULTS, supplied)
    errors, warnings = validate(cfg)
    result = {"config": os.path.abspath(args.config), "errors": errors,
              "warnings": warnings, "status": "pass" if not errors and not (args.strict and warnings) else "fail"}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("DINO config: %s" % result["status"].upper())
        for item in errors:
            print("ERROR: %s" % item)
        for item in warnings:
            print("WARNING: %s" % item)
        if not errors:
            print("Effective crop count: 2 global + %s local = %s student views" %
                  (cfg["DATA"]["LOCAL_CROPS_NUMBER"], cfg["DATA"]["LOCAL_CROPS_NUMBER"] + 2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
