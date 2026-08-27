#!/usr/bin/env python3
"""Safe nnU-Net runtime smoke.

This helper checks the installed package, the nnU-Net CLI surface, the batchgenerators
augmenter export, and an optional tiny CUDA tensor smoke. It avoids dataset access,
training, downloads, and any destructive side effects.
"""

from __future__ import annotations

import argparse
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the installed nnU-Net runtime")
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="Also allocate a tiny CUDA tensor when torch reports CUDA availability.",
    )
    args = parser.parse_args()

    import nnunet  # type: ignore
    import torch  # type: ignore
    from batchgenerators.dataloading import MultiThreadedAugmenter, SingleThreadedAugmenter  # type: ignore
    from nnunet.network_architecture.neural_network import SegmentationNetwork  # type: ignore

    print(f"nnunet={metadata.version('nnunet')}")
    print(f"nnunet_file={nnunet.__file__}")
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"batchgenerators.MultiThreadedAugmenter={MultiThreadedAugmenter.__name__}")
    print(f"batchgenerators.SingleThreadedAugmenter={SingleThreadedAugmenter.__name__}")
    steps = SegmentationNetwork._compute_steps_for_sliding_window((64, 64), (128, 128), 0.5)
    print(f"sliding_window_steps={steps}")

    if args.cuda_smoke:
        if torch.cuda.is_available():
            x = torch.empty((1,), device="cuda")
            print(f"cuda_tensor={x.device}")
        else:
            print("cuda_tensor=skipped_cuda_unavailable")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
