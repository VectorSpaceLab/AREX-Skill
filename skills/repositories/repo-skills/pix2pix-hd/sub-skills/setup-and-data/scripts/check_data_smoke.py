#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
import tempfile

sys.dont_write_bytecode = True
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_cityscapes_layout import LayoutError, validate_cityscapes_layout


class SmokeError(RuntimeError):
    pass


def fail(message: str, code: int = 2) -> int:
    print(message, file=sys.stderr)
    return code


def require_module(module_name: str, hint: str):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised through CLI
        raise SmokeError(f"[missing-dependency] could not import {module_name}: {exc}\n{hint}") from exc


def prepare_repo_root(repo_root: str) -> Path:
    root = Path(repo_root).expanduser().resolve()
    required = [
        "README.md",
        "options/train_options.py",
        "options/test_options.py",
        "data/aligned_dataset.py",
        "data/base_dataset.py",
        "data/image_folder.py",
        "util/util.py",
        "datasets/cityscapes",
    ]
    missing = [rel for rel in required if not (root / rel).exists()]
    if missing:
        raise SmokeError(
            f"[invalid-repo-root] {root} is missing required pix2pixHD files: {', '.join(missing)}"
        )
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def parse_with_argv(option_cls, argv):
    old_argv = sys.argv[:]
    sys.argv = [old_argv[0], *argv]
    try:
        return option_cls().parse(save=False)
    finally:
        sys.argv = old_argv


def smoke_train_sample(repo_root: Path, tmp_root: Path):
    from options.train_options import TrainOptions
    from data.aligned_dataset import AlignedDataset
    from util import util

    dataroot = repo_root / "datasets" / "cityscapes"
    train_opt = parse_with_argv(
        TrainOptions,
        [
            "--gpu_ids",
            "-1",
            "--checkpoints_dir",
            str(tmp_root / "checkpoints"),
            "--dataroot",
            str(dataroot),
            "--name",
            "setup-and-data-train-smoke",
            "--batchSize",
            "1",
            "--nThreads",
            "0",
            "--serial_batches",
            "--no_flip",
            "--resize_or_crop",
            "scale_width",
        ],
    )
    if not train_opt.isTrain:
        raise SmokeError("[parser-error] TrainOptions did not set isTrain=True")
    dataset = AlignedDataset()
    dataset.initialize(train_opt)
    if len(dataset) <= 0:
        raise SmokeError("[data-error] training fixture produced an empty dataset; keep batchSize=1 for tiny smoke checks")
    sample = dataset[0]
    expected_keys = {"label", "inst", "image", "feat", "path"}
    if set(sample) != expected_keys:
        raise SmokeError(f"[data-error] unexpected train sample keys: {sorted(sample)}")
    if sample["label"].shape[0] != 1 or sample["inst"].shape[0] != 1 or sample["image"].shape[0] != 3:
        raise SmokeError(
            f"[data-error] unexpected train tensor channels: label={tuple(sample['label'].shape)}, inst={tuple(sample['inst'].shape)}, image={tuple(sample['image'].shape)}"
        )
    if not sample["path"].endswith("_gtFine_labelIds.png"):
        raise SmokeError(f"[data-error] train sample path does not point at a label map: {sample['path']}")
    if sample["feat"] != 0:
        raise SmokeError(f"[data-error] train smoke expected feat=0 when load_features=False, got: {sample['feat']!r}")
    label_vis = util.tensor2label(sample["label"], train_opt.label_nc)
    image_vis = util.tensor2im(sample["image"])
    if label_vis.shape[-1] != 3 or image_vis.shape[-1] != 3:
        raise SmokeError(
            f"[data-error] tensor2label/tensor2im did not return RGB outputs: label={label_vis.shape}, image={image_vis.shape}"
        )
    print(
        f"[ok] train smoke: dataset_len={len(dataset)} label={tuple(sample['label'].shape)} inst={tuple(sample['inst'].shape)} image={tuple(sample['image'].shape)}"
    )
    print(f"[ok] train smoke: tensor2label={label_vis.shape} tensor2im={image_vis.shape}")


def smoke_test_sample(repo_root: Path, tmp_root: Path):
    from options.test_options import TestOptions
    from data.aligned_dataset import AlignedDataset
    from util import util

    dataroot = repo_root / "datasets" / "cityscapes"
    test_opt = parse_with_argv(
        TestOptions,
        [
            "--gpu_ids",
            "-1",
            "--checkpoints_dir",
            str(tmp_root / "checkpoints"),
            "--results_dir",
            str(tmp_root / "results"),
            "--dataroot",
            str(dataroot),
            "--name",
            "setup-and-data-test-smoke",
            "--batchSize",
            "1",
            "--nThreads",
            "1",
            "--serial_batches",
            "--no_flip",
        ],
    )
    if test_opt.isTrain:
        raise SmokeError("[parser-error] TestOptions did not set isTrain=False")
    dataset = AlignedDataset()
    dataset.initialize(test_opt)
    if len(dataset) <= 0:
        raise SmokeError("[data-error] test fixture produced an empty dataset; keep batchSize=1 for tiny smoke checks")
    sample = dataset[0]
    if sample["image"] != 0:
        raise SmokeError(f"[data-error] test smoke expected image=0 when use_encoded_image=False, got: {sample['image']!r}")
    if sample["feat"] != 0:
        raise SmokeError(f"[data-error] test smoke expected feat=0 when load_features=False, got: {sample['feat']!r}")
    if sample["path"].endswith("_gtFine_labelIds.png") is False:
        raise SmokeError(f"[data-error] test sample path does not point at a label map: {sample['path']}")
    label_vis = util.tensor2label(sample["label"], test_opt.label_nc)
    if label_vis.shape[-1] != 3:
        raise SmokeError(f"[data-error] tensor2label did not return an RGB output for the test sample: {label_vis.shape}")
    print(
        f"[ok] test smoke: dataset_len={len(dataset)} label={tuple(sample['label'].shape)} inst={tuple(sample['inst'].shape)} image={sample['image']!r}"
    )
    print(f"[ok] test smoke: tensor2label={label_vis.shape} path={sample['path']}")


def probe_legacy_resize():
    from data.base_dataset import get_transform

    legacy_opt = SimpleNamespace(
        resize_or_crop="resize_and_crop",
        loadSize=4,
        fineSize=2,
        isTrain=False,
        no_flip=True,
        n_downsample_global=4,
        n_local_enhancers=1,
        netG="global",
    )
    try:
        transform = get_transform(legacy_opt, {"crop_pos": (0, 0), "flip": False}, normalize=False)
        print("[ok] legacy resize probe: torchvision still provides the resize path")
        return transform
    except Exception as exc:
        print(f"[warning] legacy resize probe failed: {exc}")
        print(
            "[warning] recovery path: keep resize_or_crop=scale_width (default), use scale_width_and_crop/crop, or patch data/base_dataset.py to torchvision.transforms.Resize"
        )
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe pix2pixHD parser and one-sample data smoke checks.")
    parser.add_argument("--repo-root", required=True, help="Path to the pix2pixHD repository root.")
    parser.add_argument("--probe-legacy-resize", action="store_true", help="Also probe the deprecated resize_and_crop path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        repo_root = prepare_repo_root(args.repo_root)
        validate_cityscapes_layout(repo_root, phases=("train", "test"), label_nc=35, no_instance=False, use_encoded_image=False)
        print("[ok] bundled Cityscapes layout validated")
        with tempfile.TemporaryDirectory(prefix="pix2pixhd-setup-and-data-") as tmp_dir:
            tmp_root = Path(tmp_dir)
            require_module("torch", "Install a compatible PyTorch wheel. Data smoke is CPU-safe when gpu_ids=-1.")
            require_module("torchvision", "Install torchvision that matches the installed torch wheel.")
            require_module("PIL.Image", "Install Pillow for image loading.")
            try:
                from options.train_options import TrainOptions
                from options.test_options import TestOptions
                from data.aligned_dataset import AlignedDataset
                from util import util
            except ModuleNotFoundError as exc:
                raise SmokeError(
                    f"[missing-dependency] could not import repo modules from {repo_root}: {exc}\n"
                    "Use --repo-root to point at the pix2pixHD checkout or expose the checkout via PYTHONPATH / .pth."
                ) from exc
            _ = (TrainOptions, TestOptions, AlignedDataset, util)
            smoke_train_sample(repo_root, tmp_root)
            smoke_test_sample(repo_root, tmp_root)
            if args.probe_legacy_resize:
                probe_legacy_resize()
        print("[ok] setup-and-data smoke completed")
        return 0
    except LayoutError as exc:
        return fail(str(exc))
    except SmokeError as exc:
        return fail(str(exc))
    except Exception as exc:
        return fail(f"[unexpected-error] {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
