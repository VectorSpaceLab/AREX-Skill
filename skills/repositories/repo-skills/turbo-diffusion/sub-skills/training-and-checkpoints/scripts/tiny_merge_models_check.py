#!/usr/bin/env python3
"""Run a tiny CPU-only check of TurboDiffusion merge arithmetic."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import torch
except Exception as exc:  # noqa: BLE001 - provide clear optional dependency message.
    print(f"PyTorch is required for the tiny merge check: {exc}", file=sys.stderr)
    raise SystemExit(2)


def torch_load(path: Path) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def source_like_merge(base_sd: dict[str, Any], diff_base_sd: dict[str, Any], diff_target_sd: dict[str, Any], weight: float) -> dict[str, Any]:
    """Mirror the public merge_models.py key/shape behavior on already-loaded dicts."""
    merged_sd: dict[str, Any] = {}
    for key, base_tensor in base_sd.items():
        if not isinstance(base_tensor, torch.Tensor):
            merged_sd[key] = base_tensor
            continue

        if key in diff_base_sd and key in diff_target_sd:
            d_base_tensor = diff_base_sd[key]
            d_target_tensor = diff_target_sd[key]
            if (
                not isinstance(d_base_tensor, torch.Tensor)
                or not isinstance(d_target_tensor, torch.Tensor)
                or base_tensor.shape != d_base_tensor.shape
                or base_tensor.shape != d_target_tensor.shape
            ):
                merged_sd[key] = base_tensor
                continue
            with torch.no_grad():
                result = base_tensor.float() + weight * (d_target_tensor.float() - d_base_tensor.float())
            merged_sd[key] = result.to(base_tensor.dtype)
        else:
            merged_sd[key] = base_tensor

    for key, target_tensor in diff_target_sd.items():
        if key not in merged_sd:
            merged_sd[key] = target_tensor
    return merged_sd


def build_fixture(root: Path) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    base = {
        "formula.weight": torch.tensor([1.0, 2.0], dtype=torch.float32),
        "kept_missing.weight": torch.tensor([5.0], dtype=torch.float32),
        "shape_mismatch.weight": torch.tensor([7.0, 8.0], dtype=torch.float32),
        "non_tensor_meta": "kept-from-base",
    }
    diff_base = {
        "formula.weight": torch.tensor([0.5, 1.0], dtype=torch.float32),
        "shape_mismatch.weight": torch.tensor([1.0, 2.0], dtype=torch.float32),
    }
    diff_target = {
        "formula.weight": torch.tensor([1.5, 3.0], dtype=torch.float32),
        "shape_mismatch.weight": torch.tensor([3.0], dtype=torch.float32),
        "target_only.weight": torch.tensor([9.0], dtype=torch.float32),
    }
    base_path = root / "base.pth"
    diff_base_path = root / "diff_base.pth"
    diff_target_path = root / "diff_target.pth"
    torch.save(base, base_path)
    torch.save(diff_base, diff_base_path)
    torch.save(diff_target, diff_target_path)
    return base_path, diff_base_path, diff_target_path


def run_check(root: Path, weight: float, verbose: bool) -> Path:
    base_path, diff_base_path, diff_target_path = build_fixture(root)
    merged = source_like_merge(
        torch_load(base_path),
        torch_load(diff_base_path),
        torch_load(diff_target_path),
        weight,
    )
    output_path = root / "merged.pth"
    torch.save(merged, output_path)

    expected_formula = torch.tensor([1.0, 2.0]) + weight * (torch.tensor([1.5, 3.0]) - torch.tensor([0.5, 1.0]))
    assert torch.allclose(merged["formula.weight"], expected_formula), merged["formula.weight"]
    assert torch.equal(merged["kept_missing.weight"], torch.tensor([5.0])), merged["kept_missing.weight"]
    assert torch.equal(merged["shape_mismatch.weight"], torch.tensor([7.0, 8.0])), merged["shape_mismatch.weight"]
    assert merged["non_tensor_meta"] == "kept-from-base", merged["non_tensor_meta"]
    assert torch.equal(merged["target_only.weight"], torch.tensor([9.0])), merged["target_only.weight"]

    if verbose:
        print(f"fixture_dir={root}")
        print(f"base={base_path}")
        print(f"diff_base={diff_base_path}")
        print(f"diff_target={diff_target_path}")
        print(f"merged={output_path}")
        print(f"formula.weight={merged['formula.weight'].tolist()}")
        print(f"shape_mismatch.weight={merged['shape_mismatch.weight'].tolist()}")
        print(f"target_only.weight={merged['target_only.weight'].tolist()}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create tiny temporary .pth checkpoints and verify TurboDiffusion's merge formula on CPU. "
            "No repository checkout, downloads, model execution, or GPU is required."
        )
    )
    parser.add_argument("--weight", type=float, default=0.25, help="Merge weight w used in base + w * (diff_target - diff_base).")
    parser.add_argument("--keep-dir", action="store_true", help="Keep the temporary fixture directory and print its path.")
    parser.add_argument("--output-dir", help="Use this fixture directory instead of creating a temporary one.")
    parser.add_argument("--verbose", action="store_true", help="Print fixture files and merged tensor values.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    cleanup = False
    if args.output_dir:
        root = Path(args.output_dir)
        root.mkdir(parents=True, exist_ok=True)
    else:
        root = Path(tempfile.mkdtemp(prefix="turbodiffusion-merge-check-"))
        cleanup = not args.keep_dir

    try:
        output_path = run_check(root, args.weight, args.verbose)
        print(f"OK: tiny merge arithmetic check passed (w={args.weight}, output={output_path})")
        if args.keep_dir or args.output_dir:
            print(f"fixture_dir={root}")
        return 0
    finally:
        if cleanup:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
