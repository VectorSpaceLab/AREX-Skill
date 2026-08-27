#!/usr/bin/env python3
"""Run an Alpamayo R1 inference smoke test on one PhysicalAI-AV clip.

This script mirrors the repository example in src/alpamayo_r1/test_inference.py,
but exposes CLI flags for the clip id, attention implementation, and optional
trajectory plotting.
"""

from __future__ import annotations

import argparse
import contextlib
from pathlib import Path

import numpy as np
import torch

from alpamayo_r1 import helper
from alpamayo_r1.load_physical_aiavdataset import load_physical_aiavdataset
from alpamayo_r1.models.alpamayo_r1 import AlpamayoR1

DEFAULT_MODEL_ID = "nvidia/Alpamayo-R1-10B"
DEFAULT_CLIP_ID = "030c760c-ae38-49aa-9ad8-f5650a545d26"
DEFAULT_T0_US = 5_100_000
DEFAULT_TOP_P = 0.98
DEFAULT_TEMPERATURE = 0.6
DEFAULT_NUM_TRAJ_SAMPLES = 1
DEFAULT_NUM_TRAJ_SETS = 1
DEFAULT_MAX_GENERATION_LENGTH = 256


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--clip-id", default=DEFAULT_CLIP_ID)
    parser.add_argument("--t0-us", type=int, default=DEFAULT_T0_US)
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--dtype",
        default="bfloat16",
        choices=("bfloat16", "float16", "float32"),
        help="Torch dtype to use when loading the model.",
    )
    parser.add_argument(
        "--attn-implementation",
        default="flash_attention_2",
        help="Attention backend to request from the model config.",
    )
    parser.add_argument("--num-traj-samples", type=int, default=DEFAULT_NUM_TRAJ_SAMPLES)
    parser.add_argument("--num-traj-sets", type=int, default=DEFAULT_NUM_TRAJ_SETS)
    parser.add_argument("--top-p", type=float, default=DEFAULT_TOP_P)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument(
        "--max-generation-length",
        type=int,
        default=DEFAULT_MAX_GENERATION_LENGTH,
    )
    parser.add_argument(
        "--maybe-stream",
        dest="maybe_stream",
        action="store_true",
        help="Stream the clip from Hugging Face if it is not cached locally.",
    )
    parser.add_argument(
        "--no-maybe-stream",
        dest="maybe_stream",
        action="store_false",
        help="Disable streaming and require a local copy of the clip.",
    )
    parser.set_defaults(maybe_stream=True)
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed used for torch CUDA sampling.",
    )
    parser.add_argument(
        "--plot-path",
        type=Path,
        default=None,
        help="Optional path for a saved XY trajectory plot.",
    )
    return parser.parse_args()


def resolve_dtype(name: str) -> torch.dtype:
    mapping = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    return mapping[name]


def print_text_traces(extra: dict[str, object]) -> None:
    for field in ("cot", "meta_action", "answer"):
        if field not in extra:
            continue
        arr = np.asarray(extra[field], dtype=object)
        print(f"{field}:")
        for set_idx in range(arr.shape[1]):
            for sample_idx in range(arr.shape[2]):
                print(f"  [{set_idx}, {sample_idx}] {arr[0, set_idx, sample_idx]}")


def compute_min_ade(pred_xyz: torch.Tensor, gt_xyz: torch.Tensor) -> tuple[float, int]:
    pred_xy = pred_xyz.detach().cpu().numpy()[0, :, :, :, :2].reshape(-1, pred_xyz.shape[-2], 2)
    gt_xy = gt_xyz.detach().cpu().numpy()[0, 0, :, :2]
    diff = np.linalg.norm(pred_xy - gt_xy[None, :, :], axis=-1).mean(-1)
    best_idx = int(diff.argmin())
    return float(diff.min()), best_idx


def maybe_save_plot(pred_xyz: torch.Tensor, gt_xyz: torch.Tensor, plot_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - optional visualization dependency
        raise RuntimeError("matplotlib is required when --plot-path is set") from exc

    def rotate_90cc(xy: np.ndarray) -> np.ndarray:
        return np.stack([-xy[1], xy[0]], axis=0)

    pred_xy = pred_xyz.detach().cpu().numpy()[0, :, :, :, :2].reshape(-1, pred_xyz.shape[-2], 2)
    gt_xy = gt_xyz.detach().cpu().numpy()[0, 0, :, :2].T

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 6))
    for idx, traj in enumerate(pred_xy):
        traj_rot = rotate_90cc(traj.T)
        plt.plot(*traj_rot, "o-", label=f"Predicted #{idx + 1}")
    plt.plot(*rotate_90cc(gt_xy), "r-", label="Ground Truth")
    plt.ylabel("y coordinate (meters)")
    plt.xlabel("x coordinate (meters)")
    plt.axis("equal")
    plt.legend(loc="best")
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved trajectory plot to {plot_path}")


def main() -> int:
    args = parse_args()
    if not args.device.startswith("cuda"):
        raise ValueError("Alpamayo R1 inference is CUDA-primary; use a CUDA device.")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available in this environment.")

    dtype = resolve_dtype(args.dtype)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    print(f"Loading dataset for clip_id: {args.clip_id}...")
    data = load_physical_aiavdataset(
        args.clip_id,
        t0_us=args.t0_us,
        maybe_stream=args.maybe_stream,
    )
    print("Dataset loaded.")
    print("image_frames shape:", tuple(data["image_frames"].shape))
    print("ego_history_xyz shape:", tuple(data["ego_history_xyz"].shape))
    print("ego_future_xyz shape:", tuple(data["ego_future_xyz"].shape))
    print("camera_indices:", data["camera_indices"].tolist())

    frames = data["image_frames"].flatten(0, 1)
    messages = helper.create_message(frames)

    model = AlpamayoR1.from_pretrained(
        args.model_id,
        dtype=dtype,
        attn_implementation=args.attn_implementation,
    ).to(args.device)
    processor = helper.get_processor(model.tokenizer)

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
        continue_final_message=True,
        return_dict=True,
        return_tensors="pt",
    )
    tokenized_data = dict(inputs)
    model_inputs = helper.to_device(
        {
            "tokenized_data": tokenized_data,
            "ego_history_xyz": data["ego_history_xyz"],
            "ego_history_rot": data["ego_history_rot"],
        },
        args.device,
    )

    autocast_ctx = (
        torch.autocast("cuda", dtype=dtype)
        if dtype != torch.float32
        else contextlib.nullcontext()
    )

    with autocast_ctx:
        pred_xyz, pred_rot, extra = model.sample_trajectories_from_data_with_vlm_rollout(
            data=model_inputs,
            top_p=args.top_p,
            top_k=args.top_k,
            temperature=args.temperature,
            num_traj_samples=args.num_traj_samples,
            num_traj_sets=args.num_traj_sets,
            max_generation_length=args.max_generation_length,
            return_extra=True,
        )

    print("pred_xyz shape:", tuple(pred_xyz.shape))
    print("pred_rot shape:", tuple(pred_rot.shape))
    print_text_traces(extra)

    min_ade, best_idx = compute_min_ade(pred_xyz, data["ego_future_xyz"])
    print("minADE:", min_ade, "meters")
    print("best trajectory index:", best_idx)

    if args.plot_path is not None:
        maybe_save_plot(pred_xyz, data["ego_future_xyz"], args.plot_path)

    print(
        "Note: VLA-reasoning outputs are sampled, so minADE and reasoning traces "
        "can vary across runs and hardware."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
