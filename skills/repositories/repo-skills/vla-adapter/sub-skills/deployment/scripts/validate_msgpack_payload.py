#!/usr/bin/env python3
"""Validate or generate a VLA-Adapter ALOHA MsgPack action payload safely."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

REQUIRED_KEYS = ["full_image", "left_wrist_image", "right_wrist_image", "state", "instruction", "unnorm_key"]


def fake_payload(height: int, width: int, state_dim: int, instruction: str, unnorm_key: str) -> dict[str, Any]:
    rng = np.random.default_rng(7)
    def image(phase: float) -> np.ndarray:
        base = rng.uniform(0, 255, size=(height, width, 3))
        return np.clip(base + phase, 0, 255).astype(np.uint8)
    return {
        "full_image": image(0),
        "left_wrist_image": image(1),
        "right_wrist_image": image(2),
        "state": np.zeros(state_dim, dtype=np.float32),
        "instruction": instruction,
        "unnorm_key": unnorm_key,
    }


def validate(payload: dict[str, Any], state_dim: int) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"missing key: {key}")
    for key in ["full_image", "left_wrist_image", "right_wrist_image"]:
        if key in payload:
            arr = np.asarray(payload[key])
            if arr.ndim != 3 or arr.shape[-1] != 3:
                errors.append(f"{key} must have shape HxWx3, got {arr.shape}")
            if arr.dtype != np.uint8:
                errors.append(f"{key} should be uint8, got {arr.dtype}")
    if "state" in payload:
        state = np.asarray(payload["state"])
        if state.shape != (state_dim,):
            errors.append(f"state must have shape ({state_dim},), got {state.shape}")
    for key in ["instruction", "unnorm_key"]:
        if key in payload and not str(payload[key]).strip():
            errors.append(f"{key} must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or generate an ALOHA MsgPack payload.")
    parser.add_argument("--height", type=int, default=224)
    parser.add_argument("--width", type=int, default=224)
    parser.add_argument("--state-dim", type=int, default=14)
    parser.add_argument("--instruction", default="open the box")
    parser.add_argument("--unnorm-key", default="bowl_stack_and_shelf_aloha_realworld_50")
    parser.add_argument("--write-msgpack", type=Path, help="Optional output path for a generated msgpack payload.")
    args = parser.parse_args()

    payload = fake_payload(args.height, args.width, args.state_dim, args.instruction, args.unnorm_key)
    errors = validate(payload, args.state_dim)
    if errors:
        for err in errors:
            print(f"FAIL: {err}")
        return 1
    print("PASS: synthetic payload contains required keys and expected shapes")
    print(f"images: {args.height}x{args.width}x3 uint8; state_dim={args.state_dim}; unnorm_key={args.unnorm_key}")

    if args.write_msgpack:
        import msgpack
        import msgpack_numpy

        args.write_msgpack.parent.mkdir(parents=True, exist_ok=True)
        with args.write_msgpack.open("wb") as f:
            f.write(msgpack.packb(payload, default=msgpack_numpy.encode, use_bin_type=True))
        print(f"PASS: wrote msgpack payload to {args.write_msgpack}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
