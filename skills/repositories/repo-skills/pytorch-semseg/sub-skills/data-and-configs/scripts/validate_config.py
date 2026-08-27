#!/usr/bin/env python3
"""Static pytorch-semseg YAML config checker.

The checker deliberately does not import pytorch-semseg, instantiate dataset
loaders, read image/mask files, download data, run training, or write files. It
only parses YAML with yaml.safe_load and validates registry names, expected
sections, legacy drift, and optional filesystem layout hints.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import yaml
except Exception as exc:  # pragma: no cover - exercised only without PyYAML
    print(f"ERROR dependency.yaml: PyYAML is required to read configs ({exc}).", file=sys.stderr)
    sys.exit(2)


MODELS = {
    "fcn32s",
    "fcn16s",
    "fcn8s",
    "unet",
    "segnet",
    "pspnet",
    "icnet",
    "icnetBN",
    "linknet",
    "frrnA",
    "frrnB",
}

LOSSES = {
    "cross_entropy",
    "bootstrapped_cross_entropy",
    "multi_scale_cross_entropy",
}

OPTIMIZERS = {
    "sgd",
    "adam",
    "asgd",
    "adamax",
    "adadelta",
    "adagrad",
    "rmsprop",
}

SCHEDULERS = {
    "constant_lr",
    "poly_lr",
    "multi_step",
    "cosine_annealing",
    "exp_lr",
}

AUGMENTATIONS = {
    "gamma",
    "hue",
    "brightness",
    "saturation",
    "contrast",
    "rcrop",
    "hflip",
    "vflip",
    "scale",
    "rsize",
    "rsizecrop",
    "rotate",
    "translate",
    "ccrop",
}

DATASETS: Dict[str, Dict[str, Any]] = {
    "pascal": {
        "loader": "pascalVOCLoader",
        "signature": "(root, sbd_path=None, split='train_aug', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"train", "val", "trainval", "train_aug", "train_aug_val"},
        "supports_same": True,
    },
    "camvid": {
        "loader": "camvidLoader",
        "signature": "(root, split='train', is_transform=False, img_size=None, augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"train", "val", "test"},
        "supports_same": False,
        "ignores_img_size": True,
    },
    "ade20k": {
        "loader": "ADE20KLoader",
        "signature": "(root, split='training', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"training", "validation"},
        "supports_same": False,
    },
    "mit_sceneparsing_benchmark": {
        "loader": "MITSceneParsingBenchmarkLoader",
        "signature": "(root, split='training', is_transform=False, img_size=512, augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"training", "validation"},
        "supports_same": True,
    },
    "cityscapes": {
        "loader": "cityscapesLoader",
        "signature": "(root, split='train', is_transform=False, img_size=(512, 1024), augmentations=None, img_norm=True, version='cityscapes', test_mode=False)",
        "splits": {"train", "val", "test"},
        "supports_same": False,
    },
    "nyuv2": {
        "loader": "NYUv2Loader",
        "signature": "(root, split='training', is_transform=False, img_size=(480, 640), augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"training", "val"},
        "supports_same": False,
    },
    "sunrgbd": {
        "loader": "SUNRGBDLoader",
        "signature": "(root, split='training', is_transform=False, img_size=(480, 640), augmentations=None, img_norm=True, test_mode=False)",
        "splits": {"training", "val"},
        "supports_same": False,
    },
    "vistas": {
        "loader": "mapillaryVistasLoader",
        "signature": "(root, split='training', img_size=(640, 1280), is_transform=True, augmentations=None, test_mode=False)",
        "splits": {"training", "validation", "testing"},
        "supports_same": True,
    },
}

TOP_LEVEL_KEYS = {"model", "data", "training", "seed"}
MODEL_KEYS = {"arch"}
DATA_KEYS = {"dataset", "train_split", "val_split", "img_rows", "img_cols", "path", "sbd_path"}
TRAINING_KEYS = {
    "train_iters",
    "batch_size",
    "n_workers",
    "val_interval",
    "print_interval",
    "optimizer",
    "loss",
    "lr_schedule",
    "resume",
    "augmentations",
    # Known legacy/drift keys are allowed only so they can receive targeted warnings.
    "l_rate",
    "l_schedule",
    "momentum",
    "weight_decay",
    "visdom",
}

LEGACY_REPLACEMENTS = {
    "l_rate": "training.optimizer.lr",
    "l_schedule": "training.lr_schedule",
    "momentum": "training.optimizer.momentum",
    "weight_decay": "training.optimizer.weight_decay",
}

Issue = Tuple[str, str, str]


def add_issue(issues: List[Issue], level: str, code: str, message: str) -> None:
    issues.append((level.upper(), code, message))


def is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def as_path_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return None


def is_placeholder(value: str) -> bool:
    lowered = value.lower().strip()
    placeholder_tokens = [
        "<",
        ">",
        "path/to",
        "todo",
        "replace_me",
        "your_dataset",
        "your-path",
        "example",
    ]
    return any(token in lowered for token in placeholder_tokens)


def is_absolute_like(value: str) -> bool:
    if value.startswith("~"):
        return True
    if Path(value).is_absolute():
        return True
    return bool(re.match(r"^[A-Za-z]:[\\/]", value))


def is_private_like(value: str) -> bool:
    lowered = value.lower()
    tokens = re.split(r"[\\/]+", lowered)
    return any(token in {"private", "users", "home", "workspace", "scratch"} for token in tokens)


def warn_path_value(issues: List[Issue], dotted_name: str, value: Any) -> None:
    text = as_path_string(value)
    if text is None:
        return
    if is_placeholder(text):
        add_issue(
            issues,
            "WARN",
            f"{dotted_name}.placeholder",
            f"{dotted_name} looks like a placeholder; replace it before running data-bound workflows.",
        )
    if is_absolute_like(text):
        add_issue(
            issues,
            "WARN",
            f"{dotted_name}.absolute",
            f"{dotted_name} is absolute or user-specific; ensure it is intentional for the current machine.",
        )
    if is_private_like(text):
        add_issue(
            issues,
            "WARN",
            f"{dotted_name}.private",
            f"{dotted_name} looks private or machine-specific; avoid copying example paths unchanged.",
        )


def load_config(path: Path) -> Tuple[Optional[Any], List[Issue]]:
    issues: List[Issue] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError:
        add_issue(issues, "ERROR", "config.not_found", f"Config file not found: {path}")
        return None, issues
    except yaml.YAMLError as exc:
        add_issue(issues, "ERROR", "yaml.parse", f"YAML parse error: {exc}")
        return None, issues
    except OSError as exc:
        add_issue(issues, "ERROR", "config.read", f"Could not read config: {exc}")
        return None, issues

    add_issue(
        issues,
        "WARN",
        "yaml.safe_load",
        "This checker uses yaml.safe_load; adapt legacy scripts that call yaml.load(fp) without a Loader on modern PyYAML.",
    )
    return data, issues


def validate_required_sections(cfg: Any, issues: List[Issue]) -> Tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    if not is_mapping(cfg):
        add_issue(issues, "ERROR", "config.type", "Config root must be a YAML mapping.")
        return {}, {}, {}

    for key in cfg.keys():
        if key not in TOP_LEVEL_KEYS:
            add_issue(issues, "WARN", "top_level.unsupported", f"Unsupported top-level key {key!r}; stock entry points ignore it.")

    sections: Dict[str, Mapping[str, Any]] = {}
    for section in ("model", "data", "training"):
        if section not in cfg:
            add_issue(issues, "ERROR", f"{section}.missing", f"Missing required top-level section {section!r}.")
            sections[section] = {}
        elif not is_mapping(cfg[section]):
            add_issue(issues, "ERROR", f"{section}.type", f"Section {section!r} must be a mapping.")
            sections[section] = {}
        else:
            sections[section] = cfg[section]
    return sections["model"], sections["data"], sections["training"]


def validate_model(model: Mapping[str, Any], issues: List[Issue]) -> None:
    for key in model.keys():
        if key not in MODEL_KEYS:
            add_issue(
                issues,
                "WARN",
                "model.extra_key",
                f"model.{key} is treated as a model constructor argument and is not validated by this sub-skill.",
            )

    arch = model.get("arch")
    if arch is None:
        add_issue(issues, "ERROR", "model.arch.missing", "Missing model.arch.")
    elif arch not in MODELS:
        add_issue(
            issues,
            "ERROR",
            "model.arch.unsupported",
            f"Unsupported model.arch {arch!r}; valid ids: {', '.join(sorted(MODELS))}.",
        )


def validate_data(data_cfg: Mapping[str, Any], issues: List[Issue]) -> None:
    for key in data_cfg.keys():
        if key not in DATA_KEYS:
            add_issue(
                issues,
                "WARN",
                "data.unsupported_key",
                f"data.{key} is not forwarded by the stock train/validate loaders unless an adapter handles it.",
            )

    for key in ("dataset", "train_split", "val_split", "img_rows", "img_cols", "path"):
        if key not in data_cfg:
            add_issue(issues, "ERROR", f"data.{key}.missing", f"Missing data.{key}.")

    dataset = data_cfg.get("dataset")
    dataset_info = DATASETS.get(dataset) if isinstance(dataset, str) else None
    if dataset is None:
        pass
    elif dataset_info is None:
        add_issue(
            issues,
            "ERROR",
            "data.dataset.unsupported",
            f"Unsupported data.dataset {dataset!r}; valid ids: {', '.join(sorted(DATASETS))}.",
        )

    if dataset_info is not None:
        valid_splits = dataset_info["splits"]
        for split_key in ("train_split", "val_split"):
            split_value = data_cfg.get(split_key)
            if split_value is None:
                continue
            if split_value not in valid_splits:
                add_issue(
                    issues,
                    "ERROR",
                    f"data.{split_key}.unsupported",
                    f"{split_key}={split_value!r} is not an expected split for {dataset!r}; expected one of {', '.join(sorted(valid_splits))}.",
                )
        if dataset in {"nyuv2", "sunrgbd"}:
            for split_key in ("train_split", "val_split"):
                if data_cfg.get(split_key) == "validation":
                    add_issue(
                        issues,
                        "ERROR",
                        f"data.{split_key}.nyu_sunrgbd_spelling",
                        f"{dataset} uses config split 'val' for the test folder, not 'validation'.",
                    )
        if dataset == "vistas" and data_cfg.get("val_split") == "testing":
            add_issue(
                issues,
                "WARN",
                "data.val_split.vistas_testing",
                "Vistas testing data may not include labels; use a labeled split for validation.",
            )

    warn_path_value(issues, "data.path", data_cfg.get("path"))
    warn_path_value(issues, "data.sbd_path", data_cfg.get("sbd_path"))

    if dataset == "pascal":
        if "sbd_path" not in data_cfg or data_cfg.get("sbd_path") in (None, ""):
            add_issue(
                issues,
                "WARN",
                "data.sbd_path.missing",
                "Pascal loader setup expects SBD path information for augmented/pre_encoded behavior; add data.sbd_path when using Pascal data preparation.",
            )
        else:
            add_issue(
                issues,
                "WARN",
                "data.sbd_path.not_forwarded",
                "Stock train/validate calls do not forward data.sbd_path to the Pascal loader; use an adapter for SBD-aware execution.",
            )
    elif "sbd_path" in data_cfg:
        add_issue(issues, "WARN", "data.sbd_path.ignored", "data.sbd_path is only meaningful for the Pascal loader.")

    validate_img_size(data_cfg, dataset_info, issues)


def validate_img_size(data_cfg: Mapping[str, Any], dataset_info: Optional[Mapping[str, Any]], issues: List[Issue]) -> None:
    rows = data_cfg.get("img_rows")
    cols = data_cfg.get("img_cols")
    if rows is None or cols is None:
        return

    rows_same = isinstance(rows, str) and rows == "same"
    cols_same = isinstance(cols, str) and cols == "same"

    if rows_same or cols_same:
        if not (rows_same and cols_same):
            add_issue(issues, "ERROR", "data.img_size.same_pair", "Use img_rows: same and img_cols: same together, or use two integers.")
            return
        if dataset_info is None:
            return
        dataset = data_cfg.get("dataset")
        if dataset_info.get("supports_same"):
            add_issue(
                issues,
                "WARN",
                "data.img_size.same",
                f"{dataset} explicitly supports the ('same', 'same') transform path; verify model memory needs separately.",
            )
        elif dataset_info.get("ignores_img_size"):
            add_issue(issues, "WARN", "data.img_size.ignored", f"{dataset} ignores config img_size; 'same' has no practical effect.")
        else:
            add_issue(
                issues,
                "ERROR",
                "data.img_size.same_unsupported",
                f"{dataset} does not explicitly support img_rows/img_cols: same; use positive integer dimensions.",
            )
        return

    if not is_positive_int(rows):
        add_issue(issues, "ERROR", "data.img_rows.type", "data.img_rows must be a positive integer or the string 'same'.")
    if not is_positive_int(cols):
        add_issue(issues, "ERROR", "data.img_cols.type", "data.img_cols must be a positive integer or the string 'same'.")

    if dataset_info is not None and dataset_info.get("ignores_img_size"):
        add_issue(issues, "WARN", "data.img_size.ignored", "CamVid loader ignores config img_rows/img_cols and uses its internal size.")


def validate_training(training: Mapping[str, Any], issues: List[Issue]) -> None:
    for key in training.keys():
        if key not in TRAINING_KEYS:
            add_issue(issues, "WARN", "training.unsupported_key", f"training.{key} is not consumed by the stock training path.")

    required = (
        "train_iters",
        "batch_size",
        "n_workers",
        "val_interval",
        "print_interval",
        "optimizer",
        "loss",
        "lr_schedule",
        "resume",
    )
    for key in required:
        if key not in training:
            replacement = " Set it to null if intentionally unused." if key in {"loss", "lr_schedule", "resume"} else ""
            add_issue(issues, "ERROR", f"training.{key}.missing", f"Missing training.{key}.{replacement}")

    for key, replacement in LEGACY_REPLACEMENTS.items():
        if key in training:
            add_issue(
                issues,
                "WARN",
                f"training.{key}.legacy",
                f"training.{key} is legacy/drifted and is not forwarded correctly; use {replacement}.",
            )

    if "visdom" in training:
        add_issue(issues, "WARN", "training.visdom.ignored", "training.visdom appears in old configs but is not used by the stock training loop.")

    int_rules = {
        "train_iters": is_positive_int,
        "batch_size": is_positive_int,
        "n_workers": is_nonnegative_int,
        "val_interval": is_positive_int,
        "print_interval": is_positive_int,
    }
    for key, predicate in int_rules.items():
        if key in training and not predicate(training[key]):
            quantifier = "non-negative" if key == "n_workers" else "positive"
            add_issue(issues, "ERROR", f"training.{key}.type", f"training.{key} must be a {quantifier} integer.")

    validate_optimizer(training.get("optimizer"), training, issues)
    validate_loss(training.get("loss"), issues)
    validate_scheduler(training.get("lr_schedule"), issues)
    validate_augmentations(training.get("augmentations"), issues)
    warn_path_value(issues, "training.resume", training.get("resume"))


def validate_optimizer(optimizer: Any, training: Mapping[str, Any], issues: List[Issue]) -> None:
    if optimizer is None:
        if "optimizer" in training:
            add_issue(issues, "ERROR", "training.optimizer.null", "training.optimizer: null is unsafe because the training loop later calls .items(); provide a mapping with name and lr.")
        return
    if not is_mapping(optimizer):
        add_issue(issues, "ERROR", "training.optimizer.type", "training.optimizer must be a mapping.")
        return
    name = optimizer.get("name")
    if name is None:
        add_issue(issues, "ERROR", "training.optimizer.name.missing", "Missing training.optimizer.name.")
    elif name not in OPTIMIZERS:
        add_issue(
            issues,
            "ERROR",
            "training.optimizer.name.unsupported",
            f"Unsupported optimizer {name!r}; valid ids: {', '.join(sorted(OPTIMIZERS))}.",
        )
    if "lr" not in optimizer:
        if "l_rate" in training:
            add_issue(issues, "WARN", "training.optimizer.lr.legacy_source", "Move training.l_rate to training.optimizer.lr.")
        else:
            add_issue(issues, "WARN", "training.optimizer.lr.missing", "Most torch optimizers need training.optimizer.lr; add it unless intentionally using an optimizer default.")
    for warmup_key in ("warmup_iters", "mode", "gamma"):
        if warmup_key in optimizer:
            add_issue(
                issues,
                "WARN",
                "training.optimizer.warmup_location",
                f"training.optimizer.{warmup_key} follows README-era wording but is not consumed by scheduler warmup code; put warmup settings under training.lr_schedule.",
            )


def validate_loss(loss: Any, issues: List[Issue]) -> None:
    if loss is None:
        return
    if not is_mapping(loss):
        add_issue(issues, "ERROR", "training.loss.type", "training.loss must be null or a mapping.")
        return
    name = loss.get("name")
    if name is None:
        add_issue(issues, "ERROR", "training.loss.name.missing", "Missing training.loss.name, or set training.loss: null for the default loss.")
    elif name not in LOSSES:
        add_issue(
            issues,
            "ERROR",
            "training.loss.name.unsupported",
            f"Unsupported loss {name!r}; valid ids: {', '.join(sorted(LOSSES))}.",
        )


def validate_scheduler(schedule: Any, issues: List[Issue]) -> None:
    if schedule is None:
        return
    if not is_mapping(schedule):
        add_issue(issues, "ERROR", "training.lr_schedule.type", "training.lr_schedule must be null or a mapping.")
        return
    name = schedule.get("name")
    if name is None:
        add_issue(issues, "ERROR", "training.lr_schedule.name.missing", "Missing training.lr_schedule.name, or set training.lr_schedule: null.")
    elif name not in SCHEDULERS:
        add_issue(
            issues,
            "ERROR",
            "training.lr_schedule.name.unsupported",
            f"Unsupported scheduler {name!r}; valid ids: {', '.join(sorted(SCHEDULERS))}.",
        )
    if "warmup_iters" in schedule:
        if "mode" in schedule or "gamma" in schedule:
            add_issue(
                issues,
                "WARN",
                "training.lr_schedule.warmup_names",
                "Scheduler warmup code expects warmup_mode and warmup_factor, not mode and gamma.",
            )


def validate_augmentations(augmentations: Any, issues: List[Issue]) -> None:
    if augmentations is None:
        return
    if not is_mapping(augmentations):
        add_issue(issues, "ERROR", "training.augmentations.type", "training.augmentations must be null or a mapping.")
        return
    for key, value in augmentations.items():
        if key not in AUGMENTATIONS:
            add_issue(
                issues,
                "ERROR",
                "training.augmentations.unsupported",
                f"Unsupported augmentation key {key!r}; valid keys: {', '.join(sorted(AUGMENTATIONS))}.",
            )
            continue
        if key in {"hflip", "vflip"} and isinstance(value, (int, float)) and not isinstance(value, bool):
            if not (0.0 <= float(value) <= 1.0):
                add_issue(issues, "WARN", f"training.augmentations.{key}.range", f"{key} is a probability; typical range is 0 to 1.")
        if key == "translate" and not (isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 2):
            add_issue(issues, "WARN", "training.augmentations.translate.shape", "translate expects a two-value sequence [dx, dy].")
        if key in {"rcrop", "ccrop"}:
            is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
            is_pair = isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 2
            if not (is_number or is_pair):
                add_issue(issues, "WARN", f"training.augmentations.{key}.shape", f"{key} expects a number or a two-value [h, w] sequence.")


def check_exists(issues: List[Issue], kind: str, path: Path, *, warn_only: bool = False) -> None:
    if path.exists():
        return
    level = "WARN" if warn_only else "ERROR"
    add_issue(issues, level, f"paths.{kind}.missing", f"Missing expected {kind}: {path}")


def path_from_config(value: Any) -> Optional[Path]:
    text = as_path_string(value)
    if text is None or is_placeholder(text):
        return None
    return Path(os.path.expanduser(text))


def split_values(data_cfg: Mapping[str, Any]) -> List[str]:
    values: List[str] = []
    for key in ("train_split", "val_split"):
        value = data_cfg.get(key)
        if isinstance(value, str) and value not in values:
            values.append(value)
    return values


def check_strict_paths(data_cfg: Mapping[str, Any], training: Mapping[str, Any], issues: List[Issue]) -> None:
    dataset = data_cfg.get("dataset")
    root = path_from_config(data_cfg.get("path"))
    if dataset not in DATASETS or root is None:
        return

    check_exists(issues, "data.path", root)
    if not root.exists():
        return

    splits = split_values(data_cfg)
    if dataset == "pascal":
        check_exists(issues, "pascal.JPEGImages", root / "JPEGImages")
        check_exists(issues, "pascal.SegmentationClass", root / "SegmentationClass")
        split_root = root / "ImageSets" / "Segmentation"
        check_exists(issues, "pascal.ImageSets.Segmentation", split_root)
        for split in splits:
            if split in {"train", "val", "trainval"}:
                check_exists(issues, f"pascal.split.{split}", split_root / f"{split}.txt")
        if any(split in {"train_aug", "train_aug_val"} for split in splits):
            pre_encoded = root / "SegmentationClass" / "pre_encoded"
            check_exists(issues, "pascal.pre_encoded", pre_encoded, warn_only=True)
            sbd = path_from_config(data_cfg.get("sbd_path"))
            if sbd is None:
                add_issue(issues, "WARN", "paths.pascal.sbd_path.unchecked", "Cannot check SBD layout because data.sbd_path is missing or placeholder-like.")
            else:
                check_exists(issues, "pascal.sbd_path", sbd)
                if sbd.exists():
                    check_exists(issues, "pascal.sbd.train_txt", sbd / "dataset" / "train.txt")
                    check_exists(issues, "pascal.sbd.cls", sbd / "dataset" / "cls")
    elif dataset == "camvid":
        for split in splits:
            check_exists(issues, f"camvid.images.{split}", root / split)
            check_exists(issues, f"camvid.labels.{split}", root / f"{split}annot")
    elif dataset == "ade20k":
        for split in splits:
            check_exists(issues, f"ade20k.images.{split}", root / "images" / split)
            add_issue(issues, "WARN", f"paths.ade20k.labels.{split}", "ADE20K labels are expected beside images as *_seg.png; this checker does not scan image files.")
    elif dataset == "mit_sceneparsing_benchmark":
        for split in splits:
            check_exists(issues, f"mit.images.{split}", root / "images" / split)
            check_exists(issues, f"mit.annotations.{split}", root / "annotations" / split)
    elif dataset == "cityscapes":
        for split in splits:
            check_exists(issues, f"cityscapes.leftImg8bit.{split}", root / "leftImg8bit" / split)
            check_exists(issues, f"cityscapes.gtFine.{split}", root / "gtFine" / split)
    elif dataset == "nyuv2":
        mapping = {"training": "train", "val": "test"}
        for split in splits:
            folder = mapping.get(split)
            if folder:
                check_exists(issues, f"nyuv2.images.{folder}", root / folder)
                check_exists(issues, f"nyuv2.labels.{folder}", root / f"{folder}_annot")
    elif dataset == "sunrgbd":
        mapping = {"training": "train", "val": "test"}
        for split in splits:
            folder = mapping.get(split)
            if folder:
                check_exists(issues, f"sunrgbd.images.{folder}", root / folder)
                check_exists(issues, f"sunrgbd.labels.{folder}", root / "annotations" / folder)
    elif dataset == "vistas":
        check_exists(issues, "vistas.config_json", root / "config.json")
        for split in splits:
            check_exists(issues, f"vistas.images.{split}", root / split / "images")
            check_exists(issues, f"vistas.labels.{split}", root / split / "labels")

    resume = path_from_config(training.get("resume"))
    if resume is not None:
        check_exists(issues, "training.resume", resume, warn_only=True)


def print_summary(cfg: Mapping[str, Any]) -> None:
    model = cfg.get("model", {}) if is_mapping(cfg) else {}
    data_cfg = cfg.get("data", {}) if is_mapping(cfg) else {}
    training = cfg.get("training", {}) if is_mapping(cfg) else {}
    dataset = data_cfg.get("dataset") if is_mapping(data_cfg) else None
    dataset_info = DATASETS.get(dataset) if isinstance(dataset, str) else None

    print("Config summary:")
    print(f"  model.arch: {model.get('arch') if is_mapping(model) else None}")
    print(f"  data.dataset: {dataset}")
    if dataset_info:
        print(f"  data.loader: {dataset_info['loader']} {dataset_info['signature']}")
    print(f"  data.train_split: {data_cfg.get('train_split') if is_mapping(data_cfg) else None}")
    print(f"  data.val_split: {data_cfg.get('val_split') if is_mapping(data_cfg) else None}")
    print(f"  data.img_size: ({data_cfg.get('img_rows') if is_mapping(data_cfg) else None}, {data_cfg.get('img_cols') if is_mapping(data_cfg) else None})")
    if is_mapping(training):
        optimizer = training.get("optimizer")
        loss = training.get("loss")
        schedule = training.get("lr_schedule")
        augmentations = training.get("augmentations")
        opt_name = optimizer.get("name") if is_mapping(optimizer) else optimizer
        loss_name = loss.get("name") if is_mapping(loss) else loss
        sched_name = schedule.get("name") if is_mapping(schedule) else schedule
        aug_keys = sorted(augmentations.keys()) if is_mapping(augmentations) else augmentations
        print(f"  training.optimizer: {opt_name}")
        print(f"  training.loss: {loss_name}")
        print(f"  training.lr_schedule: {sched_name}")
        print(f"  training.augmentations: {aug_keys}")


def print_issues(issues: Iterable[Issue]) -> None:
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for level, code, message in sorted(issues, key=lambda item: (order.get(item[0], 99), item[1], item[2])):
        print(f"{level} {code}: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically validate a pytorch-semseg YAML config without importing loaders or reading dataset files."
    )
    parser.add_argument("--config", required=True, help="Path to the YAML config file to validate.")
    parser.add_argument(
        "--strict-paths",
        action="store_true",
        help="Also check expected dataset/checkpoint paths relative to the current working directory when paths are not absolute.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print normalized model/data/training summary after parsing.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    cfg, issues = load_config(config_path)
    if cfg is None:
        print_issues(issues)
        return 1

    model, data_cfg, training = validate_required_sections(cfg, issues)
    validate_model(model, issues)
    validate_data(data_cfg, issues)
    validate_training(training, issues)
    if args.strict_paths:
        check_strict_paths(data_cfg, training, issues)

    if args.print_summary and is_mapping(cfg):
        print_summary(cfg)
        print("")

    print_issues(issues)
    return 1 if any(level == "ERROR" for level, _code, _message in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
