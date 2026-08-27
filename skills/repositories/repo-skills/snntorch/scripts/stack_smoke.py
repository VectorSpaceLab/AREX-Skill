#!/usr/bin/env python3
"""Broad snnTorch import and backend smoke.

The script imports the primary public surfaces, prints versions, and can
optionally probe a tiny CUDA allocation. It is intentionally synthetic and does
not read datasets or run long training.
"""

from __future__ import annotations

import argparse
import json
import warnings
from importlib import metadata
from typing import Any


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _import_surface() -> dict[str, Any]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        import torch
        import snntorch as snn
        from snntorch import spikegen, surrogate, utils
        import snntorch.functional as SF
        import snntorch.spikeplot as splt
        from snntorch.export_nir import export_to_nir
        from snntorch.import_nir import import_from_nir
        from snntorch.spikevision import spikedata

    return {
        "warnings": [str(item.message) for item in caught],
        "versions": {
            "snntorch": _dist_version("snntorch"),
            "torch": _dist_version("torch"),
            "torchvision": _dist_version("torchvision"),
            "nir": _dist_version("nir"),
            "nirtorch": _dist_version("nirtorch"),
            "matplotlib": _dist_version("matplotlib"),
            "pandas": _dist_version("pandas"),
        },
        "imports": {
            "snntorch": "ok",
            "spikegen": str(spikegen.rate),
            "surrogate": str(surrogate.fast_sigmoid),
            "functional": str(SF.ce_count_loss),
            "utils": str(utils.reset),
            "spikeplot": str(splt.raster),
            "export_to_nir": str(export_to_nir),
            "import_from_nir": str(import_from_nir),
            "spikevision": sorted(getattr(spikedata, "__all__", [])),
        },
    }


def _cuda_probe() -> dict[str, Any]:
    import torch

    if not torch.cuda.is_available():
        return {"available": False}

    x = torch.empty(1, device="cuda")
    return {
        "available": True,
        "device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0),
        "capability": list(torch.cuda.get_device_capability(0)),
        "allocation": str(x.device),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cuda",
        action="store_true",
        help="also allocate a tiny CUDA tensor if torch.cuda.is_available()",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of pretty text",
    )
    args = parser.parse_args()

    payload: dict[str, Any] = {"surface": _import_surface()}
    if args.cuda:
        payload["cuda"] = _cuda_probe()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print("[snnTorch] versions")
        for name, value in payload["surface"]["versions"].items():
            print(f"  {name}: {value}")
        if payload["surface"]["warnings"]:
            print("[snnTorch] warnings")
            for warning in payload["surface"]["warnings"]:
                print(f"  {warning}")
        print("[snnTorch] imports")
        for name, value in payload["surface"]["imports"].items():
            print(f"  {name}: {value}")
        if args.cuda:
            print("[snnTorch] cuda")
            print(json.dumps(payload["cuda"], indent=2, sort_keys=True, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
