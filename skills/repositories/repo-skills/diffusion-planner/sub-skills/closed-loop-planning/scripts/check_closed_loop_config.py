#!/usr/bin/env python3
"""Safe preflight checks for a DiffusionPlanner closed-loop run.

This helper intentionally avoids importing nuPlan, Ray, or torch by default. It
checks the external paths and the model-side JSON contract before a Hydra run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SPLIT_TO_BUILDER = {
    "val14": "nuplan",
    "test14-random": "nuplan_challenge",
    "test14-hard": "nuplan_challenge",
    # This is the runner's automatic result, not a universal requirement.
    "val14-collision": "nuplan_challenge",
}
CHALLENGES = {"closed_loop_nonreactive_agents", "closed_loop_reactive_agents"}
REQUIRED_MODEL_KEYS = {
    "agent_num",
    "decoder_depth",
    "decoder_drop_path_rate",
    "device",
    "diffusion_model_type",
    "encoder_depth",
    "encoder_drop_path_rate",
    "future_len",
    "hidden_dim",
    "lane_len",
    "lane_num",
    "num_heads",
    "predicted_neighbor_num",
    "route_len",
    "route_num",
    "static_objects_num",
    "static_objects_state_dim",
    "time_len",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DiffusionPlanner checkpoint/config paths, JSON shape, "
            "split/challenge choices, and nuPlan root directories without "
            "starting Hydra, Ray, or a simulation."
        )
    )
    parser.add_argument("--args-file", required=True, help="Path to model args.json")
    parser.add_argument("--checkpoint", required=True, help="Path to model.pth")
    parser.add_argument(
        "--split",
        required=True,
        choices=sorted(SPLIT_TO_BUILDER),
        help="Packaged scenario filter name",
    )
    parser.add_argument(
        "--challenge",
        required=True,
        choices=sorted(CHALLENGES),
        help="nuPlan simulation challenge",
    )
    parser.add_argument(
        "--builder",
        choices=("auto", "nuplan", "nuplan_challenge"),
        default="auto",
        help="Scenario builder; auto mirrors the supplied shell runner",
    )
    parser.add_argument(
        "--device", choices=("cpu", "cuda"), default="cuda", help="Planner device"
    )
    parser.add_argument("--nuplan-devkit-root", help="Optional installed devkit root")
    parser.add_argument("--data-root", help="Optional NUPLAN_DATA_ROOT")
    parser.add_argument("--maps-root", help="Optional NUPLAN_MAPS_ROOT")
    parser.add_argument("--exp-root", help="Optional NUPLAN_EXP_ROOT")
    parser.add_argument(
        "--future-poses",
        type=int,
        help="Optional override to compare with args.json future_len",
    )
    parser.add_argument(
        "--strict-pairing",
        action="store_true",
        help="Fail when val14-collision uses the runner's ambiguous auto pairing",
    )
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Probe torch.cuda availability (optional dependency/import)",
    )
    return parser


def _file_check(value: str, label: str, errors: List[str]) -> Optional[Path]:
    path = Path(value).expanduser()
    if not path.exists():
        errors.append("{} does not exist: {}".format(label, path))
        return None
    if not path.is_file():
        errors.append("{} is not a file: {}".format(label, path))
        return None
    if not os.access(str(path), os.R_OK):
        errors.append("{} is not readable: {}".format(label, path))
    if path.stat().st_size == 0:
        errors.append("{} is empty: {}".format(label, path))
    return path


def _dir_check(value: Optional[str], label: str, errors: List[str]) -> None:
    if value is None:
        return
    path = Path(value).expanduser()
    if not path.exists():
        errors.append("{} does not exist: {}".format(label, path))
    elif not path.is_dir():
        errors.append("{} is not a directory: {}".format(label, path))


def _json_check(path: Optional[Path], errors: List[str], warnings: List[str]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError) as exc:
        errors.append("args-file is not valid JSON: {} ({})".format(path, exc))
        return {}
    if not isinstance(payload, dict):
        errors.append("args-file top level must be a JSON object")
        return {}

    missing = sorted(REQUIRED_MODEL_KEYS.difference(payload))
    if missing:
        errors.append("args-file missing model keys: {}".format(", ".join(missing)))

    for name in ("state_normalizer", "observation_normalizer"):
        value = payload.get(name)
        if not isinstance(value, dict):
            errors.append("args-file field {} must be an object".format(name))
            continue
        if name == "state_normalizer":
            for stat in ("mean", "std"):
                if stat not in value:
                    errors.append("state_normalizer is missing {}".format(stat))
        else:
            for feature, entry in value.items():
                if not isinstance(entry, dict) or "mean" not in entry or "std" not in entry:
                    errors.append(
                        "observation_normalizer entry {!r} needs mean and std".format(feature)
                    )

    future_len = payload.get("future_len")
    if future_len is not None:
        try:
            future_len_int = int(future_len)
            if future_len_int <= 0:
                errors.append("args-file future_len must be positive")
            elif future_len_int != future_len:
                warnings.append("args-file future_len is not an integer: {!r}".format(future_len))
            return {"future_len": future_len_int}
        except (TypeError, ValueError):
            errors.append("args-file future_len must be an integer")
    return {}


def _cuda_check(errors: List[str], warnings: List[str]) -> None:
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller environment
        errors.append("--check-cuda requested but torch could not import: {}".format(exc))
        return
    if not torch.cuda.is_available():
        errors.append("--check-cuda requested but torch.cuda.is_available() is false")
    else:
        warnings.append("CUDA is available: {} device(s)".format(torch.cuda.device_count()))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    errors: List[str] = []
    warnings: List[str] = []

    args_path = _file_check(args.args_file, "args-file", errors)
    checkpoint_path = _file_check(args.checkpoint, "checkpoint", errors)
    model_info = _json_check(args_path, errors, warnings)

    for value, label in (
        (args.nuplan_devkit_root, "nuPlan devkit root"),
        (args.data_root, "data root"),
        (args.maps_root, "maps root"),
        (args.exp_root, "experiment root"),
    ):
        _dir_check(value, label, errors)

    expected_builder = SPLIT_TO_BUILDER[args.split]
    actual_builder = expected_builder if args.builder == "auto" else args.builder
    if args.split == "val14-collision" and args.builder == "auto":
        message = (
            "val14-collision is a curated four-token filter; auto mirrors the "
            "runner and selects nuplan_challenge. Confirm the local DB/mapping "
            "or pass --builder explicitly."
        )
        if args.strict_pairing:
            errors.append(message)
        else:
            warnings.append(message)
    if args.split == "val14" and args.builder == "nuplan_challenge":
        warnings.append("val14 normally pairs with nuplan; challenge pairing is an explicit override")
    if args.split.startswith("test14") and args.builder == "nuplan":
        warnings.append("{} normally pairs with nuplan_challenge; nuplan was explicitly selected".format(args.split))

    if args.future_poses is not None:
        if args.future_poses <= 0:
            errors.append("--future-poses must be positive")
        elif model_info.get("future_len") is not None and args.future_poses != model_info["future_len"]:
            warnings.append(
                "future pose override ({}) differs from args.json future_len ({}); "
                "verify checkpoint compatibility".format(args.future_poses, model_info["future_len"])
            )

    if args.check_cuda:
        _cuda_check(errors, warnings)

    print("closed-loop preflight")
    print("  split: {}".format(args.split))
    print("  challenge: {}".format(args.challenge))
    print("  builder: {} (requested: {})".format(actual_builder, args.builder))
    print("  device: {}".format(args.device))
    print("  args-file: {}".format(Path(args.args_file).expanduser()))
    print("  checkpoint: {}".format(Path(args.checkpoint).expanduser()))
    for warning in warnings:
        print("WARNING: {}".format(warning), file=sys.stderr)
    if errors:
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
        print("NOT READY: resolve the errors before launching Hydra/Ray", file=sys.stderr)
        return 2
    print("READY FOR NEXT CHECK: paths and static planner contract passed")
    print("NOTE: this helper does not prove dataset/map/checkpoint compatibility or run simulation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
