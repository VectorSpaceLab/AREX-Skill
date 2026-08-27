#!/usr/bin/env python3
"""CPU-safe smoke checks for vit-pytorch introspection/customization helpers.

Purpose:
  - verify Recorder attention capture and hook cleanup;
  - verify Extractor latent capture, missing-layer errors, and eject behavior;
  - verify efficient.ViT with a tiny token-preserving custom transformer;
  - verify parallel_vit and PyTorch-SDPA flash wrapper shapes when available.

Example:
  python sub-skills/introspection-and-customization/scripts/smoke_introspection.py

The script imports the installed vit_pytorch package. It does not read external
source files and does not require CUDA, downloads, external transformer packages,
or the external flash-attn package.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import warnings
from dataclasses import dataclass
from importlib import metadata
from typing import Callable, List, Optional

import torch
from torch import nn

# Avoid backend deprecation warnings printing local environment paths during the
# optional PyTorch SDPA smoke checks. Actual failures are still reported.
warnings.filterwarnings(
    "ignore",
    message=r".*torch\.backends\.cuda\.sdp_kernel.*",
    category=FutureWarning,
)


class SkipCheck(RuntimeError):
    """Raised when an optional check is not applicable in this runtime."""


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _assert_shape(tensor: torch.Tensor, expected: tuple[int, ...], name: str) -> None:
    actual = tuple(tensor.shape)
    if actual != expected:
        raise AssertionError(f"{name} shape {actual} != expected {expected}")


def _torch_version_tuple() -> tuple[int, int]:
    version = torch.__version__.split("+")[0]
    parts = version.split(".")
    try:
        return int(parts[0]), int(parts[1])
    except Exception:
        return (0, 0)


def _make_base_vit(num_classes: int = 5):
    from vit_pytorch.vit import ViT

    return ViT(
        image_size=16,
        patch_size=8,
        num_classes=num_classes,
        dim=32,
        depth=2,
        heads=4,
        mlp_dim=64,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )


def check_recorder() -> str:
    from vit_pytorch.recorder import Recorder

    torch.manual_seed(0)
    vit = _make_base_vit(num_classes=5).eval()
    img = torch.randn(2, 3, 16, 16)

    recorder = Recorder(vit)
    with torch.no_grad():
        logits, attn = recorder(img)

    _assert_shape(logits, (2, 5), "Recorder logits")
    if attn is None:
        raise AssertionError("Recorder returned None attention maps for base ViT")
    _assert_shape(attn, (2, 2, 4, 5, 5), "Recorder attention")

    original = recorder.eject()
    if original is not vit:
        raise AssertionError("Recorder.eject() did not return the original backbone")
    if recorder.hooks:
        raise AssertionError("Recorder.eject() left hook handles registered")

    try:
        recorder(img)
    except AssertionError as exc:
        if "ejected" not in str(exc):
            raise
    else:
        raise AssertionError("Ejected Recorder unexpectedly allowed forward")

    early = Recorder(_make_base_vit(num_classes=5).eval())
    early_backbone = early.eject()
    with torch.no_grad():
        early_logits = early_backbone(img)
    _assert_shape(early_logits, (2, 5), "Early-ejected backbone logits")

    return "base ViT attention shape, eject cleanup, and early-eject backbone path passed"


def check_extractor() -> str:
    from vit_pytorch.extractor import Extractor

    torch.manual_seed(1)
    vit = _make_base_vit(num_classes=6).eval()
    img = torch.randn(2, 3, 16, 16)

    extractor = Extractor(vit)
    with torch.no_grad():
        logits, latents = extractor(img)

    _assert_shape(logits, (2, 6), "Extractor logits")
    _assert_shape(latents, (2, 5, 32), "Extractor latents")

    original = extractor.eject()
    if original is not vit:
        raise AssertionError("Extractor.eject() did not return the original backbone")
    if extractor.hooks:
        raise AssertionError("Extractor.eject() left hook handles registered")
    try:
        extractor(img)
    except AssertionError as exc:
        if "ejected" not in str(exc):
            raise
    else:
        raise AssertionError("Ejected Extractor unexpectedly allowed forward")

    embeddings_only = Extractor(_make_base_vit(num_classes=6).eval(), return_embeddings_only=True)
    with torch.no_grad():
        only = embeddings_only(img)
    _assert_shape(only, (2, 5, 32), "Extractor return_embeddings_only latents")
    embeddings_only.eject()

    bad_layer = Extractor(_make_base_vit(num_classes=6).eval(), layer_name="does_not_exist")
    try:
        with torch.no_grad():
            bad_layer(img)
    except AssertionError as exc:
        if "layer whose output" not in str(exc):
            raise
    else:
        raise AssertionError("Extractor with a missing layer_name unexpectedly succeeded")

    return "latent shape, return_embeddings_only, missing-layer error, and eject behavior passed"


class TinyTokenMixer(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.net = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, dim))

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        if tokens.ndim != 3:
            raise AssertionError(f"expected 3D tokens, got shape {tuple(tokens.shape)}")
        return tokens + self.net(tokens)


class BadPooledTransformer(nn.Module):
    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        return tokens.mean(dim=1)


def check_efficient_vit_contract() -> str:
    from vit_pytorch.efficient import ViT as EfficientViT

    torch.manual_seed(2)
    img = torch.randn(2, 3, 16, 16)

    model = EfficientViT(
        image_size=16,
        patch_size=8,
        num_classes=7,
        dim=32,
        transformer=TinyTokenMixer(dim=32),
    ).eval()
    with torch.no_grad():
        logits = model(img)
    _assert_shape(logits, (2, 7), "efficient.ViT logits")

    bad = EfficientViT(
        image_size=16,
        patch_size=8,
        num_classes=7,
        dim=32,
        transformer=BadPooledTransformer(),
    ).eval()
    try:
        with torch.no_grad():
            bad(img)
    except Exception:
        pass
    else:
        raise AssertionError("Bad transformer that returns pooled tokens unexpectedly succeeded")

    return "token-preserving custom transformer passed and pooled-output guard failed as expected"


def check_parallel_vit() -> str:
    from vit_pytorch.parallel_vit import ViT as ParallelViT

    torch.manual_seed(3)
    model = ParallelViT(
        image_size=16,
        patch_size=8,
        num_classes=4,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=8,
        num_parallel_branches=2,
        dropout=0.0,
        emb_dropout=0.0,
    ).eval()
    img = torch.randn(2, 3, 16, 16)
    with torch.no_grad():
        logits = model(img)
    _assert_shape(logits, (2, 4), "parallel_vit logits")
    return "parallel_vit tiny classifier shape passed"


def check_simple_flash_2d() -> str:
    if _torch_version_tuple() < (2, 0):
        raise SkipCheck("PyTorch < 2.0: simple_flash_attn_vit use_flash=True is not applicable")

    module = importlib.import_module("vit_pytorch.simple_flash_attn_vit")
    SimpleViT = module.SimpleViT

    torch.manual_seed(4)
    model = SimpleViT(
        image_size=16,
        patch_size=8,
        num_classes=3,
        dim=8,
        depth=1,
        heads=2,
        mlp_dim=16,
        dim_head=4,
        use_flash=True,
    ).eval()
    img = torch.randn(2, 3, 16, 16)
    with torch.no_grad():
        logits = model(img)
    _assert_shape(logits, (2, 3), "simple_flash_attn_vit logits")
    return "simple_flash_attn_vit CPU SDPA shape passed"


def check_simple_flash_3d() -> str:
    if _torch_version_tuple() < (2, 0):
        raise SkipCheck("PyTorch < 2.0: simple_flash_attn_vit_3d use_flash_attn=True is not applicable")

    module = importlib.import_module("vit_pytorch.simple_flash_attn_vit_3d")
    SimpleViT3D = module.SimpleViT

    torch.manual_seed(5)
    model = SimpleViT3D(
        image_size=8,
        image_patch_size=4,
        frames=4,
        frame_patch_size=2,
        num_classes=3,
        dim=12,
        depth=1,
        heads=2,
        mlp_dim=24,
        dim_head=6,
        use_flash_attn=True,
    ).eval()
    video = torch.randn(2, 3, 4, 8, 8)
    with torch.no_grad():
        logits = model(video)
    _assert_shape(logits, (2, 3), "simple_flash_attn_vit_3d logits")
    return "simple_flash_attn_vit_3d CPU SDPA shape passed"


def run_check(results: List[CheckResult], name: str, fn: Callable[[], str], required: bool = True) -> bool:
    try:
        detail = fn()
    except SkipCheck as exc:
        results.append(CheckResult(name=name, status="skipped", detail=str(exc)))
        return True
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report concise failure
        status = "failed" if required else "optional-failed"
        results.append(CheckResult(name=name, status=status, detail=f"{type(exc).__name__}: {exc}"))
        return not required
    else:
        results.append(CheckResult(name=name, status="passed", detail=detail))
        return True


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-performance-wrappers",
        action="store_true",
        help="only run Recorder, Extractor, and efficient.ViT contract checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    results: List[CheckResult] = []

    try:
        version = metadata.version("vit-pytorch")
    except metadata.PackageNotFoundError:
        version = "unknown"

    ok = True
    ok &= run_check(results, "Recorder", check_recorder, required=True)
    ok &= run_check(results, "Extractor", check_extractor, required=True)
    ok &= run_check(results, "efficient.ViT custom transformer", check_efficient_vit_contract, required=True)

    if not args.skip_performance_wrappers:
        ok &= run_check(results, "parallel_vit", check_parallel_vit, required=True)
        ok &= run_check(results, "simple_flash_attn_vit", check_simple_flash_2d, required=False)
        ok &= run_check(results, "simple_flash_attn_vit_3d", check_simple_flash_3d, required=False)

    payload = {
        "package": "vit-pytorch",
        "version": version,
        "torch": torch.__version__,
        "device_scope": "cpu",
        "results": [result.__dict__ for result in results],
        "ok": bool(ok),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"vit-pytorch introspection smoke (package version: {version}, torch: {torch.__version__})")
        for result in results:
            print(f"[{result.status}] {result.name}: {result.detail}")
        print("overall:", "ok" if ok else "failed")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
