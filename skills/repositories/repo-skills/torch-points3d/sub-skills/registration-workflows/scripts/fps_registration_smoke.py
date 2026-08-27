#!/usr/bin/env python3
"""Tiny CPU smoke for Torch Points3D registration FPS sampling.

This mirrors the repository's safe unit-test fixture for
`torch_points3d.datasets.registration.utils.fps_sampling`.

Example:
  python sub-skills/registration-workflows/scripts/fps_registration_smoke.py --json
"""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny registration FPS utility smoke test.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    try:
        import torch
        from torch_points3d.datasets.registration.utils import fps_sampling
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"registration utility import failed: {type(exc).__name__}: {exc}")

    pos = torch.tensor([[0, 0, 0], [0.5, 0.5, 0], [0.4, 0.2, 0], [2, 2, 2], [-1, -2, -0.01]]).float()
    pair_ind = torch.tensor([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]]).long()
    expected_pairs = torch.tensor([[0, 0], [3, 3], [4, 4]]).long()
    new_ind = fps_sampling(pair_ind, pos, 3)
    new_pairs = pair_ind[new_ind]

    if not torch.equal(new_pairs, expected_pairs):
        raise SystemExit(f"unexpected sampled pairs: got {new_pairs.tolist()}, expected {expected_pairs.tolist()}")

    result = {
        "status": "passed",
        "selected_indices": new_ind.tolist(),
        "selected_pairs": new_pairs.tolist(),
        "expected_pairs": expected_pairs.tolist(),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Torch Points3D registration FPS smoke passed")
        print("selected_pairs:", result["selected_pairs"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
