#!/usr/bin/env python3
"""Diagnose the minimal GeoSeg runtime without importing a config or dataset.

This read-only helper checks the installed framework versions, core imports,
and CUDA availability. It does not import data-bound configs, download weights,
or launch training/inference.

Example:
    python check_env.py --skip-cuda
"""

import argparse
import importlib
import sys

CORE_IMPORTS = (
    "geoseg",
    "geoseg.losses",
    "geoseg.datasets.vaihingen_dataset",
    "geoseg.datasets.potsdam_dataset",
    "geoseg.datasets.uavid_dataset",
    "geoseg.models.UNetFormer",
    "geoseg.models.FTUNetFormer",
    "geoseg.models.DCSwin",
    "tools.cfg",
    "tools.metric",
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cuda", action="store_true", help="do not probe torch CUDA")
    args = parser.parse_args(argv)

    try:
        import torch
    except ImportError as exc:
        print("FAIL torch import: {}".format(exc))
        return 1

    print("torch={}".format(torch.__version__))
    failures = []
    for name in CORE_IMPORTS:
        try:
            importlib.import_module(name)
            print("OK import {}".format(name))
        except Exception as exc:
            failures.append(name)
            print("FAIL import {}: {}: {}".format(name, type(exc).__name__, exc))

    if not args.skip_cuda:
        available = bool(torch.cuda.is_available())
        print("cuda_available={}".format(available))
        if not available:
            failures.append("cuda")
        else:
            device = torch.device("cuda:0")
            print("cuda_device={}".format(torch.cuda.get_device_name(0)))
            print("cuda_capability={}".format(torch.cuda.get_device_capability(0)))
            try:
                print("cuda_probe_device={}".format(torch.empty((1,), device=device).device))
            except Exception as exc:
                failures.append("cuda-allocation")
                print("FAIL cuda allocation: {}: {}".format(type(exc).__name__, exc))

    if failures:
        print("FAILURES: {}".format(", ".join(failures)))
        return 1
    print("GeoSeg core environment checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
