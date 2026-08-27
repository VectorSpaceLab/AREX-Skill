#!/usr/bin/env python3
"""Extract EMA weights from a D-FINE checkpoint and save a model-only checkpoint."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path

import torch


def _derive_output_path(input_path: Path) -> Path:
    suffix = input_path.suffix or ".pth"
    return input_path.with_name(f"{input_path.stem}_converted{suffix}")


def extract_ema_weights(checkpoint: object) -> dict[str, object]:
    if not isinstance(checkpoint, Mapping):
        raise TypeError(
            f"Expected a checkpoint mapping, got {type(checkpoint).__name__}."
        )
    if "ema" not in checkpoint:
        raise KeyError("Checkpoint does not contain an 'ema' entry.")

    ema = checkpoint["ema"]
    if isinstance(ema, Mapping):
        if "module" not in ema:
            raise KeyError("checkpoint['ema'] does not contain a 'module' entry.")
        module = ema["module"]
    elif hasattr(ema, "module"):
        module = ema.module
    else:
        raise TypeError(
            "checkpoint['ema'] must be a mapping with a 'module' key or an object with a 'module' attribute."
        )

    return {"model": module}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract EMA weights from a D-FINE checkpoint and save a model-only checkpoint."
    )
    parser.add_argument("checkpoint", help="Input checkpoint containing ema.module weights.")
    parser.add_argument(
        "-o",
        "--output",
        help="Output checkpoint path. Defaults to <stem>_converted<suffix> next to the input.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect the checkpoint and print the planned output path without writing anything.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.checkpoint)
    if not input_path.exists():
        raise SystemExit(f"Checkpoint not found: {input_path}")

    checkpoint = torch.load(input_path, map_location="cpu")
    extracted = extract_ema_weights(checkpoint)

    output_path = Path(args.output) if args.output else _derive_output_path(input_path)
    if output_path.exists() and not args.overwrite:
        raise SystemExit(
            f"Output already exists: {output_path}. Use --overwrite to replace it."
        )

    print(f"input: {input_path}")
    print(f"output: {output_path}")
    print("saved keys: model")
    if args.dry_run:
        print("dry-run: no file written")
        return 0

    torch.save(extracted, output_path)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
