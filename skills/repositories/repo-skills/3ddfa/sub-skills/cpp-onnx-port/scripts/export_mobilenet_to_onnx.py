#!/usr/bin/env python3
"""Export a 3DDFA MobileNet checkpoint to ONNX for the C++ OpenCV DNN port.

The script intentionally imports PyTorch only after argparse has parsed the
command line, so `--help` remains usable in lightweight environments.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ARCH_CHOICES = ("mobilenet_2", "mobilenet_1", "mobilenet_075", "mobilenet_05", "mobilenet_025")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a 3DDFA MobileNet checkpoint to ONNX for the optional C++ OpenCV DNN demo."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to a 3DDFA checkout or source tree containing mobilenet_v1.py or c++/mobilenet_v1.py.",
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        type=Path,
        help="Checkpoint path. Relative paths are resolved against --repo-root.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output ONNX path. Relative paths are resolved against --repo-root.",
    )
    parser.add_argument(
        "--arch",
        default="mobilenet_1",
        choices=ARCH_CHOICES,
        help="MobileNet factory name from mobilenet_v1.py. Default: mobilenet_1.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=62,
        help="Output dimension for 3DDFA parameters. Keep 62 for the stock C++ port. Default: 62.",
    )
    parser.add_argument(
        "--checkpoint-key",
        default="state_dict",
        help="Dictionary key containing model weights when the checkpoint is a training bundle. Default: state_dict.",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=11,
        help="ONNX opset version. Use a lower value such as 9 only for older OpenCV DNN builds. Default: 11.",
    )
    parser.add_argument(
        "--input-channels",
        type=int,
        default=3,
        help="Dummy input channels for ONNX export. Default: 3.",
    )
    parser.add_argument(
        "--input-height",
        type=int,
        default=120,
        help="Dummy input height for the stock C++ predictor. Default: 120.",
    )
    parser.add_argument(
        "--input-width",
        type=int,
        default=120,
        help="Dummy input width for the stock C++ predictor. Default: 120.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Allow missing model keys by leaving initialization in place. Unsafe for production export.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and remap the checkpoint, report key coverage, but do not write ONNX.",
    )
    return parser


def resolve_under_repo(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def import_torch():
    try:
        import torch  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "PyTorch is required for ONNX export. Install torch in the active environment; "
            "`--help` does not require torch."
        ) from exc
    return torch


def import_mobilenet(repo_root: Path):
    candidates = [repo_root, repo_root / "c++"]
    for candidate in candidates:
        if (candidate / "mobilenet_v1.py").is_file():
            sys.path.insert(0, str(candidate))
            try:
                return importlib.import_module("mobilenet_v1")
            finally:
                try:
                    sys.path.remove(str(candidate))
                except ValueError:
                    pass
    raise SystemExit("mobilenet_v1.py was not found under --repo-root or --repo-root/c++.")


def strip_module_prefix(key: str) -> str:
    while key.startswith("module."):
        key = key[len("module.") :]
    return key


def remap_key(key: str) -> str:
    key = strip_module_prefix(key)
    if key == "fc_param.weight":
        return "fc.weight"
    if key == "fc_param.bias":
        return "fc.bias"
    return key


def is_tensor_dict(value) -> bool:
    return isinstance(value, dict) and bool(value) and all(hasattr(v, "shape") for v in value.values())


def extract_state_dict(checkpoint, checkpoint_key: str):
    if isinstance(checkpoint, dict) and checkpoint_key in checkpoint:
        state_dict = checkpoint[checkpoint_key]
        if not isinstance(state_dict, dict):
            raise SystemExit(f"Checkpoint key {checkpoint_key!r} exists but is not a state dict.")
        return state_dict
    if is_tensor_dict(checkpoint):
        return checkpoint
    if isinstance(checkpoint, dict):
        keys = ", ".join(str(k) for k in list(checkpoint.keys())[:20])
        raise SystemExit(
            f"Checkpoint does not contain key {checkpoint_key!r} and is not a raw tensor state dict. "
            f"Available top-level keys include: {keys}"
        )
    raise SystemExit("Checkpoint is not a dictionary or tensor state dict.")


def tensor_shape(tensor) -> Tuple[int, ...]:
    return tuple(int(x) for x in tensor.shape)


def remap_state_dict(state_dict, model_state) -> Tuple[Dict[str, object], List[str], List[str], List[str]]:
    remapped: Dict[str, object] = {}
    skipped: List[str] = []
    mismatched: List[str] = []
    duplicates: List[str] = []

    for source_key, tensor in state_dict.items():
        target_key = remap_key(str(source_key))
        if target_key not in model_state:
            skipped.append(f"{source_key} -> {target_key}")
            continue
        if tensor_shape(tensor) != tensor_shape(model_state[target_key]):
            mismatched.append(
                f"{source_key} -> {target_key}: checkpoint {tensor_shape(tensor)} != model {tensor_shape(model_state[target_key])}"
            )
            continue
        if target_key in remapped:
            duplicates.append(f"{source_key} -> {target_key}")
            continue
        remapped[target_key] = tensor

    return remapped, skipped, mismatched, duplicates


def is_noncritical_missing(key: str) -> bool:
    return key.endswith(".num_batches_tracked")


def print_lines(title: str, lines: Iterable[str], limit: int = 30) -> None:
    lines = list(lines)
    if not lines:
        return
    print(f"\n{title} ({len(lines)}):")
    for line in lines[:limit]:
        print(f"  - {line}")
    if len(lines) > limit:
        print(f"  ... {len(lines) - limit} more")


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.expanduser().resolve()
    checkpoint_path = resolve_under_repo(repo_root, args.checkpoint).expanduser().resolve()
    output_path = resolve_under_repo(repo_root, args.output).expanduser().resolve()

    if not repo_root.is_dir():
        parser.error(f"--repo-root is not a directory: {repo_root}")
    if not checkpoint_path.is_file():
        parser.error(f"--checkpoint is not a file: {checkpoint_path}")
    if args.num_classes <= 0:
        parser.error("--num-classes must be positive")
    if args.input_channels <= 0 or args.input_height <= 0 or args.input_width <= 0:
        parser.error("input dimensions must be positive")

    torch = import_torch()
    mobilenet_v1 = import_mobilenet(repo_root)

    if not hasattr(mobilenet_v1, args.arch):
        parser.error(f"mobilenet_v1.py does not expose architecture {args.arch!r}")

    checkpoint = torch.load(str(checkpoint_path), map_location="cpu")
    state_dict = extract_state_dict(checkpoint, args.checkpoint_key)

    model_factory = getattr(mobilenet_v1, args.arch)
    model = model_factory(num_classes=args.num_classes, input_channel=args.input_channels)
    model.eval()
    model_state = model.state_dict()

    remapped, skipped, mismatched, duplicates = remap_state_dict(state_dict, model_state)
    if mismatched:
        print_lines("Shape mismatches", mismatched)
        raise SystemExit("Refusing to export because checkpoint tensor shapes do not match the selected architecture.")
    if duplicates:
        print_lines("Duplicate target keys", duplicates)
        raise SystemExit("Refusing to export because multiple checkpoint keys map to the same model key.")

    missing = sorted(k for k in model_state.keys() if k not in remapped)
    critical_missing = [k for k in missing if not is_noncritical_missing(k)]
    if critical_missing and not args.allow_missing:
        print_lines("Missing model keys after remapping", critical_missing)
        raise SystemExit("Refusing to export an incomplete model. Pass --allow-missing only for diagnostics.")

    load_state = dict(model_state)
    load_state.update(remapped)
    model.load_state_dict(load_state, strict=True)

    print(f"Loaded checkpoint: {checkpoint_path}")
    print(f"Architecture: {args.arch}(num_classes={args.num_classes}, input_channel={args.input_channels})")
    print(f"Remapped tensors loaded: {len(remapped)} / {len(model_state)} model tensors")
    print_lines("Skipped checkpoint keys", skipped)
    if missing:
        print_lines("Model keys left at initialization", missing)

    if args.dry_run:
        print("Dry run requested; ONNX export was not written.")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_input = torch.randn(1, args.input_channels, args.input_height, args.input_width)
    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        export_params=True,
        opset_version=args.opset,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["params"],
    )
    print(f"Wrote ONNX: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
