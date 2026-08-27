#!/usr/bin/env python3
"""Run Attention-Gated Networks segmentation training from a config.

This bundled script replaces the source repository's hard-coded segmentation
entry point while preserving the same model, dataset, transform, visualizer, and
optimizer wiring. It imports installed package modules and can optionally add a
local checkout via --repo-root.

Examples:
  python run_segmentation.py --repo-root /path/to/repo --config config.json --disable-visdom
  python run_segmentation.py --repo-root /path/to/repo --config config.json --max-epochs 1 --limit-batches 2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from torch.utils.data import DataLoader
from tqdm import tqdm


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
    return to_namespace(data)


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


def set_attr(obj, name: str, value) -> None:
    setattr(obj, name, value)


def build_loaders(json_opts, num_workers: int | None):
    from dataio.loader import get_dataset, get_dataset_path
    from dataio.transformation import get_dataset_transformation

    train_opts = json_opts.training
    arch_type = train_opts.arch_type
    dataset_class = get_dataset(arch_type)
    dataset_path = get_dataset_path(arch_type, json_opts.data_path)
    dataset_transform = get_dataset_transformation(arch_type, opts=json_opts.augmentation)
    workers = int(num_workers if num_workers is not None else getattr(train_opts, "num_workers", 16))
    batch_size = int(train_opts.batchSize)

    train_dataset = dataset_class(dataset_path, split="train", transform=dataset_transform["train"], preload_data=train_opts.preloadData)
    valid_dataset = dataset_class(dataset_path, split="validation", transform=dataset_transform["valid"], preload_data=train_opts.preloadData)
    test_dataset = dataset_class(dataset_path, split="test", transform=dataset_transform["valid"], preload_data=train_opts.preloadData)

    return {
        "train": DataLoader(dataset=train_dataset, num_workers=workers, batch_size=batch_size, shuffle=True),
        "validation": DataLoader(dataset=valid_dataset, num_workers=workers, batch_size=batch_size, shuffle=False),
        "test": DataLoader(dataset=test_dataset, num_workers=workers, batch_size=batch_size, shuffle=False),
    }


def train(json_opts, args) -> None:
    from models import get_model
    from utils.error_logger import ErrorLogger
    from utils.visualiser import Visualiser

    if args.disable_visdom:
        set_attr(json_opts.visualisation, "display_id", 0)
    if args.max_epochs is not None:
        set_attr(json_opts.training, "n_epochs", int(args.max_epochs))

    model = get_model(json_opts.model)
    loaders = build_loaders(json_opts, args.num_workers)
    visualizer = Visualiser(json_opts.visualisation, save_dir=model.save_dir)
    error_logger = ErrorLogger()
    train_opts = json_opts.training

    model.set_scheduler(train_opts)
    for epoch in range(model.which_epoch, int(train_opts.n_epochs)):
        print(f"(epoch: {epoch}, total # iters: {len(loaders['train'])})")

        for epoch_iter, (images, labels) in tqdm(enumerate(loaders["train"], 1), total=len(loaders["train"])):
            model.set_input(images, labels)
            model.optimize_parameters()
            error_logger.update(model.get_current_errors(), split="train")
            if args.limit_batches is not None and epoch_iter >= args.limit_batches:
                break

        for split in ["validation", "test"]:
            for epoch_iter, (images, labels) in tqdm(enumerate(loaders[split], 1), total=len(loaders[split])):
                model.set_input(images, labels)
                model.validate()
                errors = model.get_current_errors()
                stats = model.get_segmentation_stats()
                error_logger.update({**errors, **stats}, split=split)
                if args.limit_batches is not None and epoch_iter >= args.limit_batches:
                    break
                visuals = model.get_current_visuals()
                visualizer.display_current_results(visuals, epoch=epoch, save_result=False)

        for split in ["train", "validation", "test"]:
            visualizer.plot_current_errors(epoch, error_logger.get_errors(split), split_name=split)
            visualizer.print_current_errors(epoch, error_logger.get_errors(split), split_name=split)
        error_logger.reset()

        if epoch % int(train_opts.save_epoch_freq) == 0:
            model.save(epoch)
        model.update_learning_rate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Checkout root; relative --config paths are resolved from here")
    parser.add_argument("--config", required=True, help="Segmentation config JSON (relative to --repo-root)")
    parser.add_argument("--disable-visdom", action="store_true", help="Set visualisation.display_id=0 before running")
    parser.add_argument("--num-workers", type=int, help="Override DataLoader worker count")
    parser.add_argument("--limit-batches", type=int, help="Stop each split after this many batches")
    parser.add_argument("--max-epochs", type=int, help="Epoch override for smoke or bounded runs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)
    cfg = load_config(args.config, args.repo_root)
    validate_data_paths(cfg)
    train(cfg, args)
    return 0




if __name__ == "__main__":
    raise SystemExit(main())
