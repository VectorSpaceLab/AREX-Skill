#!/usr/bin/env python3
"""Run a minimal CUDA smoke test for OpenNMT-py dependencies."""

from __future__ import annotations

import torch


def main() -> None:
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    if not torch.cuda.is_available():
        raise SystemExit(1)
    torch.empty((1,), device="cuda")
    print(f"cuda_device_name={torch.cuda.get_device_name(0)}")
    print(f"cuda_device_capability={torch.cuda.get_device_capability(0)}")


if __name__ == "__main__":
    main()
