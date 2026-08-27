#!/usr/bin/env python3
"""Print a read-only CPU/GPU monitoring summary for LabML.

This script exercises the optional hardware-monitoring dependencies used by the
client package. It does not start the long-running monitor service.

Example:
    python scripts/hardware_probe.py
    python scripts/hardware_probe.py --require-gpu
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe LabML hardware-monitoring dependencies.")
    parser.add_argument("--require-gpu", action="store_true", help="Exit non-zero if NVIDIA GPU reporting is unavailable.")
    args = parser.parse_args()

    try:
        import psutil
    except Exception as exc:
        print(f"psutil_unavailable={exc}")
        return 1

    print(f"cpu_count={psutil.cpu_count()}")
    print(f"cpu_count_physical={psutil.cpu_count(logical=False)}")
    print(f"memory_total={psutil.virtual_memory().total}")
    print(f"memory_available={psutil.virtual_memory().available}")
    print(f"disk_total={psutil.disk_usage('/').total}")
    print(f"disk_used={psutil.disk_usage('/').used}")

    gpu_ok = False
    try:
        import torch
        print(f"torch_cuda_available={torch.cuda.is_available()}")
        print(f"torch_cuda_device_count={torch.cuda.device_count()}")
    except Exception as exc:
        print(f"torch_cuda_unavailable={exc}")

    try:
        from py3nvml import py3nvml as nvml

        nvml.nvmlInit()
        print(f"nvidia_driver={nvml.nvmlSystemGetDriverVersion()}")
        print(f"nvidia_device_count={nvml.nvmlDeviceGetCount()}")
        gpu_ok = True
        nvml.nvmlShutdown()
    except Exception as exc:
        print(f"py3nvml_unavailable={exc}")

    if args.require_gpu and not gpu_ok:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
