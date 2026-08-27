#!/usr/bin/env python3
"""Tiny no-network image API smoke for imagen-pytorch.

This helper intentionally uses unconditional synthetic tensors so it does not
call the package T5 text-encoding path. It checks construction, one training
loss, backward, and optional sampling. It does not prove generation quality.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny unconditional imagen-pytorch image smoke check."
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device for the smoke. 'auto' uses CUDA when torch reports it available.",
    )
    parser.add_argument(
        "--family",
        choices=("imagen", "elucidated"),
        default="imagen",
        help="Wrapper family to instantiate.",
    )
    parser.add_argument("--batch-size", type=int, default=1, help="Synthetic batch size.")
    parser.add_argument("--image-size", type=int, default=16, help="Tiny square image size.")
    parser.add_argument("--dim", type=int, default=8, help="Tiny Unet base dimension.")
    parser.add_argument(
        "--timesteps",
        type=int,
        default=2,
        help="DDPM timesteps for --family imagen. Keep tiny for smoke.",
    )
    parser.add_argument(
        "--num-sample-steps",
        type=int,
        default=2,
        help="Karras sampling steps for --family elucidated. Must be at least 2.",
    )
    parser.add_argument(
        "--skip-sample",
        action="store_true",
        help="Only run construction, loss, and backward; skip diffusion sampling.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Torch random seed for reproducible synthetic tensors.",
    )
    return parser.parse_args()


def fail(message: str, exc: Optional[BaseException] = None) -> int:
    print(f"[tiny-image-smoke] ERROR: {message}", file=sys.stderr)
    if exc is not None:
        print(f"[tiny-image-smoke] detail: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1


def resolve_device(torch_module, requested: str):
    if requested == "cpu":
        return torch_module.device("cpu")
    if requested == "cuda":
        if not torch_module.cuda.is_available():
            raise RuntimeError("--device cuda requested, but torch.cuda.is_available() is False")
        return torch_module.device("cuda")
    return torch_module.device("cuda" if torch_module.cuda.is_available() else "cpu")


def validate_args(args: argparse.Namespace) -> None:
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")
    if args.image_size < 8:
        raise ValueError("--image-size must be >= 8 for this tiny Unet")
    if args.image_size % 2 != 0:
        raise ValueError("--image-size must be even")
    if args.dim < 2:
        raise ValueError("--dim must be >= 2")
    if args.timesteps < 1:
        raise ValueError("--timesteps must be >= 1")
    if args.num_sample_steps < 2:
        raise ValueError("--num-sample-steps must be >= 2 for ElucidatedImagen")


def patch_t5_config_for_no_network() -> None:
    """Prevent the package import-time Unet default from fetching T5 config.

    The Unet constructor default references the default T5 encoded dimension at
    import time. For this unconditional smoke, a local dummy T5Config with the
    default base hidden size is enough because no text encoding path is used.
    """

    import transformers

    t5_config = transformers.T5Config

    def offline_from_pretrained(cls, *args, **kwargs):  # noqa: ANN001, ANN202
        return cls(d_model=768)

    t5_config.from_pretrained = classmethod(offline_from_pretrained)


def make_tiny_unet(Unet, *, dim: int):
    return Unet(
        dim=dim,
        text_embed_dim=None,
        dim_mults=(1, 1),
        num_resnet_blocks=1,
        layer_attns=False,
        layer_cross_attns=False,
        use_linear_attn=False,
        use_linear_cross_attn=False,
        attn_heads=2,
        cond_on_text=False,
    )


def make_model(args: argparse.Namespace, Unet, Imagen, ElucidatedImagen):
    unet = make_tiny_unet(Unet, dim=args.dim)
    common = dict(
        unets=(unet,),
        image_sizes=(args.image_size,),
        condition_on_text=False,
        cond_drop_prob=0.0,
    )
    if args.family == "imagen":
        return Imagen(timesteps=args.timesteps, **common)
    return ElucidatedImagen(num_sample_steps=args.num_sample_steps, **common)


def expected_shape(args: argparse.Namespace) -> Tuple[int, int, int, int]:
    return (args.batch_size, 3, args.image_size, args.image_size)


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
    except Exception as exc:  # noqa: BLE001 - command-line helper should print clear failures
        return fail("invalid arguments", exc)

    try:
        patch_t5_config_for_no_network()
        import torch
        from imagen_pytorch import ElucidatedImagen, Imagen, Unet
    except Exception as exc:  # noqa: BLE001
        return fail(
            "could not import torch and imagen_pytorch public APIs. Install the package and its runtime dependencies first. "
            "This helper avoids text encoding and patches T5Config to avoid network config downloads, "
            "but the package import may still require its declared dependencies.",
            exc,
        )

    try:
        device = resolve_device(torch, args.device)
    except Exception as exc:  # noqa: BLE001
        return fail("could not resolve requested device", exc)

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    try:
        model = make_model(args, Unet, Imagen, ElucidatedImagen).to(device)
    except Exception as exc:  # noqa: BLE001
        return fail("model construction failed", exc)

    shape = expected_shape(args)
    try:
        images = torch.rand(shape, device=device, dtype=torch.float32)
        loss = model(images, unet_number=1)
        if not torch.isfinite(loss).item():
            return fail(f"loss is not finite: {loss.detach().item()!r}")
        loss.backward()
        print(
            f"[tiny-image-smoke] loss ok: family={args.family} "
            f"device={device} value={loss.detach().item():.6f}"
        )
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            return fail(
                "loss/backward ran out of memory. Retry --device cpu, --skip-sample, smaller --batch-size, or smaller --image-size.",
                exc,
            )
        return fail("loss/backward failed", exc)
    except Exception as exc:  # noqa: BLE001
        return fail("loss/backward failed", exc)

    if args.skip_sample:
        print("[tiny-image-smoke] sample skipped by --skip-sample")
        return 0

    try:
        with torch.no_grad():
            samples = model.sample(
                batch_size=args.batch_size,
                cond_scale=1.0,
                use_tqdm=False,
                use_one_unet_in_gpu=False,
            )
        if tuple(samples.shape) != shape:
            return fail(f"unexpected sample shape {tuple(samples.shape)}; expected {shape}")
        if not torch.isfinite(samples).all().item():
            return fail("sample tensor contains non-finite values")
        print(
            f"[tiny-image-smoke] sample ok: shape={tuple(samples.shape)} "
            f"min={samples.min().item():.4f} max={samples.max().item():.4f}"
        )
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            return fail(
                "sampling ran out of memory. Retry with --skip-sample, smaller dimensions, or CUDA with enough memory.",
                exc,
            )
        return fail("sampling failed", exc)
    except Exception as exc:  # noqa: BLE001
        return fail("sampling failed", exc)

    print("[tiny-image-smoke] PASS (API smoke only; no quality claim)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
