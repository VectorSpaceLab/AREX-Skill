#!/usr/bin/env python3
"""Validate the audio/music demo config and checkpoint layout.

This helper checks the placeholder paths and required subdirectories used by
Lumina's text-to-audio and text-to-music demos.

Examples:
    python check_audio_music_inputs.py --kind audio --config configs/lumina-text2audio.yaml --ckpt-root /path/to/ckpt
    python check_audio_music_inputs.py --kind music --config configs/lumina-text2music.yaml --ckpt-root /path/to/ckpt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


EXPECTED_SUBDIRS = {
    "audio": ["audio_generation", "maa2", "bigvnat", "CLAP"],
    "music": ["music_generation", "maa2", "bigvnat"],
}


def nested_get(data, path: list[str]):
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(EXPECTED_SUBDIRS), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--ckpt-root", type=Path, default=None)
    parser.add_argument("--must-resolve", action="store_true", help="Fail if config paths still look like placeholders.")
    args = parser.parse_args()

    ok = True
    config_path = args.config.resolve()
    print(f"kind={args.kind}")
    print(f"config={config_path}")
    if not config_path.exists():
        print("FAIL: config file does not exist")
        return 1

    with config_path.open() as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print("FAIL: config did not parse as a mapping")
        return 1

    if args.ckpt_root is not None:
        ckpt_root = args.ckpt_root.resolve()
        print(f"ckpt_root={ckpt_root}")
        if not ckpt_root.exists():
            print("FAIL: checkpoint root does not exist")
            ok = False
        else:
            for rel in EXPECTED_SUBDIRS[args.kind]:
                path = ckpt_root / rel
                if path.exists():
                    print(f"  OK {rel}")
                else:
                    print(f"  FAIL missing {rel}")
                    ok = False

    if args.kind == "audio":
        ckpt_path = nested_get(config, ["model", "params", "first_stage_config", "params", "ckpt_path"])
        weights_path = nested_get(config, ["model", "params", "cond_stage_config", "params", "weights_path"])
        print(f"first_stage_ckpt_path={ckpt_path}")
        print(f"cond_stage_weights_path={weights_path}")
        if ckpt_path is None or weights_path is None:
            print("FAIL: audio config is missing ckpt_path or weights_path")
            ok = False
        if args.must_resolve and (not ckpt_path or "path/to" in str(ckpt_path) or "<real_ckpt_path>" in str(ckpt_path)):
            print("FAIL: audio config still contains placeholder ckpt paths")
            ok = False

    if args.kind == "music":
        ckpt_path = nested_get(config, ["model", "params", "first_stage_config", "params", "ckpt_path"])
        print(f"first_stage_ckpt_path={ckpt_path}")
        if ckpt_path is None:
            print("FAIL: music config is missing first_stage ckpt_path")
            ok = False
        if args.must_resolve and (not ckpt_path or "path/to" in str(ckpt_path) or "<real_ckpt_path>" in str(ckpt_path)):
            print("FAIL: music config still contains placeholder ckpt paths")
            ok = False

    if ok:
        print("Result: audio/music inputs look valid.")
        return 0

    print("Result: audio/music inputs need fixes.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
