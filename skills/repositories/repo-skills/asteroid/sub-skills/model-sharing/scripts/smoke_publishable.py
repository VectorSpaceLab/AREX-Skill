#!/usr/bin/env python3
"""Tiny publishable-model smoke check for Asteroid."""

from __future__ import annotations

import tempfile
from pathlib import Path

import torch

from asteroid.data.wham_dataset import wsj0_license, wham_noise_license
from asteroid.models import ConvTasNet, save_publishable


def main() -> None:
    model = ConvTasNet(
        n_src=2,
        n_repeats=1,
        n_blocks=1,
        bn_chan=8,
        hid_chan=4,
        skip_chan=4,
        n_filters=16,
    )
    model_dict = model.serialize()
    model_dict.update(
        {
            "dataset": "WHAM",
            "task": "sep_noisy",
            "licenses": [wsj0_license, wham_noise_license],
        }
    )
    model_dict.setdefault("infos", {})
    publish_root = Path(tempfile.mkdtemp(prefix="asteroid-publish-"))
    save_publishable(
        publish_root.as_posix(),
        model_dict,
        metrics={"si_sdr": 1.23, "si_sdr_imp": 0.42},
        train_conf={"smoke": True},
        recipe="smoke/convtasnet",
    )
    saved = publish_root / "model.pth"
    print(f"publishable saved: {saved.is_file()} at {publish_root}")

    # Make sure the saved file can be loaded back. The file was just created
    # locally, so opt out of the PyTorch >=2.6 weights-only default for this
    # trusted smoke artifact while remaining compatible with older PyTorch.
    try:
        loaded = torch.load(saved, map_location="cpu", weights_only=False)
    except TypeError:
        loaded = torch.load(saved, map_location="cpu")
    print(f"loaded keys: {sorted(loaded.keys())[:5]}")


if __name__ == "__main__":
    main()
