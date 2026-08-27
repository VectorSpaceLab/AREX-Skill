#!/usr/bin/env python3
"""Check the Attention-Gated Networks environment and run tiny CUDA smokes.

Run this from any working directory. Pass --repo-root when the repository is
not already importable from the current Python environment.

Examples:
  python scripts/check_env.py --repo-root /path/to/repo --mode all
  python scripts/check_env.py --repo-root /path/to/repo --mode classification
  python scripts/check_env.py --repo-root /path/to/repo --mode segmentation
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


def resolve_config_path(config_path: str, repo_root: Path) -> Path:
    candidate = Path(config_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def check_config_data_paths(config_path: str, repo_root: Path) -> None:
    resolved = resolve_config_path(config_path, repo_root)
    try:
        data = json.loads(resolved.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"config not found: {resolved}") from exc
    for dataset_name, raw_path in data.get("data_path", {}).items():
        if not isinstance(raw_path, str):
            continue
        if not Path(raw_path).expanduser().is_absolute():
            raw_path = str((resolved.parent / raw_path).resolve())
        if raw_path.startswith("/vol/"):
            raise SystemExit(
                f"data_path.{dataset_name} points to private path {raw_path!r}; "
                "copy the config and override it before running"
            )
        if not Path(raw_path).expanduser().exists():
            raise SystemExit(
                f"data_path.{dataset_name} does not exist: {raw_path}; "
                "override the config with an accessible dataset"
            )


def add_repo_root(repo_root: str) -> Path:
    root = Path(repo_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def build_classification_opts(tmpdir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        gpu_ids=[0],
        isTrain=True,
        continue_train=False,
        which_epoch=0,
        save_dir=str(tmpdir / "classification"),
        model_type="sononet2",
        input_nc=1,
        output_nc=14,
        lr_rate=0.1,
        l2_reg_weight=1e-6,
        feature_scale=8,
        tensor_dim="2D",
        path_pre_trained_model=None,
        criterion="cross_entropy",
        type="classifier",
        nonlocal_mode="concatenation_mean_flow",
        attention_dsample=(2, 2, 2),
        aggregation_mode="mean",
        checkpoints_dir=str(tmpdir),
        experiment_name="classification-smoke",
    )


def build_segmentation_opts(tmpdir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        gpu_ids=[0],
        isTrain=True,
        continue_train=False,
        which_epoch=0,
        save_dir=str(tmpdir / "segmentation"),
        model_type="unet_ct_dsv",
        input_nc=1,
        output_nc=4,
        lr_rate=1e-4,
        l2_reg_weight=1e-6,
        feature_scale=4,
        tensor_dim="3D",
        path_pre_trained_model=None,
        criterion="dice_loss",
        type="seg",
        nonlocal_mode="concatenation",
        attention_dsample=(2, 2, 2),
        aggregation_mode="concat",
        checkpoints_dir=str(tmpdir),
        experiment_name="segmentation-smoke",
    )


def build_us_aug_opts() -> SimpleNamespace:
    return SimpleNamespace(
        us=SimpleNamespace(
            patch_size=[208, 272],
            shift=[0.02, 0.02],
            rotate=25.0,
            scale=[0.7, 1.3],
            intensity=[1.0, 1.0],
            random_flip_prob=0.5,
        )
    )


def build_acdc_aug_opts() -> SimpleNamespace:
    return SimpleNamespace(
        acdc_sax=SimpleNamespace(
            shift=[0.1, 0.1],
            rotate=15.0,
            scale=[0.7, 1.3],
            intensity=[1.0, 1.0],
            random_flip_prob=0.5,
            scale_size=[16, 16, 16],
            patch_size=[16, 16, 16],
        )
    )


def run_import_smoke() -> None:
    import torch  # noqa: F401
    import torchvision  # noqa: F401
    import torchsample  # noqa: F401
    import dataio  # noqa: F401
    import models  # noqa: F401
    import utils  # noqa: F401
    import visdom  # noqa: F401
    import SimpleITK  # noqa: F401
    print("imports-ok")


def run_cuda_smoke() -> None:
    import torch

    print(f"torch={torch.__version__}")
    print(f"cuda={torch.version.cuda}")
    print(f"available={torch.cuda.is_available()}")
    print(f"devices={torch.cuda.device_count()}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available in the target environment")
    print(f"name={torch.cuda.get_device_name(0)}")
    print(f"capability={torch.cuda.get_device_capability(0)}")
    sample = torch.empty((1,), device="cuda:0")
    print(f"tensor_device={sample.device}")


def run_classification_smoke() -> None:
    import collections
    import collections.abc

    if not hasattr(collections, "Sequence"):
        collections.Sequence = collections.abc.Sequence

    import torch
    from dataio.transformation import get_dataset_transformation
    from models import get_model

    with tempfile.TemporaryDirectory(prefix="ag-net-classification-") as tmp:
        tmpdir = Path(tmp)
        aug = get_dataset_transformation("us", opts=build_us_aug_opts())
        if sorted(aug.keys()) != ["train", "valid"]:
            raise SystemExit(f"unexpected ultrasound transform keys: {sorted(aug.keys())}")

        model = get_model(build_classification_opts(tmpdir))
        model.net.eval()
        with torch.no_grad():
            output = model.net(torch.randn(2, 1, 32, 32, device="cuda:0"))
        print(f"classification-output={tuple(output.shape)}")

        att_cfg = build_classification_opts(tmpdir)
        att_cfg.type = "aggregated_classifier"
        att_cfg.model_type = "sononet_grid_attention"
        att_cfg.nonlocal_mode = "concatenation_mean_flow"
        att_cfg.aggregation_mode = "mean"
        att_cfg.weight = [1, 1, 1]
        att_cfg.aggregation = "mean"
        att_cfg.aggregation_param = 0
        att_model = get_model(att_cfg)
        att_model.net.eval()
        with torch.no_grad():
            att_output = att_model.net(torch.randn(2, 1, 32, 32, device="cuda:0"))
        shapes = [tuple(item.shape) for item in att_output] if isinstance(att_output, list) else [tuple(att_output.shape)]
        print(f"attention-classification-output={shapes}")


def run_segmentation_smoke() -> None:
    import torch
    from dataio.transformation import get_dataset_transformation
    from models import get_model

    with tempfile.TemporaryDirectory(prefix="ag-net-segmentation-") as tmp:
        tmpdir = Path(tmp)
        aug = get_dataset_transformation("acdc_sax", opts=build_acdc_aug_opts())
        if sorted(aug.keys()) != ["train", "valid"]:
            raise SystemExit(f"unexpected ACDC transform keys: {sorted(aug.keys())}")

        model = get_model(build_segmentation_opts(tmpdir))
        model.net.eval()
        with torch.no_grad():
            output = model.net(torch.randn(1, 1, 16, 16, 16, device="cuda:0"))
        print(f"segmentation-output={tuple(output.shape)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root to add to sys.path")
    parser.add_argument(
        "--config",
        help="Optional config to validate; relative paths are resolved from --repo-root",
    )
    parser.add_argument(
        "--mode",
        choices=("all", "imports", "cuda", "classification", "segmentation"),
        default="all",
        help="Which smoke checks to run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = add_repo_root(args.repo_root)
    if args.config:
        check_config_data_paths(args.config, repo_root)

    if args.mode in ("all", "imports"):
        run_import_smoke()
    if args.mode in ("all", "cuda"):
        run_cuda_smoke()
    if args.mode in ("all", "classification"):
        run_classification_smoke()
    if args.mode in ("all", "segmentation"):
        run_segmentation_smoke()

    print("check-env-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
