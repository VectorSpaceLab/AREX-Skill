#!/usr/bin/env python3
"""Safe Torchreid train/eval command and config planner.

This helper is intentionally non-executing: it never launches training or
model evaluation. It merges embedded Torchreid 1.4.0-style defaults, embedded
official config templates, a user-supplied YAML config, and command-line
changes, then prints a command/config plan that a human or agent can review.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

IMAGE_DATASETS = {
    "market1501",
    "cuhk03",
    "dukemtmcreid",
    "msmt17",
    "viper",
    "grid",
    "cuhk01",
    "ilids",
    "sensereid",
    "prid",
    "cuhk02",
    "university1652",
    "cuhksysu",
}
VIDEO_DATASETS = {"mars", "ilidsvid", "prid2011", "dukemtmcvidreid"}
SAMPLERS = {
    "RandomSampler",
    "SequentialSampler",
    "RandomIdentitySampler",
    "RandomDomainSampler",
    "RandomDatasetSampler",
}
TRANSFORMS = {"random_flip", "random_crop", "random_patch", "color_jitter", "random_erase"}
OPTIMS = {"adam", "amsgrad", "sgd", "rmsprop", "radam"}
SCHEDULERS = {"single_step", "multi_step", "cosine"}

DEFAULT_CONFIG: Dict[str, Any] = {
    "model": {"name": "resnet50", "pretrained": True, "load_weights": "", "resume": ""},
    "data": {
        "type": "image",
        "root": "reid-data",
        "sources": ["market1501"],
        "targets": ["market1501"],
        "workers": 4,
        "split_id": 0,
        "height": 256,
        "width": 128,
        "combineall": False,
        "transforms": ["random_flip"],
        "k_tfm": 1,
        "norm_mean": [0.485, 0.456, 0.406],
        "norm_std": [0.229, 0.224, 0.225],
        "save_dir": "log",
        "load_train_targets": False,
    },
    "market1501": {"use_500k_distractors": False},
    "cuhk03": {"labeled_images": False, "classic_split": False, "use_metric_cuhk03": False},
    "sampler": {
        "train_sampler": "RandomSampler",
        "train_sampler_t": "RandomSampler",
        "num_instances": 4,
        "num_cams": 1,
        "num_datasets": 1,
    },
    "video": {"seq_len": 15, "sample_method": "evenly", "pooling_method": "avg"},
    "train": {
        "optim": "adam",
        "lr": 0.0003,
        "weight_decay": 5e-4,
        "max_epoch": 60,
        "start_epoch": 0,
        "batch_size": 32,
        "fixbase_epoch": 0,
        "open_layers": ["classifier"],
        "staged_lr": False,
        "new_layers": ["classifier"],
        "base_lr_mult": 0.1,
        "lr_scheduler": "single_step",
        "stepsize": [20],
        "gamma": 0.1,
        "print_freq": 20,
        "seed": 1,
    },
    "sgd": {"momentum": 0.9, "dampening": 0.0, "nesterov": False},
    "rmsprop": {"alpha": 0.99},
    "adam": {"beta1": 0.9, "beta2": 0.999},
    "loss": {
        "name": "softmax",
        "softmax": {"label_smooth": True},
        "triplet": {"margin": 0.3, "weight_t": 1.0, "weight_x": 0.0},
    },
    "test": {
        "batch_size": 100,
        "dist_metric": "euclidean",
        "normalize_feature": False,
        "ranks": [1, 5, 10, 20],
        "evaluate": False,
        "eval_freq": -1,
        "start_eval": 0,
        "rerank": False,
        "visrank": False,
        "visrank_topk": 10,
    },
}

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "im_osnet_x1_0_softmax_256x128_amsgrad_cosine": {
        "model": {"name": "osnet_x1_0", "pretrained": True},
        "data": {
            "type": "image",
            "sources": ["market1501"],
            "targets": ["market1501"],
            "height": 256,
            "width": 128,
            "combineall": False,
            "transforms": ["random_flip"],
            "save_dir": "log/osnet_x1_0_market1501_softmax_cosinelr",
        },
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {
            "optim": "amsgrad",
            "lr": 0.0015,
            "max_epoch": 250,
            "batch_size": 64,
            "fixbase_epoch": 10,
            "open_layers": ["classifier"],
            "lr_scheduler": "cosine",
        },
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_x1_0_softmax_256x128_amsgrad": {
        "model": {"name": "osnet_x1_0", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/osnet_x1_0_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0015, "max_epoch": 150, "batch_size": 64, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [60]},
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_x0_75_softmax_256x128_amsgrad": {
        "model": {"name": "osnet_x0_75", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/osnet_x0_75_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0015, "max_epoch": 150, "batch_size": 64, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [60]},
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_x0_5_softmax_256x128_amsgrad": {
        "model": {"name": "osnet_x0_5", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/osnet_x0_5_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.003, "max_epoch": 180, "batch_size": 128, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [80]},
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_x0_25_softmax_256x128_amsgrad": {
        "model": {"name": "osnet_x0_25", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/osnet_x0_25_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.003, "max_epoch": 180, "batch_size": 128, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [80]},
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_ibn_x1_0_softmax_256x128_amsgrad": {
        "model": {"name": "osnet_ibn_x1_0", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["dukemtmcreid"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip", "color_jitter"], "save_dir": "log/osnet_ibn_x1_0_market2duke_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0015, "max_epoch": 150, "batch_size": 64, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [60]},
        "test": {"batch_size": 300, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_osnet_ain_x1_0_softmax_256x128_amsgrad_cosine": {
        "model": {"name": "osnet_ain_x1_0", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501", "dukemtmcreid"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip", "color_jitter"], "save_dir": "log/osnet_ain_x1_0_market1501_softmax_cosinelr"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0015, "max_epoch": 100, "batch_size": 64, "fixbase_epoch": 10, "open_layers": ["classifier"], "lr_scheduler": "cosine"},
        "test": {"batch_size": 300, "dist_metric": "cosine", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_r50_softmax_256x128_amsgrad": {
        "model": {"name": "resnet50_fc512", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/resnet50_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0003, "max_epoch": 60, "batch_size": 32, "fixbase_epoch": 5, "open_layers": ["classifier"], "lr_scheduler": "single_step", "stepsize": [20]},
        "test": {"batch_size": 100, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
    "im_r50fc512_softmax_256x128_amsgrad": {
        "model": {"name": "resnet50_fc512", "pretrained": True},
        "data": {"type": "image", "sources": ["market1501"], "targets": ["market1501"], "height": 256, "width": 128, "combineall": False, "transforms": ["random_flip"], "save_dir": "log/resnet50_fc512_market1501_softmax"},
        "loss": {"name": "softmax", "softmax": {"label_smooth": True}},
        "train": {"optim": "amsgrad", "lr": 0.0003, "max_epoch": 60, "batch_size": 32, "fixbase_epoch": 5, "open_layers": ["fc", "classifier"], "lr_scheduler": "single_step", "stepsize": [20]},
        "test": {"batch_size": 100, "dist_metric": "euclidean", "normalize_feature": False, "evaluate": False, "eval_freq": -1, "rerank": False},
    },
}


def deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def flatten_keys(d: Dict[str, Any], prefix: str = "") -> Set[str]:
    keys = set()
    for key, value in d.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(flatten_keys(value, dotted))
        else:
            keys.add(dotted)
    return keys


VALID_KEYS = flatten_keys(DEFAULT_CONFIG)


def parse_literal(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none":
        return None
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


def set_dotted(cfg: Dict[str, Any], dotted_key: str, value: Any) -> None:
    if dotted_key not in VALID_KEYS:
        raise KeyError(f"Unknown config key: {dotted_key!r}")
    cursor = cfg
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = value


def get_dotted(cfg: Dict[str, Any], dotted_key: str) -> Any:
    cursor: Any = cfg
    for part in dotted_key.split("."):
        cursor = cursor[part]
    return cursor


def load_yaml(path: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("PyYAML is required to load --config-file YAML. Install pyyaml or use --template.") from exc
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must contain a mapping at top level: {path}")
    return data


def dump_config(cfg: Dict[str, Any]) -> str:
    try:
        import yaml  # type: ignore
    except Exception:
        return json.dumps(cfg, indent=2, sort_keys=False)
    return yaml.safe_dump(cfg, sort_keys=False)


def quote(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (list, tuple, dict)):
        return shlex.quote(repr(value))
    return shlex.quote(str(value))


def format_command(tokens: Iterable[str]) -> str:
    return " \\\n  ".join(tokens)


def opts_for_plan(cfg: Dict[str, Any]) -> List[Tuple[str, Any]]:
    keys = [
        "model.name",
        "model.pretrained",
        "model.load_weights",
        "model.resume",
        "data.type",
        "data.root",
        "data.sources",
        "data.targets",
        "data.height",
        "data.width",
        "data.transforms",
        "data.save_dir",
        "data.workers",
        "data.split_id",
        "data.combineall",
        "data.load_train_targets",
        "loss.name",
        "sampler.train_sampler",
        "sampler.num_instances",
        "sampler.num_cams",
        "sampler.num_datasets",
        "video.seq_len",
        "video.sample_method",
        "video.pooling_method",
        "train.optim",
        "train.lr",
        "train.max_epoch",
        "train.batch_size",
        "train.fixbase_epoch",
        "train.open_layers",
        "train.lr_scheduler",
        "train.stepsize",
        "test.batch_size",
        "test.dist_metric",
        "test.normalize_feature",
        "test.evaluate",
        "test.eval_freq",
        "test.rerank",
        "test.visrank",
        "test.visrank_topk",
        "cuhk03.labeled_images",
        "cuhk03.classic_split",
        "cuhk03.use_metric_cuhk03",
        "market1501.use_500k_distractors",
    ]
    return [(key, get_dotted(cfg, key)) for key in keys]


def add_pair_opts(tokens: List[str], pairs: List[Tuple[str, Any]]) -> None:
    for key, value in pairs:
        if value in ("", None):
            continue
        tokens.extend([shlex.quote(key), quote(value)])


def looks_like_placeholder(path: str) -> bool:
    p = path.lower()
    return p.startswith("/path/to") or "path_to" in p or p.startswith("<") or p.startswith("your_")


def validate_cfg(cfg: Dict[str, Any], *, warnings: List[str], errors: List[str]) -> None:
    data_type = cfg["data"]["type"]
    sources = cfg["data"]["sources"] or []
    targets = cfg["data"]["targets"] or []
    if isinstance(sources, str):
        sources = [sources]
    if isinstance(targets, str):
        targets = [targets]

    if data_type == "image":
        for key in list(sources) + list(targets):
            if key not in IMAGE_DATASETS:
                warnings.append(f"Dataset key {key!r} is not a built-in image key. If it is custom, register it before constructing ImageDataManager.")
    elif data_type == "video":
        for key in list(sources) + list(targets):
            if key not in VIDEO_DATASETS:
                warnings.append(f"Dataset key {key!r} is not a built-in video key. If it is custom, register it before constructing VideoDataManager.")
    else:
        errors.append("data.type must be 'image' or 'video'.")

    bad_transforms = [t for t in cfg["data"].get("transforms", []) if t not in TRANSFORMS]
    if bad_transforms:
        warnings.append(f"Unknown transform token(s) {bad_transforms}; Torchreid's transform builder ignores unsupported names.")

    if cfg["loss"]["name"] == "triplet":
        if cfg["sampler"]["train_sampler"] != "RandomIdentitySampler":
            warnings.append("Triplet loss usually needs sampler.train_sampler RandomIdentitySampler.")
        if cfg["loss"]["triplet"].get("weight_x", 0) == 0 and cfg["train"].get("fixbase_epoch", 0) > 0:
            errors.append("Pure triplet loss (loss.triplet.weight_x == 0) is incompatible with train.fixbase_epoch > 0 in the unified config check.")

    if cfg["test"].get("visrank") and not cfg["test"].get("evaluate"):
        errors.append("test.visrank True requires test.evaluate True.")

    if cfg["train"].get("optim") not in OPTIMS:
        errors.append(f"Unsupported optimizer {cfg['train'].get('optim')!r}; expected one of {sorted(OPTIMS)}.")
    if cfg["train"].get("lr_scheduler") not in SCHEDULERS:
        errors.append(f"Unsupported scheduler {cfg['train'].get('lr_scheduler')!r}; expected one of {sorted(SCHEDULERS)}.")
    if cfg["sampler"].get("train_sampler") not in SAMPLERS:
        errors.append(f"Unsupported sampler {cfg['sampler'].get('train_sampler')!r}; expected one of {sorted(SAMPLERS)}.")

    if cfg["video"].get("sample_method") == "all" and cfg["train"].get("batch_size") != 1:
        warnings.append("video.sample_method 'all' should use train.batch_size 1 because tracklet lengths can vary.")

    for key in ("model.load_weights", "model.resume"):
        value = get_dotted(cfg, key)
        if value and not looks_like_placeholder(str(value)) and not os.path.isfile(str(value)):
            warnings.append(f"{key} points to a file that does not exist yet: {value}")

    if cfg["test"].get("evaluate"):
        warnings.append("Torchreid's unified data-manager construction still loads the source train split in test-only mode; ensure data.sources is locally available or use a custom API runner.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe Torchreid train/eval command and config plans; never runs training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--list-templates", action="store_true", help="List embedded official template names and exit.")
    parser.add_argument("--template", choices=sorted(TEMPLATES), help="Embedded official config template to start from.")
    parser.add_argument("--config-file", help="YAML config to load and merge after defaults/template.")
    parser.add_argument("--mode", choices=["train", "eval"], default="train", help="Set train or test-only evaluation mode.")
    parser.add_argument("--data-type", choices=["image", "video"], help="Use ImageDataManager or VideoDataManager.")
    parser.add_argument("--root", help="Dataset root parent directory.")
    parser.add_argument("-s", "--source", nargs="+", dest="sources", help="Source dataset key(s).")
    parser.add_argument("-t", "--target", nargs="+", dest="targets", help="Target dataset key(s).")
    parser.add_argument("--transforms", nargs="+", help="Training transform tokens.")
    parser.add_argument("--model", help="Model key, e.g. osnet_x1_0 or resnet50_fc512.")
    pretrained = parser.add_mutually_exclusive_group()
    pretrained.add_argument("--pretrained", dest="pretrained", action="store_true", help="Set model.pretrained True.")
    pretrained.add_argument("--no-pretrained", dest="pretrained", action="store_false", help="Set model.pretrained False to avoid automatic pretrained loading.")
    parser.set_defaults(pretrained=None)
    parser.add_argument("--loss", choices=["softmax", "triplet"], help="Loss/engine family.")
    parser.add_argument("--weights", help="Path for model.load_weights.")
    parser.add_argument("--resume", help="Path for model.resume.")
    parser.add_argument("--save-dir", help="Output directory for logs/checkpoints/visrank.")
    parser.add_argument("--optimizer", choices=sorted(OPTIMS), help="Optimizer name.")
    parser.add_argument("--lr", type=float, help="Learning rate.")
    parser.add_argument("--max-epoch", type=int, help="Maximum training epochs.")
    parser.add_argument("--batch-size", type=int, help="Train batch size/tracklet batch size.")
    parser.add_argument("--test-batch-size", type=int, help="Evaluation batch size.")
    parser.add_argument("--scheduler", choices=sorted(SCHEDULERS), help="LR scheduler.")
    parser.add_argument("--stepsize", type=int, nargs="+", help="One or more LR step epochs.")
    parser.add_argument("--train-sampler", choices=sorted(SAMPLERS), help="Training sampler.")
    parser.add_argument("--num-instances", type=int, help="Instances per identity for RandomIdentitySampler.")
    parser.add_argument("--num-cams", type=int, help="Cameras/domains per batch for RandomDomainSampler.")
    parser.add_argument("--num-datasets", type=int, help="Datasets per batch for RandomDatasetSampler.")
    parser.add_argument("--workers", type=int, help="DataLoader workers.")
    parser.add_argument("--split-id", type=int, help="Dataset split id.")
    parser.add_argument("--seq-len", type=int, help="Video sequence length.")
    parser.add_argument("--sample-method", choices=["evenly", "random", "all"], help="Video sample method.")
    parser.add_argument("--pooling-method", choices=["avg", "max"], help="Video feature pooling.")
    parser.add_argument("--dist-metric", choices=["euclidean", "cosine"], help="Evaluation distance metric.")
    parser.add_argument("--normalize-feature", action="store_true", help="Set test.normalize_feature True.")
    parser.add_argument("--rerank", action="store_true", help="Set test.rerank True.")
    parser.add_argument("--visrank", action="store_true", help="Set test.visrank True; requires --mode eval.")
    parser.add_argument("--visrank-topk", type=int, help="Top-k gallery images for visrank output.")
    parser.add_argument("--cuhk03-labeled", action="store_true", help="Use CUHK03 labeled images.")
    parser.add_argument("--cuhk03-classic-split", action="store_true", help="Use CUHK03 classic split.")
    parser.add_argument("--use-metric-cuhk03", action="store_true", help="Use CUHK03 single-gallery-shot metric.")
    parser.add_argument("--market1501-500k", action="store_true", help="Use Market1501 500K distractors if present.")
    parser.add_argument("--load-train-targets", action="store_true", help="Build target train loader for domain adaptation.")
    parser.add_argument("--extra-opts", nargs=argparse.REMAINDER, help="Additional dotted KEY VALUE overrides, like YACS merge_from_list.")
    parser.add_argument("--launcher", default="<torchreid-unified-launcher>", help="Placeholder or user-provided launcher path used only in the printed command.")
    parser.add_argument("--write-config", help="Write the resolved config to this YAML/JSON file.")
    parser.add_argument("--print-json", action="store_true", help="Print resolved config as JSON instead of YAML-like text.")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for clarity; the helper is always a dry run and never executes training.")
    return parser


def apply_args(cfg: Dict[str, Any], args: argparse.Namespace) -> None:
    if args.data_type:
        cfg["data"]["type"] = args.data_type
    if args.root:
        cfg["data"]["root"] = args.root
    if args.sources:
        cfg["data"]["sources"] = args.sources
    if args.targets:
        cfg["data"]["targets"] = args.targets
    if args.transforms:
        cfg["data"]["transforms"] = args.transforms
    if args.model:
        cfg["model"]["name"] = args.model
    if args.pretrained is not None:
        cfg["model"]["pretrained"] = args.pretrained
    if args.loss:
        cfg["loss"]["name"] = args.loss
    if args.weights:
        cfg["model"]["load_weights"] = args.weights
    if args.resume:
        cfg["model"]["resume"] = args.resume
    if args.save_dir:
        cfg["data"]["save_dir"] = args.save_dir
    if args.optimizer:
        cfg["train"]["optim"] = args.optimizer
    if args.lr is not None:
        cfg["train"]["lr"] = args.lr
    if args.max_epoch is not None:
        cfg["train"]["max_epoch"] = args.max_epoch
    if args.batch_size is not None:
        cfg["train"]["batch_size"] = args.batch_size
    if args.test_batch_size is not None:
        cfg["test"]["batch_size"] = args.test_batch_size
    if args.scheduler:
        cfg["train"]["lr_scheduler"] = args.scheduler
    if args.stepsize:
        cfg["train"]["stepsize"] = args.stepsize if len(args.stepsize) > 1 else [args.stepsize[0]]
    if args.train_sampler:
        cfg["sampler"]["train_sampler"] = args.train_sampler
    if args.num_instances is not None:
        cfg["sampler"]["num_instances"] = args.num_instances
    if args.num_cams is not None:
        cfg["sampler"]["num_cams"] = args.num_cams
    if args.num_datasets is not None:
        cfg["sampler"]["num_datasets"] = args.num_datasets
    if args.workers is not None:
        cfg["data"]["workers"] = args.workers
    if args.split_id is not None:
        cfg["data"]["split_id"] = args.split_id
    if args.seq_len is not None:
        cfg["video"]["seq_len"] = args.seq_len
    if args.sample_method:
        cfg["video"]["sample_method"] = args.sample_method
    if args.pooling_method:
        cfg["video"]["pooling_method"] = args.pooling_method
    if args.dist_metric:
        cfg["test"]["dist_metric"] = args.dist_metric
    if args.normalize_feature:
        cfg["test"]["normalize_feature"] = True
    if args.rerank:
        cfg["test"]["rerank"] = True
    if args.visrank:
        cfg["test"]["visrank"] = True
    if args.visrank_topk is not None:
        cfg["test"]["visrank_topk"] = args.visrank_topk
    if args.cuhk03_labeled:
        cfg["cuhk03"]["labeled_images"] = True
    if args.cuhk03_classic_split:
        cfg["cuhk03"]["classic_split"] = True
    if args.use_metric_cuhk03:
        cfg["cuhk03"]["use_metric_cuhk03"] = True
    if args.market1501_500k:
        cfg["market1501"]["use_500k_distractors"] = True
    if args.load_train_targets:
        cfg["data"]["load_train_targets"] = True

    cfg["test"]["evaluate"] = args.mode == "eval"

    if args.extra_opts:
        if len(args.extra_opts) % 2 != 0:
            raise ValueError("--extra-opts must contain KEY VALUE pairs.")
        for key, value in zip(args.extra_opts[0::2], args.extra_opts[1::2]):
            set_dotted(cfg, key, parse_literal(value))


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates:
        print("Embedded templates:")
        for name in sorted(TEMPLATES):
            print(f"  - {name}")
        return 0

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if args.template:
        deep_merge(cfg, TEMPLATES[args.template])
    if args.config_file:
        deep_merge(cfg, load_yaml(args.config_file))

    try:
        apply_args(cfg, args)
    except Exception as exc:
        parser.error(str(exc))

    warnings: List[str] = []
    errors: List[str] = []
    validate_cfg(cfg, warnings=warnings, errors=errors)

    if args.write_config:
        out = Path(args.write_config)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dump_config(cfg), encoding="utf-8")

    print("Torchreid train/eval plan (dry-run only; nothing was executed)")
    print("=" * 72)
    if args.template:
        print(f"Template: {args.template}")
    if args.config_file:
        print(f"Loaded config: {args.config_file}")
    if args.write_config:
        print(f"Resolved config written to: {args.write_config}")
    print(f"Mode: {args.mode}")
    print()

    print("CLI-style command plan")
    print("----------------------")
    tokens = ["python", shlex.quote(args.launcher)]
    if args.write_config:
        tokens.extend(["--config-file", shlex.quote(args.write_config)])
    elif args.config_file:
        tokens.extend(["--config-file", shlex.quote(args.config_file)])
    elif args.template:
        tokens.extend(["--config-file", shlex.quote(f"<embedded-template:{args.template}>")])
    tokens.extend(["--root", quote(cfg["data"]["root"])])
    if cfg["data"].get("sources"):
        tokens.extend(["-s", " ".join(shlex.quote(str(x)) for x in cfg["data"]["sources"])])
    if cfg["data"].get("targets"):
        tokens.extend(["-t", " ".join(shlex.quote(str(x)) for x in cfg["data"]["targets"])])
    if cfg["data"].get("transforms"):
        tokens.extend(["--transforms", " ".join(shlex.quote(str(x)) for x in cfg["data"]["transforms"])])

    command_pairs = [
        ("model.name", cfg["model"]["name"]),
        ("model.pretrained", cfg["model"]["pretrained"]),
        ("model.load_weights", cfg["model"].get("load_weights", "")),
        ("model.resume", cfg["model"].get("resume", "")),
        ("data.type", cfg["data"]["type"]),
        ("data.save_dir", cfg["data"]["save_dir"]),
        ("loss.name", cfg["loss"]["name"]),
        ("test.evaluate", cfg["test"]["evaluate"]),
        ("test.visrank", cfg["test"]["visrank"]),
        ("test.rerank", cfg["test"]["rerank"]),
        ("test.dist_metric", cfg["test"]["dist_metric"]),
    ]
    add_pair_opts(tokens, command_pairs)
    print(format_command(tokens))
    print()

    print("Key dotted opts")
    print("---------------")
    for key, value in opts_for_plan(cfg):
        if value in ("", None):
            continue
        print(f"{key} {repr(value) if isinstance(value, list) else value}")
    print()

    if warnings:
        print("Warnings")
        print("--------")
        for warning in warnings:
            print(f"- {warning}")
        print()

    if errors:
        print("Errors")
        print("------")
        for error in errors:
            print(f"- {error}")
        print(file=sys.stderr)
        return 2

    print("Resolved config")
    print("---------------")
    if args.print_json:
        print(json.dumps(cfg, indent=2, sort_keys=False))
    else:
        print(dump_config(cfg).rstrip())

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
