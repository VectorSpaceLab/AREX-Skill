#!/usr/bin/env python3
"""Safe, no-download preflight for mergekit model references and checkpoints.

This script deliberately does not call Hub download APIs, load model classes,
execute remote code, materialize checkpoint tensors, or write files. It can be
run from any working directory with the installed mergekit environment.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Iterable


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse mergekit references and inspect local checkpoint indexes "
            "without downloads, model loading, or output writes."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run package/device checks (also implied by --device or --checkpoint)",
    )
    parser.add_argument(
        "--model-ref",
        action="append",
        default=[],
        metavar="MODEL[@REV][+LORA[@REV]]",
        help="reference to parse; repeat for multiple inputs",
    )
    parser.add_argument(
        "--checkpoint",
        action="append",
        default=[],
        metavar="DIR",
        help="local checkpoint directory to index; repeat to inspect several",
    )
    parser.add_argument(
        "--device",
        default=None,
        metavar="DEVICE",
        help="device to report, for example cpu, cuda, cuda:0, or auto",
    )
    parser.add_argument(
        "--allocate",
        action="store_true",
        help="with a CUDA device, perform one tiny allocation (still no model load)",
    )
    return parser


def _parse_references(values: Iterable[str]) -> int:
    if not values:
        return 0
    try:
        from mergekit.common import ModelReference
    except Exception as exc:  # pragma: no cover - environment-specific
        print(f"reference check: cannot import mergekit ({type(exc).__name__}: {exc})")
        return 1

    failed = 0
    for value in values:
        try:
            ref = ModelReference.parse(value)
            print(
                "reference: OK "
                f"{value!r} -> model={ref.model.path!r} "
                f"revision={ref.model.revision!r} "
                f"lora={str(ref.lora) if ref.lora else None!r}"
            )
        except Exception as exc:
            failed += 1
            print(f"reference: FAIL {value!r}: {type(exc).__name__}: {exc}")
    return failed


def _checkpoint(path_text: str) -> int:
    """Inspect metadata without invoking torch.load on a legacy BIN file."""
    path = Path(path_text).expanduser().resolve()
    safe_file = path / "model.safetensors"
    safe_index_file = Path(os.fspath(safe_file) + ".index.json")
    bin_file = path / "pytorch_model.bin"
    bin_index_file = Path(os.fspath(bin_file) + ".index.json")

    try:
        if safe_file.exists() or safe_index_file.exists():
            # safe_open only reads safetensors metadata/data and never unpickles.
            from mergekit.io.lazy_tensor_loader import ShardedTensorIndex

            index = ShardedTensorIndex.from_disk(os.fspath(path))
            missing = sorted(
                {
                    os.fspath(path / shard)
                    for shard in index.tensor_paths.values()
                    if not (path / shard).exists()
                }
            )
            if missing:
                print(
                    f"checkpoint: FAIL {path}: missing indexed shard(s): "
                    + ", ".join(missing)
                )
                return 1
            print(
                f"checkpoint: OK {path} format=safetensors "
                f"tensors={len(index.tensor_paths)} shards={len(index.shards)}"
            )
            for shard in index.shards:
                print(f"  shard: {shard.filename} tensors={len(shard.contained_keys)}")
            return 0

        if bin_index_file.exists():
            # Do not call ShardedTensorIndex.from_disk here: its single-file BIN
            # fallback uses torch.load, which is not appropriate for an
            # untrusted preflight input. The index JSON is inert metadata.
            data = json.loads(bin_index_file.read_text(encoding="utf-8"))
            weight_map = data["weight_map"]
            shard_names = sorted(set(weight_map.values()))
            missing = [name for name in shard_names if not (path / name).exists()]
            if missing:
                print(
                    f"checkpoint: FAIL {path}: missing indexed shard(s): "
                    + ", ".join(missing)
                )
                return 1
            print(
                f"checkpoint: OK {path} format=pytorch-bin indexed "
                f"tensors={len(weight_map)} shards={len(shard_names)}"
            )
            for shard in shard_names:
                print(
                    f"  shard: {shard} tensors="
                    f"{sum(name == shard for name in weight_map.values())}"
                )
            return 0

        if bin_file.exists():
            print(
                f"checkpoint: OK {path} format=pytorch-bin single-shard "
                "tensors=unknown (not enumerated by safe preflight)"
            )
            return 0

        raise FileNotFoundError(
            "expected model.safetensors, model.safetensors.index.json, "
            "pytorch_model.bin, or pytorch_model.bin.index.json"
        )
    except Exception as exc:
        print(f"checkpoint: FAIL {path}: {type(exc).__name__}: {exc}")
        return 1


def _device(device_text: str | None, allocate: bool) -> int:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment-specific
        print(f"device: cannot import torch ({type(exc).__name__}: {exc})")
        return 1

    requested = device_text or "cpu"
    selected = requested
    if requested == "auto":
        if torch.cuda.is_available():
            selected = "cuda"
        elif hasattr(torch, "xpu") and torch.xpu.is_available():
            selected = "xpu"
        else:
            selected = "cpu"

    print(
        f"device: requested={requested} selected={selected} "
        f"torch={getattr(torch, '__version__', 'unknown')} "
        f"torch_cuda={torch.version.cuda!r}"
    )
    if hasattr(torch, "cuda"):
        print(
            f"  cuda_available={torch.cuda.is_available()} "
            f"device_count={torch.cuda.device_count()}"
        )

    if selected.startswith("cuda"):
        if not torch.cuda.is_available():
            print("device: FAIL CUDA is unavailable")
            return 1
        try:
            index = torch.device(selected).index
            if index is None:
                index = torch.cuda.current_device()
            name = torch.cuda.get_device_name(index)
            capability = torch.cuda.get_device_capability(index)
            print(f"  cuda_device={index} name={name!r} capability={capability}")
            if allocate:
                probe = torch.zeros(1, device=torch.device(selected))
                print(f"  allocation=OK dtype={probe.dtype} device={probe.device}")
                del probe
        except Exception as exc:
            print(f"device: FAIL {type(exc).__name__}: {exc}")
            return 1
    return 0


def _package_check() -> int:
    names = ["mergekit", "torch", "transformers", "safetensors", "huggingface_hub"]
    failed = 0
    for name in names:
        try:
            print(f"package: {name}={importlib.metadata.version(name)}")
        except importlib.metadata.PackageNotFoundError:
            failed += 1
            print(f"package: MISSING {name}")
    return failed


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not (args.check or args.model_ref or args.checkpoint or args.device):
        print("tiny check: no network, model load, or output write requested")
        return 0

    failed = 0
    if args.check:
        failed += _package_check()
    failed += _parse_references(args.model_ref)
    for path in args.checkpoint:
        failed += _checkpoint(path)
    if args.device or args.allocate:
        failed += _device(args.device, args.allocate)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
