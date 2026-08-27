#!/usr/bin/env python3
"""Print the installed OpenNMT-py runtime facts."""

from __future__ import annotations

from importlib.metadata import version

import torch

import onmt


def main() -> None:
    print("onmt_import=ok")
    print(f"OpenNMT-py={version('OpenNMT-py')}")
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        print(f"cuda_device_name={torch.cuda.get_device_name(0)}")
        print(f"cuda_device_capability={torch.cuda.get_device_capability(0)}")


if __name__ == "__main__":
    main()
