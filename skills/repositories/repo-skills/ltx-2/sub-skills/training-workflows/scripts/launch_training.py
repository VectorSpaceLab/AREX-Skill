#!/usr/bin/env python3
"""Launch LTX Trainer from a YAML config after explicit user approval.

This is a self-contained wrapper around the installed `ltx_trainer` package.
It performs the same config loading and trainer construction as the upstream
training entry point, but it lives inside the generated skill tree so future
agents do not need the source checkout path.

Example:
    python path/to/training-workflows/scripts/launch_training.py /path/to/config.yaml --disable-progress-bars
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_path", type=Path, help="Path to an LTX Trainer YAML config")
    parser.add_argument(
        "--disable-progress-bars",
        action="store_true",
        help="Disable progress bars (useful for multi-process runs)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.config_path.exists():
        raise SystemExit(f"Error: configuration file does not exist: {args.config_path}")

    try:
        import yaml
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Error: PyYAML is required to read configs: {exc}") from exc

    try:
        from ltx_trainer.config import LtxTrainerConfig
        from ltx_trainer.trainer import LtxvTrainer
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Error: ltx_trainer is not available in the active environment: {exc}") from exc

    with args.config_path.open("r", encoding="utf-8") as handle:
        config_data = yaml.safe_load(handle)

    try:
        trainer_config = LtxTrainerConfig(**config_data)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Error: invalid configuration data: {exc}") from exc

    trainer = LtxvTrainer(trainer_config)
    trainer.train(disable_progress_bars=args.disable_progress_bars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
