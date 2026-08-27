#!/usr/bin/env python3
"""Create a smaller ProtoMotions MotionLib by selecting every Nth motion.

This is adapted from the ProtoMotions utility for safe CPU-side debugging. It
expects a packaged MotionLib .pt dictionary with frame-indexed fields.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch


FRAME_INDEXED_FIELDS = ["gts", "grs", "gvs", "gavs", "dvs", "dps", "contacts", "lrs"]
MOTION_INDEXED_FIELDS = ["motion_lengths", "motion_dt", "motion_weights"]


def subset_motion_lib(input_path: str, output_path: str, sample_every: int = 200) -> dict:
    if sample_every <= 0:
        raise ValueError("sample_every must be positive")
    data = torch.load(input_path, map_location="cpu", weights_only=False)
    required = ["motion_num_frames", "length_starts"]
    missing = [key for key in required if key not in data]
    if missing:
        raise KeyError(f"Input is missing required MotionLib fields: {missing}")

    num_motions = len(data["motion_num_frames"])
    selected_indices = list(range(0, num_motions, sample_every))
    frame_indices: list[int] = []
    new_motion_num_frames = []
    for idx in selected_indices:
        start = int(data["length_starts"][idx].item())
        frames = int(data["motion_num_frames"][idx].item())
        frame_indices.extend(range(start, start + frames))
        new_motion_num_frames.append(frames)

    frame_index_tensor = torch.tensor(frame_indices, dtype=torch.long)
    new_data = {}
    for field in FRAME_INDEXED_FIELDS:
        value = data.get(field)
        if value is not None and torch.is_tensor(value):
            new_data[field] = value[frame_index_tensor]

    new_frames_tensor = torch.tensor(new_motion_num_frames, dtype=torch.long)
    shifted = new_frames_tensor.roll(1)
    if len(shifted):
        shifted[0] = 0
    new_data["length_starts"] = shifted.cumsum(0)
    new_data["motion_num_frames"] = new_frames_tensor

    for field in MOTION_INDEXED_FIELDS:
        value = data.get(field)
        if value is not None and torch.is_tensor(value):
            new_data[field] = value[selected_indices].clone()

    if "motion_files" in data:
        new_data["motion_files"] = tuple(data["motion_files"][idx] for idx in selected_indices)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(new_data, output)
    return {
        "input_motions": num_motions,
        "output_motions": len(selected_indices),
        "input_frames": int(sum(int(x.item()) for x in data["motion_num_frames"])),
        "output_frames": len(frame_indices),
        "output": str(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input packaged MotionLib .pt")
    parser.add_argument("output", help="Output packaged MotionLib .pt")
    parser.add_argument("--sample-every", type=int, default=200)
    args = parser.parse_args()
    summary = subset_motion_lib(args.input, args.output, args.sample_every)
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
