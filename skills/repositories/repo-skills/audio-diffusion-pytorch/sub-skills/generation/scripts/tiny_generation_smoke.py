#!/usr/bin/env python3
"""Run a tiny CPU smoke for waveform generation and inpainting.

The script builds tiny DiffusionModel and VInpainter instances without pretrained
weights or external data. The optional text-conditioning constructor check is
skipped unless --include-text-constructor is provided; when requested, it only
runs if transformers is importable and may touch T5 or Hugging Face cache state.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys

import torch
from audio_diffusion_pytorch import DiffusionModel, UNetV0, VDiffusion, VInpainter, VSampler

CHANNELS = [4, 4]
FACTORS = [1, 2]
ITEMS = [1, 1]
ATTENTIONS = [0, 0]
RESNET_GROUPS = 1
LENGTH = 16
STEPS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny CPU smoke for generator and inpainting workflows."
    )
    parser.add_argument(
        "--include-text-constructor",
        action="store_true",
        help=(
            "Also check a text-conditioned UNetV0 constructor when transformers is available. "
            "This may load T5/cache state and requires embedding_features=768."
        ),
    )
    return parser.parse_args()


def build_generator(device: torch.device) -> dict:
    model = DiffusionModel(
        net_t=UNetV0,
        in_channels=1,
        channels=CHANNELS,
        factors=FACTORS,
        items=ITEMS,
        attentions=ATTENTIONS,
        resnet_groups=RESNET_GROUPS,
        diffusion_t=VDiffusion,
        sampler_t=VSampler,
    ).to(device)

    audio = torch.randn(1, 1, LENGTH, device=device)
    loss = model(audio)
    assert loss.ndim == 0, f"expected scalar loss, got ndim={loss.ndim}"
    sample = model.sample(torch.randn_like(audio), num_steps=STEPS)
    assert tuple(sample.shape) == tuple(audio.shape), (
        f"expected sample shape {tuple(audio.shape)}, got {tuple(sample.shape)}"
    )

    return {
        "loss_ndim": int(loss.ndim),
        "sample_shape": list(sample.shape),
    }


def build_inpainter(device: torch.device) -> dict:
    net = UNetV0(
        dim=1,
        in_channels=1,
        channels=CHANNELS,
        factors=FACTORS,
        items=ITEMS,
        attentions=ATTENTIONS,
        resnet_groups=RESNET_GROUPS,
    ).to(device)
    inpainter = VInpainter(net=net).to(device)

    source = torch.randn(1, 1, LENGTH, device=device)
    mask = torch.zeros_like(source, dtype=torch.bool)
    mask[..., : LENGTH // 2] = True
    assert mask.dtype == torch.bool, "expected bool mask"
    assert mask.shape == source.shape, "mask must match source shape"
    output = inpainter(source=source, mask=mask, num_steps=STEPS, num_resamples=1)
    assert tuple(output.shape) == tuple(source.shape), (
        f"expected output shape {tuple(source.shape)}, got {tuple(output.shape)}"
    )

    return {
        "output_shape": list(output.shape),
        "kept_elements": int(mask.sum().item()),
    }


def check_text_constructor() -> dict:
    if importlib.util.find_spec("transformers") is None:
        print(
            "transformers is not available; skipping the optional text-constructor check.",
            file=sys.stderr,
        )
        return {"status": "skipped", "reason": "transformers_missing"}

    import transformers

    print(
        "warning: the optional text-conditioning path may touch T5 or Hugging Face cache state and requires embedding_features=768.",
        file=sys.stderr,
    )

    net = UNetV0(
        dim=1,
        in_channels=1,
        channels=[8, 8],
        factors=FACTORS,
        items=ITEMS,
        attentions=ATTENTIONS,
        cross_attentions=[0, 1],
        attention_heads=1,
        attention_features=8,
        resnet_groups=RESNET_GROUPS,
        use_text_conditioning=True,
        use_embedding_cfg=True,
        embedding_max_length=64,
        embedding_features=768,
    )
    return {
        "status": "ok",
        "transformers_version": transformers.__version__,
        "net_type": type(net).__name__,
    }


def main() -> int:
    args = parse_args()
    torch.manual_seed(0)
    device = torch.device("cpu")

    results = {
        "device": str(device),
        "generator": build_generator(device),
        "inpainting": build_inpainter(device),
        "text_constructor": {"status": "not-requested"},
    }

    if args.include_text_constructor:
        results["text_constructor"] = check_text_constructor()

    print(json.dumps(results, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
