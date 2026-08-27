#!/usr/bin/env python3
"""CPU smoke checks for vit-pytorch variable-shape and video workflows.

The checks use tiny random tensors and import the installed vit_pytorch package.
They do not read repository source files, download data, or require CUDA.

Default coverage:
  - standard NaViT greedy grouping and manual grouped forward;
  - tiny ViT3D, SimpleViT3D, CCT3D, and ViViT forward passes;
  - AcceptVideoWrapper restoring a time dimension and adding time embeddings;
  - representative 1D and N-D forward passes.

Nested tensor NaViT checks are version/backend sensitive and are opt-in:
  python smoke_variable_shapes_video.py --include-nested
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import traceback
from dataclasses import asdict, dataclass
from typing import Any, Callable


class SkipCheck(RuntimeError):
    """Raised when an optional check is not applicable in this runtime."""


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _assert_shape(tensor: Any, expected: tuple[int, ...], name: str) -> None:
    actual = tuple(tensor.shape)
    if actual != expected:
        raise AssertionError(f"{name} shape {actual} != expected {expected}")


def _filter_supported_kwargs(cls: type, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Drop optional kwargs when checking older installed variants."""

    signature = inspect.signature(cls.__init__)
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
        return dict(kwargs)
    return {key: value for key, value in kwargs.items() if key in signature.parameters}


def _resolve_class(module_name: str, *candidate_names: str) -> type:
    module = importlib.import_module(module_name)
    for candidate in candidate_names:
        cls = getattr(module, candidate, None)
        if cls is not None:
            return cls
    raise AttributeError(f"{module_name} exposes none of {candidate_names}")


def check_navit_grouping(torch: Any) -> str:
    from vit_pytorch.na_vit import NaViT, group_images_by_max_seq_len

    torch.manual_seed(0)
    model = NaViT(
        image_size=32,
        patch_size=8,
        num_classes=7,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
        token_dropout_prob=0.0,
    ).eval()

    images = [
        torch.randn(3, 32, 32),  # 16 tokens
        torch.randn(3, 16, 16),  # 4 tokens
        torch.randn(3, 16, 32),  # 8 tokens
        torch.randn(3, 8, 32),   # 4 tokens
    ]

    groups = group_images_by_max_seq_len(images, patch_size=8, max_seq_len=20)
    group_lengths = [len(group) for group in groups]
    if group_lengths != [2, 2]:
        raise AssertionError(f"unexpected greedy groups {group_lengths}, expected [2, 2]")

    with torch.no_grad():
        auto_logits = model(images, group_images=True, group_max_seq_len=20)
        manual_logits = model(groups)

    _assert_shape(auto_logits, (4, 7), "auto grouped NaViT logits")
    _assert_shape(manual_logits, (4, 7), "manual grouped NaViT logits")

    try:
        group_images_by_max_seq_len([torch.randn(3, 32, 32)], patch_size=8, max_seq_len=15)
    except AssertionError as exc:
        if "exceeds maximum sequence length" not in str(exc):
            raise
    else:
        raise AssertionError("expected a single over-budget image to fail grouping")

    return "NaViT grouped [2, 2], logits (4, 7), and over-budget image assertion all behaved as expected"


def check_vit3d(torch: Any) -> str:
    from vit_pytorch.vit_3d import ViT

    torch.manual_seed(1)
    model = ViT(
        image_size=16,
        image_patch_size=8,
        frames=4,
        frame_patch_size=2,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
    ).eval()

    video = torch.randn(2, 3, 4, 16, 16)
    with torch.no_grad():
        logits = model(video)
    _assert_shape(logits, (2, 5), "ViT3D logits")
    return "vit_3d.ViT accepted (2, 3, 4, 16, 16) and returned (2, 5)"


def check_simple_vit3d(torch: Any) -> str:
    from vit_pytorch.simple_vit_3d import SimpleViT

    torch.manual_seed(2)
    model = SimpleViT(
        image_size=16,
        image_patch_size=8,
        frames=4,
        frame_patch_size=2,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
    ).eval()

    video = torch.randn(2, 3, 4, 16, 16)
    with torch.no_grad():
        logits = model(video)
    _assert_shape(logits, (2, 5), "SimpleViT3D logits")
    return "simple_vit_3d.SimpleViT accepted (2, 3, 4, 16, 16) and returned (2, 5)"


def check_cct3d(torch: Any) -> str:
    from vit_pytorch.cct_3d import CCT

    torch.manual_seed(3)
    model = CCT(
        img_size=8,
        num_frames=4,
        embedding_dim=16,
        n_conv_layers=1,
        frame_kernel_size=3,
        kernel_size=3,
        stride=1,
        padding=1,
        pooling_kernel_size=2,
        pooling_stride=2,
        pooling_padding=0,
        num_layers=1,
        num_heads=2,
        mlp_ratio=2.0,
        num_classes=5,
        positional_embedding="learnable",
    ).eval()

    video = torch.randn(2, 3, 4, 8, 8)
    with torch.no_grad():
        logits = model(video)
    _assert_shape(logits, (2, 5), "CCT3D logits")
    return "cct_3d.CCT accepted (2, 3, 4, 8, 8) and returned (2, 5)"


def check_vivit(torch: Any) -> str:
    ViViT = _resolve_class("vit_pytorch.vivit", "ViViT", "ViT")

    kwargs = _filter_supported_kwargs(
        ViViT,
        dict(
            image_size=16,
            image_patch_size=8,
            frames=4,
            frame_patch_size=2,
            num_classes=5,
            dim=32,
            spatial_depth=1,
            temporal_depth=1,
            heads=2,
            mlp_dim=64,
            dim_head=16,
            dropout=0.0,
            emb_dropout=0.0,
            variant="factorized_encoder",
            use_flash_attn=False,
        ),
    )

    torch.manual_seed(4)
    model = ViViT(**kwargs).eval()
    video = torch.randn(2, 3, 4, 16, 16)
    with torch.no_grad():
        logits = model(video)
    _assert_shape(logits, (2, 5), "ViViT logits")
    return f"{ViViT.__module__}.{ViViT.__name__} accepted (2, 3, 4, 16, 16) and returned (2, 5)"


def check_accept_video_wrapper(torch: Any) -> str:
    from torch import nn
    from vit_pytorch.accept_video_wrapper import AcceptVideoWrapper

    class TinyFrameEmbeddingNet(nn.Module):
        patch_size = 8

        def forward(self, frames):
            batch = frames.shape[0]
            # One CLS token plus four patch tokens for a 16x16 frame with patch_size 8.
            return torch.zeros(batch, 5, 12, device=frames.device, dtype=frames.dtype)

    torch.manual_seed(5)
    wrapper = AcceptVideoWrapper(
        TinyFrameEmbeddingNet(),
        add_time_pos_emb=True,
        dim_emb=12,
        time_seq_len=4,
    ).eval()

    video = torch.randn(2, 3, 4, 16, 16)
    with torch.no_grad():
        embeddings = wrapper(video)
    _assert_shape(embeddings, (2, 4, 5, 12), "AcceptVideoWrapper embeddings")
    return "AcceptVideoWrapper restored time dimension and added time embeddings: (2, 4, 5, 12)"


def check_1d_and_nd(torch: Any) -> str:
    from vit_pytorch.vit_1d import ViT as ViT1D
    from vit_pytorch.simple_vit_1d import SimpleViT as SimpleViT1D
    from vit_pytorch.vit_nd import ViTND
    from vit_pytorch.vit_nd_pope import ViTND as PoPEViTND
    from vit_pytorch.vit_nd_rotary import ViTND as RotaryViTND

    torch.manual_seed(6)
    series = torch.randn(2, 3, 16)

    vit1d = ViT1D(
        seq_len=16,
        patch_size=4,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
    ).eval()
    simple1d = SimpleViT1D(
        seq_len=16,
        patch_size=4,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
    ).eval()

    with torch.no_grad():
        _assert_shape(vit1d(series), (2, 5), "ViT1D logits")
        _assert_shape(simple1d(series), (2, 5), "SimpleViT1D logits")

    nd_input = torch.randn(2, 3, 4, 8, 8)
    common_nd_kwargs = dict(
        ndim=3,
        input_shape=(4, 8, 8),
        patch_size=(2, 4, 4),
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
    )

    nd = ViTND(**common_nd_kwargs).eval()
    pope_kwargs = dict(common_nd_kwargs)
    pope_kwargs.pop("emb_dropout", None)
    pope = PoPEViTND(**pope_kwargs).eval()
    rotary = RotaryViTND(**pope_kwargs).eval()

    with torch.no_grad():
        _assert_shape(nd(nd_input), (2, 5), "ViTND logits")
        _assert_shape(pope(nd_input), (2, 5), "PoPE ViTND logits")
        _assert_shape(rotary(nd_input), (2, 5), "Rotary ViTND logits")
        _assert_shape(pope(nd_input, return_embed=True), (2, 2, 2, 2, 32), "PoPE ViTND patch-grid embeddings")
        _assert_shape(rotary(nd_input, return_embed=True), (2, 2, 2, 2, 32), "Rotary ViTND patch-grid embeddings")

    return "1D logits (2, 5), N-D logits (2, 5), and PoPE/RoPE patch-grid embeddings (2, 2, 2, 2, 32) passed"


def check_nested(torch: Any) -> str:
    if not hasattr(torch, "jagged"):
        raise SkipCheck("this PyTorch build does not expose torch.jagged")

    try:
        from torch.nested import nested_tensor as _nested_tensor  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on installed torch
        raise SkipCheck(f"torch.nested.nested_tensor is unavailable: {exc}") from exc

    from vit_pytorch.na_vit_nested_tensor import NaViT as NestedNaViT
    from vit_pytorch.na_vit_nested_tensor_3d import NaViT as NestedNaViT3D

    torch.manual_seed(7)
    navit = NestedNaViT(
        image_size=32,
        patch_size=8,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
        token_dropout_prob=0.0,
    ).eval()

    images = [torch.randn(3, 32, 32), torch.randn(3, 16, 16)]

    navit3d = NestedNaViT3D(
        image_size=16,
        max_frames=4,
        patch_size=8,
        frame_patch_size=2,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        mlp_dim=64,
        dim_head=16,
        dropout=0.0,
        emb_dropout=0.0,
        token_dropout_prob=0.0,
    ).eval()

    volumes = [torch.randn(3, 4, 16, 16), torch.randn(3, 2, 16, 8)]

    with torch.no_grad():
        _assert_shape(navit(images), (2, 5), "nested NaViT logits")
        _assert_shape(navit3d(volumes), (2, 5), "nested NaViT 3D logits")

    return "optional nested tensor NaViT 2D and 3D checks returned (2, 5) logits"


def _run_check(name: str, fn: Callable[[Any], str], torch: Any, verbose: bool) -> CheckResult:
    try:
        detail = fn(torch)
        return CheckResult(name=name, status="pass", detail=detail)
    except SkipCheck as exc:
        return CheckResult(name=name, status="skip", detail=str(exc))
    except Exception as exc:  # pragma: no cover - intended CLI diagnostics
        detail = f"{type(exc).__name__}: {exc}"
        if verbose:
            detail += "\n" + traceback.format_exc()
        return CheckResult(name=name, status="fail", detail=detail)


def _import_torch() -> Any:
    try:
        return importlib.import_module("torch")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "torch is not installed in this Python environment. Install vit-pytorch's runtime dependencies "
            "and rerun this smoke helper with that environment's Python."
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-nested", action="store_true", help="also run version-sensitive nested tensor NaViT checks")
    parser.add_argument("--skip-cct", action="store_true", help="skip the tiny cct_3d.CCT check")
    parser.add_argument("--skip-nd", action="store_true", help="skip 1D and N-D tensor family checks")
    parser.add_argument("--threads", type=int, default=1, help="torch CPU thread count for deterministic small checks")
    parser.add_argument("--json", action="store_true", help="emit JSON results instead of human-readable lines")
    parser.add_argument("--verbose", action="store_true", help="include tracebacks for failed checks")
    args = parser.parse_args(argv)

    torch = _import_torch()
    if args.threads > 0:
        torch.set_num_threads(args.threads)

    checks: list[tuple[str, Callable[[Any], str]]] = [
        ("navit_grouping", check_navit_grouping),
        ("vit3d", check_vit3d),
        ("simple_vit3d", check_simple_vit3d),
        ("vivit", check_vivit),
        ("accept_video_wrapper", check_accept_video_wrapper),
    ]

    if not args.skip_cct:
        checks.insert(3, ("cct3d", check_cct3d))

    if not args.skip_nd:
        checks.append(("one_d_and_nd", check_1d_and_nd))

    if args.include_nested:
        checks.append(("nested_navits", check_nested))

    results = [_run_check(name, fn, torch, args.verbose) for name, fn in checks]

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"[{result.status.upper()}] {result.name}: {result.detail}")

    return 1 if any(result.status == "fail" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
