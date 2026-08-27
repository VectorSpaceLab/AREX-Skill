#!/usr/bin/env python3
"""Tiny no-download Accelerate big-model API smoke check."""

import argparse
import json


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Construct a tiny model on the meta device and infer a CPU-only device map. "
            "No downloads, checkpoints, GPUs, or forward passes are used."
        )
    )
    parser.add_argument(
        "--max-cpu-memory",
        default="256MiB",
        help="CPU memory budget passed to infer_auto_device_map, e.g. 256MiB or 1GiB.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a short text summary.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    import torch
    import torch.nn as nn
    from accelerate import init_empty_weights
    from accelerate.utils import compute_module_sizes, infer_auto_device_map

    class TinyResidualBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Linear(8, 8)
            self.mlp = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 8))

        def forward(self, inputs):
            return inputs + self.mlp(self.proj(inputs))

    class TinyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.block0 = TinyResidualBlock()
            self.block1 = TinyResidualBlock()
            self.head = nn.Linear(8, 2)

        def forward(self, inputs):
            return self.head(self.block1(self.block0(inputs)))

    with init_empty_weights():
        model = TinyModel()

    parameter_devices = sorted({parameter.device.type for parameter in model.parameters()})
    module_sizes = compute_module_sizes(model)
    device_map = infer_auto_device_map(
        model,
        max_memory={"cpu": args.max_cpu_memory},
        no_split_module_classes=["TinyResidualBlock"],
    )

    result = {
        "torch_version": torch.__version__,
        "parameter_devices": parameter_devices,
        "total_size_bytes": int(module_sizes.get("", 0)),
        "device_map": {key: str(value) for key, value in device_map.items()},
        "safe": "no downloads, no checkpoint loading, no GPU calls, no forward pass",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Accelerate big-model smoke check passed")
        print(f"parameter devices: {', '.join(parameter_devices)}")
        print(f"total size bytes: {result['total_size_bytes']}")
        print(f"device map: {result['device_map']}")
        print(result["safe"])


if __name__ == "__main__":
    main()
