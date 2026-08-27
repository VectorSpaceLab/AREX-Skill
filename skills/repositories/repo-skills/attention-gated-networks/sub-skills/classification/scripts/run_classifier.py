#!/usr/bin/env python3
"""Run Attention-Gated Networks classification training or testing.

This is a bundled replacement for the source repository's classification entry
points. It imports the installed package modules and can optionally add a local
checkout via --repo-root, but the script itself lives inside the generated skill.

Examples:
  python run_classifier.py --repo-root /path/to/repo --config config.json --mode train
  python run_classifier.py --repo-root /path/to/repo --config config.json --mode test --disable-visdom
"""
from __future__ import annotations

import argparse
import collections
import collections.abc
import json
import os
import pickle
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from torch.utils.data import DataLoader, sampler
from tqdm import tqdm

if not hasattr(collections, "Sequence"):
    collections.Sequence = collections.abc.Sequence


def add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def resolve_config_path(path: str, repo_root: Path | str | None = None) -> Path:
    """Resolve configs independently of the process working directory."""
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if repo_root is None:
        raise SystemExit("relative --config requires an explicit --repo-root")
    return (Path(repo_root).resolve() / candidate).resolve()


def to_namespace(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{key: to_namespace(val) for key, val in value.items()})
    if isinstance(value, list):
        return [to_namespace(item) for item in value]
    return value


def load_config(path: str, repo_root: Path | str | None = None):
    resolved = resolve_config_path(path, repo_root)
    try:
        data = json.loads(resolved.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"config not found: {resolved}") from exc
    # A relative dataset path belongs to the config, not to the caller's cwd.
    for key, value in data.get("data_path", {}).items():
        if isinstance(value, str) and not Path(value).expanduser().is_absolute():
            data["data_path"][key] = str((resolved.parent / value).resolve())
    cfg = to_namespace(data)
    if getattr(cfg.model, "type", None) == "aggregated_classifier" and not hasattr(cfg.model, "aggregation_param"):
        cfg.model.aggregation_param = 0
    return cfg


def validate_data_paths(cfg) -> None:
    """Reject private or missing datasets before constructing a loader."""
    for dataset_name, raw_path in vars(getattr(cfg, "data_path", SimpleNamespace())).items():
        if not isinstance(raw_path, str):
            continue
        if raw_path.startswith("/vol/"):
            raise SystemExit(
                f"data_path.{dataset_name} points to private path {raw_path!r}; "
                "copy the config and override it with an accessible dataset"
            )
        dataset_path = Path(raw_path).expanduser()
        if not dataset_path.exists():
            raise SystemExit(
                f"data_path.{dataset_name} does not exist: {dataset_path}; "
                "override the config before running"
            )


def set_attr(obj, name: str, value):
    setattr(obj, name, value)


def make_stratified_sampler(class_vector, batch_size):
    class StratifiedSampler(object):
        def __init__(self, class_vector, batch_size):
            self.class_vector = np.asarray(class_vector)
            self.batch_size = batch_size
            self.num_iter = len(class_vector) // 52
            self.n_class = 14
            self.sample_n = 2
            self.indices = {i: np.where(self.class_vector == i)[0] for i in range(self.n_class)}
            self.background_index = np.argmax([len(self.indices[i]) for i in range(self.n_class)])

        def gen_sample_array(self):
            sample_array = []
            for _ in range(self.num_iter):
                arrs = []
                for cls_id in range(self.n_class):
                    n = self.sample_n
                    if cls_id == self.background_index:
                        n = self.sample_n * (self.n_class - 1)
                    if len(self.indices[cls_id]) == 0:
                        raise SystemExit(f"class {cls_id} has no samples for stratified sampling")
                    arrs.append(np.random.choice(self.indices[cls_id], n))
                sample_array.append(np.hstack(arrs))
            return np.hstack(sample_array)

        def __iter__(self):
            return iter(self.gen_sample_array())

        def __len__(self):
            return len(self.class_vector)

    return StratifiedSampler(class_vector, batch_size)


def build_loaders(json_opts, mode: str, limit_workers: int | None):
    from dataio.loader import get_dataset, get_dataset_path
    from dataio.transformation import get_dataset_transformation

    train_opts = json_opts.training
    arch_type = train_opts.arch_type
    ds_class = get_dataset(arch_type)
    ds_path = get_dataset_path(arch_type, json_opts.data_path)
    ds_transform = get_dataset_transformation(arch_type, opts=json_opts.augmentation)
    num_workers = int(limit_workers if limit_workers is not None else getattr(train_opts, "num_workers", 16))
    batch_size = int(train_opts.batchSize)

    if mode == "test":
        valid_dataset = ds_class(ds_path, split="val", transform=ds_transform["valid"], preload_data=train_opts.preloadData)
        test_dataset = ds_class(ds_path, split="test", transform=ds_transform["valid"], preload_data=train_opts.preloadData)
        return {
            "valid_dataset": valid_dataset,
            "test_dataset": test_dataset,
            "test": DataLoader(test_dataset, num_workers=0, batch_size=batch_size, shuffle=False),
        }

    train_dataset = ds_class(ds_path, split="train", transform=ds_transform["train"], preload_data=train_opts.preloadData)
    valid_dataset = ds_class(ds_path, split="val", transform=ds_transform["valid"], preload_data=train_opts.preloadData)
    test_dataset = ds_class(ds_path, split="test", transform=ds_transform["valid"], preload_data=train_opts.preloadData)

    sampler_name = getattr(train_opts, "sampler", "weighted")
    if sampler_name == "stratified":
        train_sampler = make_stratified_sampler(train_dataset.labels, batch_size)
        effective_batch_size = 52
    elif sampler_name == "weighted2":
        weight = np.array(train_dataset.weight, copy=True)
        background_weight = np.min(weight)
        multiplier = getattr(train_opts, "bgd_weight_multiplier", 1)
        weight[np.abs(weight - background_weight) < 1e-8] = background_weight * multiplier
        train_sampler = sampler.WeightedRandomSampler(weight, len(weight))
        effective_batch_size = batch_size
    else:
        weight = np.array(train_dataset.weight, copy=True)
        train_sampler = sampler.WeightedRandomSampler(weight, len(weight))
        effective_batch_size = batch_size

    return {
        "train_dataset": train_dataset,
        "valid_dataset": valid_dataset,
        "test_dataset": test_dataset,
        "train": DataLoader(train_dataset, num_workers=num_workers, batch_size=effective_batch_size, sampler=train_sampler),
        "validation": DataLoader(valid_dataset, num_workers=num_workers, batch_size=batch_size, shuffle=True),
        "test": DataLoader(test_dataset, num_workers=num_workers, batch_size=batch_size, shuffle=True),
    }


def train(json_opts, args) -> None:
    from models import get_model
    from models.networks_other import adjust_learning_rate
    from utils.error_logger import ErrorLogger
    from utils.visualiser import Visualiser

    if args.disable_visdom:
        set_attr(json_opts.visualisation, "display_id", 0)

    if args.max_epochs is not None:
        set_attr(json_opts.training, "n_epochs", int(args.max_epochs))
    if args.limit_batches is not None:
        set_attr(json_opts.training, "max_it", int(args.limit_batches))

    model = get_model(json_opts.model)
    loaders = build_loaders(json_opts, mode="train", limit_workers=args.num_workers)
    visualizer = Visualiser(json_opts.visualisation, save_dir=model.save_dir)
    error_logger = ErrorLogger()
    train_dataset = loaders["train_dataset"]
    train_opts = json_opts.training

    track_labels = np.arange(len(train_dataset.label_names))
    model.set_labels(track_labels)
    model.set_scheduler(train_opts)
    if hasattr(model, "update_state"):
        model.update_state(0)

    for epoch in range(model.which_epoch, int(train_opts.n_epochs)):
        print(f"(epoch: {epoch}, total # iters: {len(loaders['train'])})")
        for epoch_iter, (images, labels) in tqdm(enumerate(loaders["train"], 1), total=len(loaders["train"])):
            model.set_input(images, labels)
            model.optimize_parameters()
            errors = model.get_current_errors()
            error_logger.update(errors, split="train")
            if getattr(train_opts, "max_it", None) == epoch_iter:
                break

        valid_err = None
        for loader, split in ((loaders["validation"], "validation"), (loaders["test"], "test")):
            model.reset_results()
            for epoch_iter, (images, labels) in tqdm(enumerate(loader, 1), total=len(loader)):
                model.set_input(images, labels)
                model.validate()
                if getattr(train_opts, "max_it", None) == epoch_iter:
                    break
            errors = model.get_accumulated_errors()
            stats = model.get_classification_stats()
            error_logger.update({**errors, **stats}, split=split)
            if split == "validation":
                valid_err = errors["CE"]

        for split in ["train", "validation", "test"]:
            labels = train_dataset.label_names
            visualizer.plot_current_errors(epoch, error_logger.get_errors(split), split_name=split, labels=labels)
            visualizer.print_current_errors(epoch, error_logger.get_errors(split), split_name=split)
        error_logger.reset()

        if epoch % int(train_opts.save_epoch_freq) == 0:
            model.save(epoch)
        if hasattr(model, "update_state"):
            model.update_state(epoch)
        model.update_learning_rate(metric=valid_err, epoch=epoch)


def test(json_opts, args) -> None:
    from models import get_model
    from utils.error_logger import ErrorLogger
    from utils.visualiser import Visualiser

    if args.disable_visdom:
        set_attr(json_opts.visualisation, "display_id", 0)

    model = get_model(json_opts.model)
    loaders = build_loaders(json_opts, mode="test", limit_workers=args.num_workers)
    valid_dataset = loaders["valid_dataset"]
    train_opts = json_opts.training
    visualizer = Visualiser(json_opts.visualisation, save_dir=model.save_dir, filename="test_loss_log.txt")
    error_logger = ErrorLogger()

    track_labels = np.arange(len(valid_dataset.label_names))
    model.set_labels(track_labels)
    model.set_scheduler(train_opts)
    if hasattr(model.net, "deep_supervised"):
        model.net.deep_supervised = False

    for loader, split in [(loaders["test"], "test")]:
        model.reset_results()
        for epoch_iter, (images, labels) in tqdm(enumerate(loader, 1), total=len(loader)):
            model.set_input(images, labels)
            model.validate()
            if args.limit_batches is not None and epoch_iter >= args.limit_batches:
                break
        errors = model.get_accumulated_errors()
        stats = model.get_classification_stats()
        error_logger.update({**errors, **stats}, split=split)

    for split in ["test"]:
        show_labels = valid_dataset.label_names
        visualizer.plot_current_errors(300, error_logger.get_errors(split), split_name=split, labels=show_labels)
        visualizer.print_current_errors(300, error_logger.get_errors(split), split_name=split)
        dst_file = os.path.join(model.save_dir, "test_result.pkl")
        with open(dst_file, "wb") as f:
            result = error_logger.get_errors(split)
            result["labels"] = valid_dataset.label_names
            result["pr_lbls"] = np.hstack(model.pr_lbls)
            result["gt_lbls"] = np.hstack(model.gt_lbls)
            pickle.dump(result, f)
        print(f"wrote={dst_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Checkout root; relative --config paths are resolved from here")
    parser.add_argument("--config", required=True, help="Classification config JSON (relative to --repo-root)")
    parser.add_argument("--mode", choices=("train", "test"), required=True, help="Run mode")
    parser.add_argument("--disable-visdom", action="store_true", help="Set visualisation.display_id=0 before running")
    parser.add_argument("--num-workers", type=int, help="Override DataLoader worker count")
    parser.add_argument("--limit-batches", type=int, help="Stop each split after this many batches")
    parser.add_argument("--max-epochs", type=int, help="Training-only epoch override for smoke runs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)
    cfg = load_config(args.config, args.repo_root)
    validate_data_paths(cfg)
    if args.mode == "train":
        train(cfg, args)
    else:
        test(cfg, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
