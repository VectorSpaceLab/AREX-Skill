#!/usr/bin/env python3
"""Validate or train a PyTorch-VAE config from any checkout root.

Prerequisites:
- A checkout of PyTorch-VAE that contains models/, experiment.py, dataset.py,
  and utils.py.
- The repo runtime dependencies installed in the active Python environment.

Safe by default: without --fit this script only loads and normalizes the config,
imports the repo modules, instantiates the model and datamodule, and runs the
Lightning data setup step. Add --fit only when you want the full training loop.
The example commands assume the generated skill directory is the current working directory.

Example:
  python ./sub-skills/training/scripts/train_from_config.py \
    --repo-root /path/to/PyTorch-VAE \
    --config /path/to/PyTorch-VAE/configs/vae.yaml

  python ./sub-skills/training/scripts/train_from_config.py \
    --repo-root /path/to/PyTorch-VAE \
    --config /path/to/PyTorch-VAE/configs/vae.yaml \
    --fit
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


def add_repo_root(repo_root: str) -> Path:
    repo = Path(repo_root).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"repo root does not exist: {repo}")
    sys.path.insert(0, str(repo))
    return repo


def load_config(config_path: str) -> Dict[str, Any]:
    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"config does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:  # pragma: no cover - direct parse failure
        raise SystemExit(f"failed to parse YAML config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"expected a mapping at top level in {path}")
    return data


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(config)

    model_params = cfg.setdefault("model_params", {})
    if "name" not in model_params:
        raise SystemExit("config is missing model_params.name")

    exp_params = cfg.setdefault("exp_params", {})
    trainer_params = cfg.setdefault("trainer_params", {})

    if "data_params" not in cfg:
        if "data_path" in exp_params and "batch_size" in exp_params:
            cfg["data_params"] = {
                "data_path": exp_params["data_path"],
                "train_batch_size": exp_params.get("batch_size", 64),
                "val_batch_size": exp_params.get("batch_size", 64),
                "patch_size": exp_params.get("img_size", 64),
                "num_workers": exp_params.get("num_workers", 4),
            }
            print("[normalize] mapped legacy exp_params data fields into data_params")
        else:
            raise SystemExit(
                "config is missing data_params; expected the current schema or a VampVAE-style legacy exp_params block"
            )

    if "max_epochs" not in trainer_params and "max_nb_epochs" in trainer_params:
        trainer_params["max_epochs"] = trainer_params["max_nb_epochs"]
        print("[normalize] copied trainer_params.max_nb_epochs to trainer_params.max_epochs")

    return cfg


def gpu_count(gpus: Any) -> int:
    if gpus is None:
        return 0
    if isinstance(gpus, bool):
        return int(gpus)
    if isinstance(gpus, int):
        return gpus
    if isinstance(gpus, (list, tuple, set)):
        return len(gpus)
    if isinstance(gpus, str):
        return 0 if gpus.strip() in {"", "0", "cpu"} else 1
    return 1


def build_model(cfg: Dict[str, Any]):
    try:
        from models import vae_models
    except ImportError as exc:
        raise SystemExit(f"could not import repo models: {exc}") from exc

    model_params = dict(cfg["model_params"])
    model_name = model_params.pop("name")
    try:
        model_cls = vae_models[model_name]
    except KeyError as exc:
        known = ", ".join(sorted(vae_models))
        raise SystemExit(f"unknown model {model_name!r}; known models: {known}") from exc
    return model_cls(**model_params)


def build_datamodule(cfg: Dict[str, Any]):
    try:
        from dataset import VAEDataset
    except ImportError as exc:
        raise SystemExit(f"could not import repo dataset module: {exc}") from exc

    trainer_gpus = cfg.get("trainer_params", {}).get("gpus", 0)
    pin_memory = gpu_count(trainer_gpus) != 0
    return VAEDataset(**cfg["data_params"], pin_memory=pin_memory)


def run_validation(cfg: Dict[str, Any]) -> None:
    model = build_model(cfg)
    try:
        from experiment import VAEXperiment
    except ImportError as exc:
        raise SystemExit(f"could not import repo experiment module: {exc}") from exc

    experiment = VAEXperiment(model, cfg["exp_params"])
    datamodule = build_datamodule(cfg)
    datamodule.setup()

    print(f"model: {model.__class__.__name__}")
    print(f"experiment: {experiment.__class__.__name__}")
    print(f"data_path: {cfg['data_params']['data_path']}")
    print(f"trainer_params.gpus: {cfg.get('trainer_params', {}).get('gpus', 0)!r}")
    print("validation-only check passed")


def run_fit(cfg: Dict[str, Any]) -> None:
    try:
        from pytorch_lightning import Trainer
        from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
        from pytorch_lightning.loggers import TensorBoardLogger
        from pytorch_lightning.plugins import DDPPlugin
        from pytorch_lightning.utilities.seed import seed_everything
    except ImportError as exc:
        raise SystemExit(f"could not import the Lightning training stack: {exc}") from exc

    model = build_model(cfg)
    from experiment import VAEXperiment
    datamodule = build_datamodule(cfg)
    datamodule.setup()

    seed = cfg.get("exp_params", {}).get("manual_seed")
    if seed is None:
        seed = cfg.get("logging_params", {}).get("manual_seed")
    if seed is not None:
        seed_everything(seed, workers=True)

    logging_params = cfg.get("logging_params", {})
    save_dir = logging_params.get("save_dir", "logs/")
    name = logging_params.get("name", cfg["model_params"]["name"])
    tb_logger = TensorBoardLogger(save_dir=save_dir, name=name)

    trainer_params = dict(cfg.get("trainer_params", {}))
    runner = Trainer(
        logger=tb_logger,
        callbacks=[
            LearningRateMonitor(),
            ModelCheckpoint(
                save_top_k=2,
                dirpath=str(Path(tb_logger.log_dir) / "checkpoints"),
                monitor="val_loss",
                save_last=True,
            ),
        ],
        strategy=DDPPlugin(find_unused_parameters=False),
        **trainer_params,
    )

    Path(tb_logger.log_dir, "Samples").mkdir(exist_ok=True, parents=True)
    Path(tb_logger.log_dir, "Reconstructions").mkdir(exist_ok=True, parents=True)

    print(f"starting fit for {cfg['model_params']['name']} -> {tb_logger.log_dir}")
    runner.fit(VAEXperiment(model, cfg["exp_params"]), datamodule=datamodule)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or train a PyTorch-VAE config")
    parser.add_argument("--repo-root", required=True, help="path to a PyTorch-VAE checkout")
    parser.add_argument("--config", required=True, help="path to a YAML config file")
    parser.add_argument("--fit", action="store_true", help="run the full Lightning fit instead of a validation-only check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)
    cfg = normalize_config(load_config(args.config))

    if args.fit:
        run_fit(cfg)
    else:
        run_validation(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
