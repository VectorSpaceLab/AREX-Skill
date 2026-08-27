#!/usr/bin/env python3
"""Check a BEVFormer checkout, import stack, and optional config summary.

This helper is read-only and safe to run from any working directory.
Pass --repo-root when the checkout is not already on PYTHONPATH.

Examples:
  python check_bevformer_environment.py --repo-root /path/to/BEVFormer --config projects/configs/bevformer/bevformer_tiny.py
  python check_bevformer_environment.py --repo-root /path/to/BEVFormer --skip-config
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

REQUIRED_MODULES: Sequence[str] = (
    "projects.mmdet3d_plugin",
    "projects.mmdet3d_plugin.bevformer.detectors.bevformer",
    "projects.mmdet3d_plugin.bevformer.detectors.bevformerV2",
    "projects.mmdet3d_plugin.bevformer.dense_heads.bevformer_head",
    "projects.mmdet3d_plugin.bevformer.modules.transformer",
    "projects.mmdet3d_plugin.bevformer.modules.transformerV2",
    "projects.mmdet3d_plugin.bevformer.modules.encoder",
    "projects.mmdet3d_plugin.bevformer.modules.spatial_cross_attention",
    "projects.mmdet3d_plugin.bevformer.modules.temporal_self_attention",
    "projects.mmdet3d_plugin.datasets.nuscenes_dataset",
    "projects.mmdet3d_plugin.datasets.nuscenes_dataset_v2",
    "projects.mmdet3d_plugin.core.bbox.coders.nms_free_coder",
    "projects.mmdet3d_plugin.core.bbox.assigners.hungarian_assigner_3d",
)

VERSION_MODULES: Sequence[str] = ("torch", "mmcv", "mmdet", "mmseg", "mmdet3d")

SYMBOLS: Sequence[Tuple[str, str]] = (
    ("projects.mmdet3d_plugin.bevformer.detectors.bevformer", "BEVFormer"),
    ("projects.mmdet3d_plugin.bevformer.detectors.bevformerV2", "BEVFormerV2"),
    ("projects.mmdet3d_plugin.bevformer.dense_heads.bevformer_head", "BEVFormerHead"),
    ("projects.mmdet3d_plugin.bevformer.modules.transformer", "PerceptionTransformer"),
    ("projects.mmdet3d_plugin.bevformer.modules.transformerV2", "PerceptionTransformerV2"),
    ("projects.mmdet3d_plugin.bevformer.modules.encoder", "BEVFormerEncoder"),
    ("projects.mmdet3d_plugin.bevformer.modules.encoder", "BEVFormerLayer"),
    ("projects.mmdet3d_plugin.bevformer.modules.temporal_self_attention", "TemporalSelfAttention"),
    ("projects.mmdet3d_plugin.bevformer.modules.spatial_cross_attention", "SpatialCrossAttention"),
    ("projects.mmdet3d_plugin.bevformer.modules.spatial_cross_attention", "MSDeformableAttention3D"),
    ("projects.mmdet3d_plugin.datasets.nuscenes_dataset", "CustomNuScenesDataset"),
    ("projects.mmdet3d_plugin.datasets.nuscenes_dataset_v2", "CustomNuScenesDatasetV2"),
    ("projects.mmdet3d_plugin.core.bbox.coders.nms_free_coder", "NMSFreeCoder"),
    ("projects.mmdet3d_plugin.core.bbox.assigners.hungarian_assigner_3d", "HungarianAssigner3D"),
)

DEFAULT_CONFIG = "projects/configs/bevformer/bevformer_tiny.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the BEVFormer environment, imports, and an optional config summary.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python check_bevformer_environment.py --repo-root /path/to/BEVFormer\n"
            "  python check_bevformer_environment.py --repo-root /path/to/BEVFormer --config projects/configs/bevformerv2/bevformerv2-r50-t1-base-24ep.py\n"
        ),
    )
    parser.add_argument(
        "--repo-root",
        help="Path to the BEVFormer checkout. If omitted, the current working directory is used.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help="Config path to summarize relative to --repo-root or the current working directory.",
    )
    parser.add_argument(
        "--skip-config",
        action="store_true",
        help="Skip config parsing and only check imports, symbols, and CUDA.",
    )
    parser.add_argument(
        "--skip-cuda",
        action="store_true",
        help="Skip the torch CUDA smoke even if torch is installed.",
    )
    return parser.parse_args()


def add_repo_root(repo_root: Optional[str]) -> Path:
    root = Path(repo_root).expanduser().resolve() if repo_root else Path.cwd().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def resolve_path(raw: str, repo_root: Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def try_import(module_name: str):
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - surfaced directly to the user
        return None, exc


def print_module_versions() -> bool:
    ok = True
    for module_name in VERSION_MODULES:
        module, error = try_import(module_name)
        if error is not None:
            print(f"[missing] {module_name}: {error}")
            ok = False
            continue
        version = getattr(module, "__version__", "<unknown>")
        print(f"[ok] {module_name} {version}")
    return ok


def print_required_modules() -> bool:
    ok = True
    for module_name in REQUIRED_MODULES:
        _, error = try_import(module_name)
        if error is not None:
            print(f"[missing] {module_name}: {error}")
            ok = False
        else:
            print(f"[ok] {module_name}")
    return ok


def describe_signature(module_name: str, symbol: str) -> str:
    module, error = try_import(module_name)
    if error is not None:
        return f"{module_name}.{symbol}: <module missing: {error}>"
    obj = getattr(module, symbol, None)
    if obj is None:
        return f"{module_name}.{symbol}: <symbol missing>"
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        signature = "<signature unavailable>"
    return f"{module_name}.{symbol}: {signature}"


def print_symbol_signatures() -> bool:
    ok = True
    for module_name, symbol in SYMBOLS:
        line = describe_signature(module_name, symbol)
        print(line)
        if "<module missing:" in line or "<symbol missing>" in line:
            ok = False
    return ok


def summarize_config(config_path: Path) -> bool:
    try:
        from mmcv import Config  # type: ignore
    except Exception as exc:
        print(f"[missing] mmcv.Config: {exc}")
        return False

    if not config_path.is_file():
        print(f"[missing] config file: {config_path}")
        return False

    try:
        cfg = Config.fromfile(str(config_path))
    except Exception as exc:
        print(f"[config-error] {config_path}: {exc}")
        return False

    print(f"[config] {config_path}")
    for key in ("plugin", "plugin_dir", "dataset_type", "data_root", "frames", "queue_length", "bev_h_", "bev_w_"):
        if key in cfg:
            print(f"  {key} = {cfg[key]!r}")

    model = cfg.get("model", {})
    if isinstance(model, dict):
        print(f"  model.type = {model.get('type', '<missing>')!r}")
        head = model.get("pts_bbox_head", {})
        if isinstance(head, dict):
            print(f"  pts_bbox_head.type = {head.get('type', '<missing>')!r}")
            transformer = head.get("transformer", {})
            if isinstance(transformer, dict):
                print(f"  transformer.type = {transformer.get('type', '<missing>')!r}")

    data = cfg.get("data", {})
    if isinstance(data, dict):
        for split in ("train", "val", "test"):
            split_cfg = data.get(split, {})
            if isinstance(split_cfg, dict) and "type" in split_cfg:
                print(f"  data.{split}.type = {split_cfg.get('type')!r}")
    return True


def smoke_cuda(skip_cuda: bool) -> bool:
    if skip_cuda:
        print("[skip] CUDA smoke")
        return True

    module, error = try_import("torch")
    if error is not None:
        print(f"[missing] torch: {error}")
        return False

    torch = module
    print(f"[torch] version={torch.__version__} cuda={getattr(torch.version, 'cuda', None)!r}")
    try:
        available = torch.cuda.is_available()
        count = torch.cuda.device_count() if available else 0
        print(f"[torch.cuda] available={available} device_count={count}")
        if available:
            print(
                f"[torch.cuda] device0={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}"
            )
            torch.empty((1,), device="cuda")
            print("[torch.cuda] tiny allocation succeeded")
    except Exception as exc:
        print(f"[torch.cuda-error] {exc}")
        return False
    return True


def main() -> int:
    args = parse_args()
    repo_root = add_repo_root(args.repo_root)
    print(f"repo-root: {repo_root}")

    imports_ok = print_module_versions()
    imports_ok = print_required_modules() and imports_ok
    imports_ok = print_symbol_signatures() and imports_ok
    config_ok = True
    if not args.skip_config:
        config_ok = summarize_config(resolve_path(args.config, repo_root))
    cuda_ok = smoke_cuda(args.skip_cuda)

    ok = imports_ok and config_ok and cuda_ok
    if ok:
        print("BEVFormer environment check: OK")
        return 0

    print("BEVFormer environment check: problems detected", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
