#!/usr/bin/env python3
"""Validate a MatterGen generation request and optionally run it.

This is a deliberately conservative companion to MatterGen's Fire-based
``mattergen-generate`` entry point. Parsing/validation is the default action:
no MatterGen import, Hub request, checkpoint load, or sampling job happens
unless the caller supplies ``--run``.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

MODEL_NAMES = {
    "mattergen_base",
    "mp_20_base",
    "chemical_system",
    "space_group",
    "dft_mag_density",
    "dft_band_gap",
    "ml_bulk_modulus",
    "dft_mag_density_hhi_score",
    "chemical_system_energy_above_hull",
}
NUM_ATOMS_DISTRIBUTIONS = {"ALEX_MP_20"}
KNOWN_PROPERTIES = {
    "dft_mag_density",
    "dft_bulk_modulus",
    "dft_shear_modulus",
    "energy_above_hull",
    "formation_energy_per_atom",
    "space_group",
    "hhi_score",
    "ml_bulk_modulus",
    "chemical_system",
    "dft_band_gap",
}
ELEMENT_RE = re.compile(r"^[A-Z][a-z]?$")
# The native CLI applies this mask so generated elements remain in the supported
# set. It is passed to the public checkpoint/API configuration path only during
# an explicitly requested run.
ELEMENT_MASK_OVERRIDE = (
    "++lightning_module.diffusion_module.model.element_mask_func="
    "{_target_:'mattergen.denoiser.mask_disallowed_elements',_partial_:True}"
)


def parse_literal(value: str, label: str) -> Any:
    """Parse JSON or Python-literal syntax without executing arbitrary code."""
    text = value.strip()
    if not text:
        raise ValueError(f"{label} cannot be empty")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(
                f"{label} must be JSON or a Python literal mapping/list; "
                f"received {value!r}"
            ) from exc


def parse_mapping(value: str, label: str) -> dict[str, Any]:
    parsed = parse_literal(value, label)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be an object/mapping, not {type(parsed).__name__}")
    for key in parsed:
        if not isinstance(key, str) or not key:
            raise ValueError(f"{label} keys must be non-empty strings")
    return parsed


def parse_compositions(values: list[str] | None) -> list[dict[str, int]]:
    compositions: list[dict[str, int]] = []
    for raw in values or []:
        parsed = parse_literal(raw, "target composition")
        if isinstance(parsed, dict):
            parsed_items = [parsed]
        elif isinstance(parsed, list):
            parsed_items = parsed
        else:
            raise ValueError("target composition must be a mapping or a list of mappings")
        for index, item in enumerate(parsed_items):
            if not isinstance(item, dict) or not item:
                raise ValueError(f"target composition {index} must be a non-empty mapping")
            normalized: dict[str, int] = {}
            for element, count in item.items():
                if not isinstance(element, str) or not ELEMENT_RE.fullmatch(element):
                    raise ValueError(
                        f"target composition element {element!r} is not a valid-looking symbol"
                    )
                # bool is an int subclass but is not a meaningful atom count.
                if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
                    raise ValueError(
                        f"target composition count for {element} must be a positive integer"
                    )
                normalized[element] = count
            compositions.append(normalized)
    return compositions


def parse_epoch(value: str) -> str | int:
    if value in {"last", "best"}:
        return value
    try:
        epoch = int(value)
    except ValueError as exc:
        raise ValueError("checkpoint epoch must be 'last', 'best', or an integer") from exc
    if epoch < 0:
        raise ValueError("checkpoint epoch must be nonnegative")
    return epoch


def _looks_like_lfs_pointer(path: Path) -> bool:
    try:
        if path.stat().st_size > 4096:
            return False
        return "git-lfs.github.com/spec/v1" in path.read_text(errors="replace")
    except OSError:
        return False


def inspect_local_checkpoint(model_path: str) -> tuple[list[str], list[str]]:
    """Return errors and warnings for a local checkpoint directory."""
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(model_path).expanduser()
    if not path.exists():
        return [f"local model_path does not exist: {model_path}"], warnings
    if not path.is_dir():
        return [f"local model_path must be a directory: {model_path}"], warnings
    if not (path / "config.yaml").is_file():
        errors.append("local model_path is missing config.yaml")
    ckpts = list(path.rglob("*.ckpt"))
    if not ckpts:
        errors.append("local model_path contains no .ckpt file")
    elif all(_looks_like_lfs_pointer(item) for item in ckpts):
        errors.append("local checkpoint files are Git-LFS pointers, not hydrated weights")
    elif any(_looks_like_lfs_pointer(item) for item in ckpts):
        warnings.append("some local .ckpt files are Git-LFS pointers and cannot be loaded")
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MatterGen generation inputs. This is a dry-run unless "
            "--run is explicitly supplied."
        )
    )
    checkpoint = parser.add_mutually_exclusive_group()
    checkpoint.add_argument(
        "--pretrained-name", choices=sorted(MODEL_NAMES), help="named Hub checkpoint"
    )
    checkpoint.add_argument("--model-path", help="local checkpoint/config directory")
    parser.add_argument("--output-dir", default="outputs", help="directory for generation artifacts")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-batches", type=int, default=1)
    parser.add_argument(
        "--properties-to-condition-on",
        help="JSON/Python mapping, e.g. '{\"dft_mag_density\":0.15}'",
    )
    parser.add_argument(
        "--target-composition",
        "--target-compositions",
        dest="target_compositions",
        action="append",
        help="one composition mapping, or a list of mappings; repeatable",
    )
    parser.add_argument("--diffusion-guidance-factor", type=float, default=0.0)
    parser.add_argument("--num-atoms-distribution", default="ALEX_MP_20")
    parser.add_argument("--sampling-config-path")
    parser.add_argument("--sampling-config-name", default="default")
    parser.add_argument(
        "--sampling-config-override", dest="sampling_config_overrides", action="append", default=[]
    )
    parser.add_argument(
        "--config-override", dest="config_overrides", action="append", default=[]
    )
    parser.add_argument("--checkpoint-epoch", default="last")
    parser.add_argument(
        "--record-trajectories",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="retain denoising trajectories (default: true)",
    )
    parser.add_argument(
        "--strict-checkpoint-loading",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="after validation, invoke the installed public MatterGen API",
    )
    return parser


def validate_args(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if args.pretrained_name is None and args.model_path is None:
        errors.append("provide exactly one of --pretrained-name or --model-path")
    if args.batch_size <= 0:
        errors.append("--batch-size must be a positive integer")
    if args.num_batches <= 0:
        errors.append("--num-batches must be a positive integer")
    if args.diffusion_guidance_factor < 0:
        errors.append("--diffusion-guidance-factor must be nonnegative")
    if args.num_atoms_distribution not in NUM_ATOMS_DISTRIBUTIONS:
        errors.append(
            f"unknown --num-atoms-distribution {args.num_atoms_distribution!r}; "
            f"available choices: {sorted(NUM_ATOMS_DISTRIBUTIONS)}"
        )
    if not str(args.output_dir).strip():
        errors.append("--output-dir cannot be empty")

    try:
        epoch = parse_epoch(str(args.checkpoint_epoch))
    except ValueError as exc:
        errors.append(str(exc))
        epoch = "last"

    properties: dict[str, Any] = {}
    if args.properties_to_condition_on is not None:
        try:
            properties = parse_mapping(
                args.properties_to_condition_on, "properties_to_condition_on"
            )
        except ValueError as exc:
            errors.append(str(exc))
        for key in properties:
            if key not in KNOWN_PROPERTIES:
                warnings.append(
                    f"property {key!r} is not in the shipped property registry; "
                    "continue only if a custom fine-tuned checkpoint supports it"
                )

    try:
        compositions = parse_compositions(args.target_compositions)
    except ValueError as exc:
        errors.append(str(exc))
        compositions = []

    if compositions and args.sampling_config_name != "csp":
        errors.append(
            "target compositions are only accepted with --sampling-config-name=csp"
        )
    if args.sampling_config_name == "csp" and not compositions:
        errors.append("CSP sampling requires at least one --target-composition mapping")
    if compositions and properties:
        errors.append(
            "target compositions and properties_to_condition_on are separate routes; "
            "do not combine them in one request"
        )
    if compositions:
        for composition in compositions:
            total = sum(composition.values())
            if total > 20:
                warnings.append(
                    f"composition total {total} exceeds the released models' 20-atom regime"
                )

    if args.model_path:
        local_errors, local_warnings = inspect_local_checkpoint(args.model_path)
        errors.extend(local_errors)
        warnings.extend(local_warnings)

    if args.sampling_config_path is not None:
        path = Path(args.sampling_config_path).expanduser()
        if not path.is_dir():
            errors.append("--sampling-config-path must name an existing directory")
        elif not (path / f"{args.sampling_config_name}.yaml").is_file():
            errors.append(
                f"sampling config {args.sampling_config_name!r} was not found under the supplied directory"
            )

    if args.diffusion_guidance_factor == 0:
        guidance_note = "0.0 (unconditional score; conditions, if supplied, are not guided)"
    elif args.diffusion_guidance_factor == 1:
        guidance_note = "1.0 (conditional score)"
    else:
        guidance_note = f"{args.diffusion_guidance_factor} (guided conditional score)"

    normalized = {
        "checkpoint": {
            "pretrained_name": args.pretrained_name,
            "model_path": str(Path(args.model_path).expanduser()) if args.model_path else None,
            "checkpoint_epoch": epoch,
            "strict_checkpoint_loading": args.strict_checkpoint_loading,
        },
        "sampling": {
            "batch_size": args.batch_size,
            "num_batches": args.num_batches,
            "requested_samples": args.batch_size * args.num_batches,
            "num_atoms_distribution": args.num_atoms_distribution,
            "sampling_config_path": args.sampling_config_path,
            "sampling_config_name": args.sampling_config_name,
            "sampling_config_overrides": args.sampling_config_overrides,
            "guidance_factor": args.diffusion_guidance_factor,
            "guidance_interpretation": guidance_note,
            "record_trajectories": args.record_trajectories,
        },
        "conditioning": {
            "properties_to_condition_on": properties,
            "target_compositions_dict": compositions,
        },
        "output_dir": args.output_dir,
        "run_requested": bool(args.run),
    }
    normalized["warnings"] = warnings
    return normalized, errors


def run_public_api(args: argparse.Namespace, normalized: dict[str, Any]) -> int:
    """Run only after --run, using public MatterGen classes."""
    # Imports are intentionally inside this function: --help and dry validation
    # must work even when optional generation dependencies are not installed.
    from mattergen.common.utils.data_classes import MatterGenCheckpointInfo
    from mattergen.generator import CrystalGenerator

    config_overrides = list(args.config_overrides)
    if ELEMENT_MASK_OVERRIDE not in config_overrides:
        config_overrides.append(ELEMENT_MASK_OVERRIDE)

    if args.pretrained_name:
        checkpoint = MatterGenCheckpointInfo.from_hf_hub(
            args.pretrained_name, config_overrides=config_overrides
        )
    else:
        checkpoint = MatterGenCheckpointInfo(
            model_path=str(Path(args.model_path).expanduser()),
            load_epoch=parse_epoch(str(args.checkpoint_epoch)),
            config_overrides=config_overrides,
            strict_checkpoint_loading=args.strict_checkpoint_loading,
        )

    sampling_path = (
        Path(args.sampling_config_path).expanduser()
        if args.sampling_config_path
        else None
    )
    generator = CrystalGenerator(
        checkpoint_info=checkpoint,
        batch_size=args.batch_size,
        num_batches=args.num_batches,
        target_compositions_dict=normalized["conditioning"]["target_compositions_dict"] or None,
        num_atoms_distribution=args.num_atoms_distribution,
        diffusion_guidance_factor=args.diffusion_guidance_factor,
        properties_to_condition_on=normalized["conditioning"]["properties_to_condition_on"] or {},
        sampling_config_overrides=list(args.sampling_config_overrides),
        sampling_config_path=sampling_path,
        sampling_config_name=args.sampling_config_name,
        record_trajectories=args.record_trajectories,
    )
    structures = generator.generate(output_dir=args.output_dir)
    print(json.dumps({"generated_structures": len(structures), "output_dir": args.output_dir}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    normalized, errors = validate_args(args)
    if errors:
        print(json.dumps({"valid": False, "errors": errors, "request": normalized}, indent=2))
        return 2
    print(json.dumps({"valid": True, "request": normalized}, indent=2, sort_keys=True))
    if not args.run:
        print("Dry validation only; add --run to invoke the installed MatterGen API.")
        return 0
    try:
        return run_public_api(args, normalized)
    except Exception as exc:
        print(
            f"Generation failed after explicit --run ({type(exc).__name__}): {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
