#!/usr/bin/env python3
"""Convert a TabPFN checkpoint to SafeTensors."""

from __future__ import annotations

import argparse
from pathlib import Path

from tabpfn.checkpoint import Checkpoint, save_as_safetensors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-checkpoint", required=True, type=Path)
    parser.add_argument("--output-safetensors", required=True, type=Path)
    args = parser.parse_args()

    checkpoint = Checkpoint(args.input_checkpoint).load()
    save_as_safetensors(checkpoint, args.output_safetensors)
    print(f"saved: {args.output_safetensors}")


if __name__ == "__main__":
    main()
