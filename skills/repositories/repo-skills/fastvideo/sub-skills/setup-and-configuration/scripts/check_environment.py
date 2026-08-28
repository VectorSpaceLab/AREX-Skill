#!/usr/bin/env python3
"""Read-only FastVideo environment diagnostic; safe from any working directory."""
import importlib.metadata
import importlib.util
import platform
import sys


def main() -> int:
    import argparse
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(f"python={sys.version.split()[0]}")
    print(f"platform={platform.system()} {platform.machine()}")
    try:
        print(f"fastvideo={importlib.metadata.version('fastvideo')}")
    except importlib.metadata.PackageNotFoundError:
        print("fastvideo=missing")
        return 2
    try:
        import torch
        print(f"torch={torch.__version__} cuda_build={torch.version.cuda}")
        print(f"cuda_available={torch.cuda.is_available()} cuda_count={torch.cuda.device_count()}")
        if torch.cuda.is_available():
            print(f"cuda_device={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
            print("cuda_allocation=passed")
        print(f"mps_available={hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()}")
    except ImportError as exc:
        print(f"torch=missing ({exc})")
        return 3
    for name in ("fastvideo_kernel", "flashinfer", "av", "torchcodec"):
        print(f"optional_{name}={'present' if importlib.util.find_spec(name) else 'absent'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
