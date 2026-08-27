#!/usr/bin/env python3
"""Bundled PaddleGAN export wrapper for static inference models."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


def parse_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value!r}")


def parse_inputs_size(text: str) -> List[List[int]]:
    shapes: List[List[int]] = []
    for raw_shape in (part.strip() for part in text.split(";")):
        if not raw_shape:
            continue
        dims: List[int] = []
        for raw_dim in (piece.strip() for piece in raw_shape.split(",")):
            if not raw_dim:
                continue
            try:
                dims.append(int(raw_dim))
            except ValueError as exc:
                raise argparse.ArgumentTypeError(
                    f"invalid integer dimension in inputs_size: {raw_dim!r}") from exc
        if not dims:
            raise argparse.ArgumentTypeError(
                "each inputs_size segment must contain at least one integer")
        shapes.append(dims)
    if not shapes:
        raise argparse.ArgumentTypeError(
            "inputs_size must contain at least one shape segment")
    return shapes


def is_nested_weight_dict(state_dicts) -> bool:
    if not isinstance(state_dicts, dict) or not state_dicts:
        return False
    first_value = next(iter(state_dicts.values()))
    return isinstance(first_value, dict)


def expected_input_count(export_spec) -> Optional[int]:
    if not isinstance(export_spec, (list, tuple)) or not export_spec:
        return None
    total = 0
    for item in export_spec:
        if not isinstance(item, dict) or "inputs_num" not in item:
            return None
        try:
            total += int(item["inputs_num"])
        except (TypeError, ValueError):
            return None
    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export PaddleGAN checkpoints to static inference models.")
    parser.add_argument(
        "-c",
        "--config-file",
        metavar="FILE",
        required=True,
        help="PaddleGAN config file used to build the model.",
    )
    parser.add_argument(
        "--load",
        type=str,
        required=True,
        help="Checkpoint or pretrained weight file to load.",
    )
    parser.add_argument(
        "-o",
        "--opt",
        nargs="+",
        help="Set configuration overrides as KEY=VALUE items.",
    )
    parser.add_argument(
        "-s",
        "--inputs_size",
        type=parse_inputs_size,
        required=True,
        help=(
            "Semicolon-separated input shapes such as '1,3,256,256;1,3,256,256'."
        ),
    )
    parser.add_argument(
        "--output_dir",
        default="./inference_model",
        type=str,
        help="Directory that will receive the exported static model files.",
    )
    parser.add_argument(
        "--export_serving_model",
        nargs="?",
        const=True,
        default=False,
        type=parse_bool,
        help="Also export Serving client/server artifacts.",
    )
    parser.add_argument(
        "--model_name",
        default=None,
        type=str,
        help=(
            "Override the export prefix. For generic multi-net exports this is "
            "ignored by the bundled wrapper to avoid clobbering one branch."
        ),
    )
    return parser


def load_runtime_modules():
    try:
        import ppgan
        from ppgan.models.base_model import BaseModel
        from ppgan.models.builder import build_model
        from ppgan.utils.config import get_config
        from ppgan.utils.filesystem import load as load_state
        from ppgan.utils.logger import get_logger
    except Exception as exc:  # pragma: no cover - import failure path
        raise RuntimeError(
            "PaddleGAN runtime modules are not available in this environment.") from exc
    return ppgan, BaseModel, build_model, get_config, load_state, get_logger


def load_checkpoint_into_model(model, state_dicts, model_name_hint: str, logger):
    nets = getattr(model, "nets", None)
    if not isinstance(nets, dict) or not nets:
        raise RuntimeError("The built model does not expose a nets dictionary.")

    lower_hint = f"{model_name_hint} {type(model).__name__}".lower()
    if "wav2lip" in lower_hint and "netG" in nets:
        if is_nested_weight_dict(state_dicts) and "netG" in state_dicts:
            state_dicts = state_dicts["netG"]
        nets["netG"].set_state_dict(state_dicts)
        logger.info("Loaded checkpoint into netG for Wav2Lip export.")
        return

    if is_nested_weight_dict(state_dicts):
        loaded_names = []
        for net_name, net in nets.items():
            if net_name in state_dicts:
                net.set_state_dict(state_dicts[net_name])
                loaded_names.append(net_name)
            else:
                logger.warning(
                    "Checkpoint does not contain a state dict for net %s; leaving that branch unchanged.",
                    net_name,
                )
        if not loaded_names:
            raise ValueError(
                "The checkpoint dict does not contain any keys that match model nets.")
        logger.info("Loaded checkpoint keys: %s", ", ".join(loaded_names))
        return

    if len(nets) == 1:
        net_name, net = next(iter(nets.items()))
        net.set_state_dict(state_dicts)
        logger.info("Loaded flat checkpoint into single net %s.", net_name)
        return

    raise ValueError(
        "The checkpoint is a flat state dict but the model exposes multiple nets; "
        "use the matching checkpoint or a model-specific export path.")


def validate_inputs_size(inputs_size, export_spec, custom_export: bool):
    if custom_export:
        return
    expected = expected_input_count(export_spec)
    if expected is None:
        if isinstance(export_spec, (list, tuple)) and export_spec:
            raise ValueError(
                "The generic export path expected named nets with inputs_num entries "
                "but the config export_model block is incomplete.")
        return
    if len(inputs_size) != expected:
        raise ValueError(
            f"inputs_size contains {len(inputs_size)} shape(s) but the export config expects {expected} input(s).")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    load_path = Path(args.load)
    if not load_path.exists():
        parser.error(f"checkpoint file not found: {args.load}")

    ppgan, BaseModel, build_model, get_config, load_state, get_logger = load_runtime_modules()
    cfg = get_config(args.config_file, args.opt, show=True)
    logger = get_logger(name="ppgan")

    model = build_model(cfg.model)
    if hasattr(model, "setup_train_mode"):
        model.setup_train_mode(is_train=False)

    logger.info("Loading checkpoint from %s", args.load)
    state_dicts = load_state(args.load)
    model_name_hint = str(getattr(getattr(cfg, "model", None), "name", ""))
    load_checkpoint_into_model(model, state_dicts, model_name_hint, logger)

    export_spec = getattr(cfg, "export_model", None)
    custom_export = type(model).export_model is not BaseModel.export_model
    validate_inputs_size(args.inputs_size, export_spec, custom_export)

    effective_model_name = args.model_name
    if (
        not custom_export
        and isinstance(export_spec, (list, tuple))
        and len(export_spec) > 1
        and args.model_name is not None
    ):
        logger.warning(
            "Ignoring --model_name for a multi-net generic export to avoid prefix collisions.")
        effective_model_name = None

    os.makedirs(args.output_dir, exist_ok=True)
    model.export_model(
        export_spec,
        args.output_dir,
        args.inputs_size,
        args.export_serving_model,
        effective_model_name,
    )
    logger.info("Export succeeded. Static model files were written under %s", args.output_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
