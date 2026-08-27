#!/usr/bin/env python3
"""Create a tiny synthetic HiFi-GAN generator checkpoint from bundled runtime.

The helper writes a `g_########` file containing a `generator` state dict plus a
paired `config.json` in the same output directory. It can also intentionally
copy a mismatched config for checkpoint/config troubleshooting cases. It does
not require an external HiFi-GAN checkout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = SKILL_ROOT / "scripts" / "hifigan_runtime"
CONFIG_DIR = RUNTIME_DIR / "configs"
CONFIG_ALIASES = {
    "1": "config_v1.json",
    "v1": "config_v1.json",
    "config-v1": "config_v1.json",
    "config_v1": "config_v1.json",
    "config_v1.json": "config_v1.json",
    "2": "config_v2.json",
    "v2": "config_v2.json",
    "config-v2": "config_v2.json",
    "config_v2": "config_v2.json",
    "config_v2.json": "config_v2.json",
    "3": "config_v3.json",
    "v3": "config_v3.json",
    "config-v3": "config_v3.json",
    "config_v3": "config_v3.json",
    "config_v3.json": "config_v3.json",
}


def resolve_existing_path(raw: str) -> Path:
    """Resolve a bundled config alias/name or an explicit filesystem path."""
    alias = CONFIG_ALIASES.get(raw.lower())
    if alias:
        return (CONFIG_DIR / alias).resolve()

    candidate = Path(raw).expanduser()
    if candidate.exists():
        return candidate.resolve()

    bundled = CONFIG_DIR / raw
    if bundled.exists():
        return bundled.resolve()

    raise FileNotFoundError(f"Could not find config file: {raw}")


def load_config(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def short_path(path: Path) -> str:
    try:
        return str(path.relative_to(SKILL_ROOT))
    except ValueError:
        return path.name


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a synthetic HiFi-GAN generator checkpoint and paired config.json "
            "from the skill's bundled runtime source."
        )
    )
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write the checkpoint bundle into.")
    parser.add_argument(
        "--state-config",
        default="v1",
        help="Config used to build the generator weights: v1, v2, v3, a bundled config filename, or a JSON path.",
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help="Config copied beside the checkpoint as config.json. Defaults to --state-config.",
    )
    parser.add_argument(
        "--checkpoint-name",
        default="g_00000000",
        help="Filename to use for the generator checkpoint inside the output directory.",
    )
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for deterministic init.")
    args = parser.parse_args()

    if str(RUNTIME_DIR) not in sys.path:
        sys.path.insert(0, str(RUNTIME_DIR))

    import torch
    from env import AttrDict
    from models import Generator

    state_config_path = resolve_existing_path(args.state_config)
    copy_config_path = resolve_existing_path(args.config_file or args.state_config)
    h = AttrDict(load_config(state_config_path))

    torch.manual_seed(args.seed)
    generator = Generator(h)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.output_dir / args.checkpoint_name
    torch.save({"generator": generator.state_dict()}, checkpoint_path)

    config_out = args.output_dir / "config.json"
    shutil.copyfile(copy_config_path, config_out)

    print(f"Wrote checkpoint: {checkpoint_path.name}")
    print(f"Wrote config: {config_out.name}")
    print(f"State config: {short_path(state_config_path)}")
    print(f"Copied config: {short_path(copy_config_path)}")


if __name__ == "__main__":
    main()
