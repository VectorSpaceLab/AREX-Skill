#!/usr/bin/env python3
"""Tiny CPU smoke checks for vit-pytorch 2D image architecture constructors.

Purpose
-------
This helper adapts the README/test pattern to reduced random tensors. It does
not download data, train models, save files, or depend on repo-local runtime
files. Run it in an environment where ``vit-pytorch`` and ``torch`` are
installed.

Examples
--------
python scripts/smoke_image_architectures.py --case quick
python scripts/smoke_image_architectures.py --case extended
python scripts/smoke_image_architectures.py --case errors
python scripts/smoke_image_architectures.py --list
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class SmokeCase:
    name: str
    factory: Callable[[int], object]
    shape: tuple[int, int, int, int]
    description: str


def _import_runtime():
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user env
        raise SystemExit(
            "Unable to import torch. Install vit-pytorch with its PyTorch dependency "
            "before running this smoke helper. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        import vit_pytorch  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on user env
        raise SystemExit(
            "Unable to import vit_pytorch. Install the vit-pytorch package in this "
            "Python environment before running this smoke helper. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return torch


def build_quick_cases() -> list[SmokeCase]:
    from vit_pytorch import SimpleViT, ViT
    from vit_pytorch.cct import CCT
    from vit_pytorch.cross_vit import CrossViT
    from vit_pytorch.vit_with_patch_merger import ViT as PatchMergerViT

    return [
        SmokeCase(
            name="vit",
            description="plain ViT baseline with learned positional embeddings",
            shape=(1, 3, 32, 32),
            factory=lambda classes: ViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
            ),
        ),
        SmokeCase(
            name="simple-vit",
            description="SimpleViT mean-pooled baseline with 2D sin/cos positions",
            shape=(1, 3, 32, 32),
            factory=lambda classes: SimpleViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
            ),
        ),
        SmokeCase(
            name="cct",
            description="compact convolutional transformer with sequence pooling",
            shape=(1, 3, 32, 32),
            factory=lambda classes: CCT(
                img_size=32,
                embedding_dim=32,
                n_conv_layers=1,
                kernel_size=3,
                stride=1,
                padding=1,
                pooling_kernel_size=2,
                pooling_stride=2,
                pooling_padding=0,
                num_layers=1,
                num_heads=2,
                mlp_ratio=2.0,
                num_classes=classes,
                positional_embedding="learnable",
            ),
        ),
        SmokeCase(
            name="cross-vit",
            description="two-scale CrossViT with one tiny cross-attention block",
            shape=(1, 3, 32, 32),
            factory=lambda classes: CrossViT(
                image_size=32,
                num_classes=classes,
                depth=1,
                sm_dim=32,
                sm_patch_size=8,
                sm_enc_depth=1,
                sm_enc_heads=2,
                sm_enc_mlp_dim=64,
                sm_enc_dim_head=16,
                lg_dim=64,
                lg_patch_size=16,
                lg_enc_depth=1,
                lg_enc_heads=2,
                lg_enc_mlp_dim=128,
                lg_enc_dim_head=16,
                cross_attn_depth=1,
                cross_attn_heads=2,
                cross_attn_dim_head=16,
                dropout=0.0,
                emb_dropout=0.0,
            ),
        ),
        SmokeCase(
            name="patch-merger-vit",
            description="ViT variant with token reduction after the first layer",
            shape=(1, 3, 32, 32),
            factory=lambda classes: PatchMergerViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=2,
                heads=2,
                dim_head=16,
                mlp_dim=64,
                patch_merge_layer=1,
                patch_merge_num_tokens=4,
            ),
        ),
    ]


def build_extended_cases() -> list[SmokeCase]:
    from vit_pytorch.crossformer import CrossFormer
    from vit_pytorch.jet_vit import JetViT
    from vit_pytorch.max_vit import MaxViT
    from vit_pytorch.mobile_vit import MobileViT
    from vit_pytorch.vit_5 import ViT as ViT5
    from vit_pytorch.vit_for_small_dataset import ViT as SmallDatasetViT
    from vit_pytorch.xcit import XCiT

    return [
        SmokeCase(
            name="small-dataset-vit",
            description="SPT/LSA ViT variant for small dataset experiments",
            shape=(1, 3, 32, 32),
            factory=lambda classes: SmallDatasetViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
            ),
        ),
        SmokeCase(
            name="xcit",
            description="cross-covariance attention classifier",
            shape=(1, 3, 32, 32),
            factory=lambda classes: XCiT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                cls_depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
            ),
        ),
        SmokeCase(
            name="jet-vit",
            description="JetViT deterministic full-attention layer",
            shape=(1, 3, 32, 32),
            factory=lambda classes: JetViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
                window_size=2,
                attn_layers=["FA"],
            ),
        ),
        SmokeCase(
            name="vit-5",
            description="RMSNorm/QK-norm/register-token ViT-5 variant",
            shape=(1, 3, 32, 32),
            factory=lambda classes: ViT5(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
                num_registers=2,
            ),
        ),
        SmokeCase(
            name="max-vit",
            description="tiny MaxViT with window size chosen for 64x64 input",
            shape=(1, 3, 64, 64),
            factory=lambda classes: MaxViT(
                num_classes=classes,
                dim=16,
                dim_head=8,
                depth=(1, 1, 1, 1),
                window_size=2,
                channels=3,
            ),
        ),
        SmokeCase(
            name="mobile-vit",
            description="small MobileViT using complete staged channel list",
            shape=(1, 3, 64, 64),
            factory=lambda classes: MobileViT(
                image_size=(64, 64),
                dims=[32, 48, 64],
                channels=[8, 16, 24, 24, 32, 32, 48, 48, 64, 64, 96],
                num_classes=classes,
                depths=(1, 1, 1),
            ),
        ),
        SmokeCase(
            name="crossformer",
            description="tiny CrossFormer with nonzero stage dimensions",
            shape=(1, 3, 32, 32),
            factory=lambda classes: CrossFormer(
                dim=(32, 64, 128, 256),
                depth=(1, 1, 1, 1),
                global_window_size=(2, 1, 1, 1),
                local_window_size=2,
                cross_embed_kernel_sizes=((2, 4), (2,), (2,), (2,)),
                cross_embed_strides=(2, 2, 2, 2),
                num_classes=classes,
            ),
        ),
    ]


def build_flash_cases() -> list[SmokeCase]:
    from vit_pytorch.simple_flash_attn_vit import SimpleViT as FlashSimpleViT

    return [
        SmokeCase(
            name="simple-flash-attn-vit",
            description="SimpleViT using PyTorch scaled-dot-product attention branch",
            shape=(1, 3, 32, 32),
            factory=lambda classes: FlashSimpleViT(
                image_size=32,
                patch_size=8,
                num_classes=classes,
                dim=32,
                depth=1,
                heads=2,
                dim_head=16,
                mlp_dim=64,
                use_flash=True,
            ),
        )
    ]


def iter_cases(case_group: str) -> Iterable[SmokeCase]:
    if case_group == "quick":
        yield from build_quick_cases()
    elif case_group == "extended":
        yield from build_extended_cases()
    elif case_group == "flash":
        yield from build_flash_cases()
    elif case_group == "all":
        yield from build_quick_cases()
        yield from build_extended_cases()
        yield from build_flash_cases()
    else:
        raise ValueError(f"unknown case group: {case_group}")


def run_forward_cases(args: argparse.Namespace) -> int:
    torch = _import_runtime()
    if args.threads is not None:
        torch.set_num_threads(args.threads)

    device = torch.device(args.device)
    torch.manual_seed(args.seed)

    passed = 0
    for case in iter_cases(args.case):
        model = case.factory(args.classes)
        model.to(device)
        model.eval()
        x = torch.randn(*case.shape, device=device)
        expected = (case.shape[0], args.classes)
        with torch.no_grad(), warnings.catch_warnings():
            if not args.show_warnings:
                warnings.simplefilter("ignore")
            out = model(x)
        if not hasattr(out, "shape"):
            raise AssertionError(f"{case.name}: expected tensor logits, got {type(out)!r}")
        actual = tuple(out.shape)
        if actual != expected:
            raise AssertionError(f"{case.name}: expected shape {expected}, got {actual}")
        if not torch.isfinite(out).all().item():
            raise AssertionError(f"{case.name}: logits contain non-finite values")
        print(f"OK {case.name}: {case.description}; output_shape={actual}")
        passed += 1

    print(f"Summary: {passed} constructor/forward smoke case(s) passed on {device}.")
    return passed


def expect_assertion(label: str, fn: Callable[[], object], expected_fragment: str) -> None:
    try:
        fn()
    except AssertionError as exc:
        msg = str(exc)
        if expected_fragment not in msg:
            raise AssertionError(
                f"{label}: got AssertionError {msg!r}, expected fragment {expected_fragment!r}"
            ) from exc
        print(f"OK expected-error {label}: {msg}")
        return
    raise AssertionError(f"{label}: expected AssertionError containing {expected_fragment!r}")


def run_error_cases(args: argparse.Namespace) -> int:
    _import_runtime()
    from vit_pytorch import ViT
    from vit_pytorch.simple_vit_with_patch_dropout import SimpleViT as PatchDropoutSimpleViT

    common = dict(
        image_size=32,
        patch_size=8,
        num_classes=args.classes,
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        mlp_dim=64,
    )

    expect_assertion(
        "non-divisible patch size",
        lambda: ViT(**{**common, "image_size": 30}),
        "Image dimensions must be divisible by the patch size.",
    )
    expect_assertion(
        "invalid pool choice",
        lambda: ViT(**{**common, "pool": "avg"}),
        "pool type must be either cls (cls token) or mean (mean pooling)",
    )
    expect_assertion(
        "invalid patch dropout probability",
        lambda: PatchDropoutSimpleViT(**{**common, "patch_dropout": 1.0}),
        "",
    )
    print("Summary: 3 expected constructor failure checks passed.")
    return 3


def list_cases() -> None:
    _import_runtime()
    groups = ["quick", "extended", "flash"]
    for group in groups:
        print(f"[{group}]")
        for case in iter_cases(group):
            print(f"  {case.name:28s} shape={case.shape} - {case.description}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny, no-download vit-pytorch 2D image architecture smoke checks. "
            "Use --case quick for the fastest representative constructors."
        )
    )
    parser.add_argument(
        "--case",
        choices=("quick", "extended", "flash", "errors", "all"),
        default="quick",
        help="which smoke group to run; 'all' runs quick, extended, flash, then errors",
    )
    parser.add_argument("--classes", type=int, default=7, help="number of logits/classes to assert")
    parser.add_argument("--device", default="cpu", help="torch device to use; default is cpu")
    parser.add_argument("--seed", type=int, default=0, help="torch random seed for deterministic random tensors")
    parser.add_argument("--threads", type=int, default=1, help="set torch CPU thread count; use 0 to leave unchanged")
    parser.add_argument("--show-warnings", action="store_true", help="show PyTorch warnings instead of suppressing them")
    parser.add_argument("--list", action="store_true", help="list bundled smoke cases and exit")
    args = parser.parse_args(argv)
    if args.threads == 0:
        args.threads = None
    if args.classes <= 0:
        parser.error("--classes must be a positive integer for classifier smoke checks")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list:
        list_cases()
        return 0

    try:
        if args.case == "errors":
            run_error_cases(args)
        elif args.case == "all":
            run_forward_cases(args)
            run_error_cases(args)
        else:
            run_forward_cases(args)
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
