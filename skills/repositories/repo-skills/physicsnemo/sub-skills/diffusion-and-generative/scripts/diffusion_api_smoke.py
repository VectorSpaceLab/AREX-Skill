#!/usr/bin/env python3
"""Tiny PhysicsNeMo diffusion API smoke.

Imports the diffusion package, prints selected signatures, and can optionally
instantiate a tiny diffusion U-Net for a sanity check without downloading
weights or running a real sampling recipe.
"""

from __future__ import annotations

import argparse
import inspect
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiny-sampling", action="store_true", help="Instantiate a tiny SongUNet and print a summary.")
    args = parser.parse_args()

    from physicsnemo.diffusion import Denoiser, DiffusionModel, Predictor
    from physicsnemo.diffusion.preconditioners import EDMPrecond
    from physicsnemo.diffusion.samplers import EulerSolver, HeunSolver
    from physicsnemo.models.diffusion_unets import SongUNet, StormCastUNet, DhariwalUNet
    from physicsnemo.models.dit import DiT
    from physicsnemo.models.topodiff import TopoDiff

    payload = {
        "DiffusionModel": str(inspect.signature(DiffusionModel)),
        "Predictor": str(inspect.signature(Predictor)),
        "Denoiser": str(inspect.signature(Denoiser)),
        "EDMPrecond": str(inspect.signature(EDMPrecond)),
        "EulerSolver": str(inspect.signature(EulerSolver)),
        "HeunSolver": str(inspect.signature(HeunSolver)),
        "SongUNet": str(inspect.signature(SongUNet)),
        "StormCastUNet": str(inspect.signature(StormCastUNet)),
        "DhariwalUNet": str(inspect.signature(DhariwalUNet)),
        "DiT": str(inspect.signature(DiT)),
        "TopoDiff": str(inspect.signature(TopoDiff)),
    }

    if args.tiny_sampling:
        try:
            model = SongUNet(img_resolution=8, in_channels=1, out_channels=1, model_channels=16, channel_mult=[1], num_blocks=1, attn_resolutions=[], dropout=0.0)
            payload["tiny_songunet"] = model.__class__.__name__
        except Exception as exc:  # pragma: no cover - smoke path only
            payload["tiny_songunet"] = f"ERROR: {type(exc).__name__}: {exc}"

    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
