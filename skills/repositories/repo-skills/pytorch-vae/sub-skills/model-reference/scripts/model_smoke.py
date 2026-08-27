#!/usr/bin/env python3
"""Run a tiny synthetic smoke on one PyTorch-VAE model.

Prerequisites:
- A checkout of PyTorch-VAE that contains models/, dataset.py, and the YAML
  configs you want to inspect.
- The repo runtime dependencies installed in the active Python environment.

Safe by default: this script only performs a tiny forward/loss check. Add
--check-sample and/or --check-generate only when the target model supports that
path and you want to exercise it explicitly.
The example commands assume the generated skill directory is the current working directory.

Example:
  python ./sub-skills/model-reference/scripts/model_smoke.py \
    --repo-root /path/to/PyTorch-VAE \
    --config /path/to/PyTorch-VAE/configs/vae.yaml

  python ./sub-skills/model-reference/scripts/model_smoke.py \
    --repo-root /path/to/PyTorch-VAE \
    --config /path/to/PyTorch-VAE/configs/vq_vae.yaml \
    --check-generate
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import torch
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
    except yaml.YAMLError as exc:
        raise SystemExit(f"failed to parse YAML config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"expected a mapping at top level in {path}")
    return data


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(config)
    model_params = cfg.setdefault("model_params", {})
    if "name" not in model_params:
        raise SystemExit("config is missing model_params.name")

    if "data_params" not in cfg:
        exp_params = cfg.setdefault("exp_params", {})
        if "data_path" in exp_params and "batch_size" in exp_params:
            cfg["data_params"] = {
                "data_path": exp_params["data_path"],
                "train_batch_size": exp_params.get("batch_size", 64),
                "val_batch_size": exp_params.get("batch_size", 64),
                "patch_size": exp_params.get("img_size", 64),
                "num_workers": exp_params.get("num_workers", 4),
            }
        else:
            raise SystemExit(
                "config is missing data_params; expected the current schema or a VampVAE-style legacy exp_params block"
            )
    return cfg


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
    return model_name, model_cls(**model_params)


def device_from_arg(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def make_inputs(model_name: str, cfg: Dict[str, Any], device: torch.device, batch_size: int) -> Tuple[torch.Tensor, Dict[str, Any]]:
    x = torch.randn(batch_size, 3, 64, 64, device=device)
    kwargs: Dict[str, Any] = {}
    if model_name == "ConditionalVAE":
        num_classes = int(cfg["model_params"].get("num_classes", 0))
        if num_classes <= 0:
            raise SystemExit("ConditionalVAE smoke needs model_params.num_classes")
        labels = torch.zeros(batch_size, num_classes, device=device)
        labels[:, 0] = 1.0
        kwargs["labels"] = labels
    return x, kwargs


def loss_kwargs(model_name: str) -> Dict[str, Any]:
    if model_name == "FactorVAE":
        return {"M_N": 0.1, "optimizer_idx": 0, "batch_idx": 0}
    return {"M_N": 0.1}


def maybe_device_arg(model_name: str, device: torch.device):
    if model_name == "VampVAE" and device.type == "cuda":
        return 0 if device.index is None else device.index
    return device


def run_smoke(cfg: Dict[str, Any], device: torch.device, batch_size: int, check_sample: bool, check_generate: bool) -> None:
    model_name, model = build_model(cfg)
    model = model.to(device)
    x, kwargs = make_inputs(model_name, cfg, device, batch_size)
    results = model(x, **kwargs)
    losses = model.loss_function(*results, **loss_kwargs(model_name))

    print(f"model: {model_name}")
    print(f"device: {device}")
    print(f"forward_outputs: {len(results)}")
    print(f"loss_keys: {sorted(losses)}")
    if "loss" in losses:
        print(f"loss: {float(losses['loss'])}")

    if check_generate and hasattr(model, "generate"):
        try:
            generated = model.generate(x, **kwargs)
            print(f"generate_shape: {tuple(generated.shape)}")
        except Exception as exc:
            print(f"generate_failed: {type(exc).__name__}: {exc}")
            raise

    if check_sample and hasattr(model, "sample"):
        try:
            sample_kwargs = dict(kwargs)
            current_device = maybe_device_arg(model_name, device)
            sampled = model.sample(batch_size, current_device, **sample_kwargs)
            print(f"sample_shape: {tuple(sampled.shape)}")
        except Warning as exc:
            print(f"sample_unavailable: {exc}")
        except Exception as exc:
            print(f"sample_failed: {type(exc).__name__}: {exc}")
            raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny synthetic smoke on one PyTorch-VAE model")
    parser.add_argument("--repo-root", required=True, help="path to a PyTorch-VAE checkout")
    parser.add_argument("--config", required=True, help="path to a YAML config file")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="device to use for the smoke")
    parser.add_argument("--batch-size", type=int, default=2, help="synthetic batch size")
    parser.add_argument("--check-sample", action="store_true", help="also try the model sample() method")
    parser.add_argument("--check-generate", action="store_true", help="also try the model generate() method")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)
    cfg = normalize_config(load_config(args.config))
    device = device_from_arg(args.device)
    run_smoke(cfg, device, args.batch_size, args.check_sample, args.check_generate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
