#!/usr/bin/env python3
"""Tiny CPU smoke checks for TLLib translation components.

The script imports the installed ``tllib`` package and exercises CycleGAN
factories/losses, the ``Translation`` PIL transform, FDA ``FourierTransform``,
and CyCADA ``SemanticConsistency`` on synthetic data. It does not download
models, read a source checkout, train a network, or mutate anything outside a
temporary directory.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def run_smoke(include_spgan: bool = False) -> dict:
    try:
        import numpy as np
        import torch
        from PIL import Image
        import tllib.translation.cyclegan as cyclegan
        from tllib.translation.cycada import SemanticConsistency
        from tllib.translation.fourier_transform import FourierTransform, low_freq_mutate
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        raise RuntimeError(
            "Failed to import TLLib translation APIs. Install tllib with a "
            "compatible PyTorch/TorchVision stack before running this smoke."
        ) from exc

    torch.manual_seed(7)
    results = {}

    # CycleGAN generator/discriminator/loss checks on tiny tensors.
    generator = cyclegan.resnet_6(ngf=4, norm="instance")
    generator.eval()
    x = torch.randn(1, 3, 32, 32)
    with torch.no_grad():
        y = generator(x)
    if tuple(y.shape) != tuple(x.shape):
        raise AssertionError(f"generator output shape {tuple(y.shape)} != {tuple(x.shape)}")

    discriminator = cyclegan.pixel(ndf=4, norm="instance")
    pred = discriminator(y.detach())
    gan_loss = cyclegan.LeastSquaresGenerativeAdversarialLoss()
    loss_real = gan_loss(pred, real=True)
    loss_fake = gan_loss(pred, real=False)
    if not torch.isfinite(loss_real).item() or not torch.isfinite(loss_fake).item():
        raise AssertionError("non-finite CycleGAN loss")
    results["cyclegan"] = {
        "generator_shape": list(y.shape),
        "discriminator_shape": list(pred.shape),
        "loss_real": float(loss_real),
        "loss_fake": float(loss_fake),
    }

    # Translation transform on a synthetic PIL image.
    translate = cyclegan.Translation(generator, device=torch.device("cpu"))
    pil_input = Image.new("RGB", (32, 32), color=(32, 96, 160))
    translated = translate(pil_input)
    if translated.size != pil_input.size or translated.mode != "RGB":
        raise AssertionError(f"bad Translation output: mode={translated.mode} size={translated.size}")
    results["translation_transform"] = {"mode": translated.mode, "size": list(translated.size)}

    # FDA low-frequency mutation and FourierTransform temporary-cache check.
    amp_src = np.ones((3, 16, 16), dtype=np.float32)
    amp_trg = np.ones((3, 16, 16), dtype=np.float32) * 2
    mutated = low_freq_mutate(amp_src.copy(), amp_trg, beta=1)
    if mutated.shape != amp_src.shape:
        raise AssertionError("low_freq_mutate changed amplitude shape")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "target.png"
        source = root / "source.png"
        Image.new("RGB", (32, 32), color=(10, 120, 200)).save(target)
        Image.new("RGB", (32, 32), color=(200, 80, 20)).save(source)
        fda = FourierTransform([str(target)], str(root / "amplitudes"), beta=1, rebuild=True)
        out = fda(Image.open(source).convert("RGB"))
        if out.size != (32, 32) or out.mode != "RGB":
            raise AssertionError(f"bad FDA output: mode={out.mode} size={out.size}")
    results["fda"] = {"low_freq_shape": list(mutated.shape), "output_size": [32, 32]}

    # CyCADA semantic consistency check.
    criterion = SemanticConsistency(ignore_index=(255,))
    logits = torch.randn(2, 4, 8, 8)
    labels = torch.randint(0, 4, (2, 8, 8))
    labels[0, 0, 0] = 255
    semantic_loss = criterion(logits, labels.clone())
    if not torch.isfinite(semantic_loss).item():
        raise AssertionError("non-finite semantic consistency loss")
    results["semantic_consistency"] = {"loss": float(semantic_loss)}

    if include_spgan:
        try:
            from tllib.translation.spgan import ContrastiveLoss, SiameseNetwork
        except Exception as exc:  # pragma: no cover - CLI diagnostic path
            raise RuntimeError("Failed to import SPGAN components") from exc
        siamese = SiameseNetwork(nsf=64)
        siamese.eval()
        with torch.no_grad():
            feat = siamese(torch.randn(2, 3, 256, 128))
        contrastive = ContrastiveLoss(margin=2.0)
        label = torch.zeros(2)
        loss = contrastive(feat, feat, label)
        if not torch.isfinite(loss).item():
            raise AssertionError("non-finite SPGAN contrastive loss")
        results["spgan"] = {"feature_shape": list(feat.shape), "loss": float(loss)}

    return {"status": "ok", "checks": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run tiny CPU checks for TLLib translation components.")
    parser.add_argument("--include-spgan", action="store_true", help="also run the heavier SPGAN Siamese check")
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args(argv)

    payload = run_smoke(include_spgan=args.include_spgan)
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("TLLib translation smoke: ok")
        for name in sorted(payload["checks"]):
            print(f"  {name}: {payload['checks'][name]}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        print(f"TLLib translation smoke: failed: {exc}", file=sys.stderr)
        raise
