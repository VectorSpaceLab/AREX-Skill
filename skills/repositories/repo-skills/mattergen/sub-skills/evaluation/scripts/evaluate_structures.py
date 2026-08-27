#!/usr/bin/env python3
"""Validate inputs and run MatterGen's evaluation API on explicit request.

This adapter deliberately does not download reference datasets or MatterSim
checkpoints. Relaxation requires an explicit local potential checkpoint.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence


_BOOL_VALUES = {
    "true": True,
    "false": False,
    "1": True,
    "0": False,
    "yes": True,
    "no": False,
}
_DEVICE_RE = re.compile(r"^(?:cpu|mps|cuda(?::[0-9]+)?)$")
_STRUCTURE_SUFFIXES = {".xyz", ".extxyz", ".zip"}
_DIRECTORY_SUFFIXES = {".cif", ".xyz", ".extxyz"}


def parse_bool(value: str) -> bool:
    """Parse the explicit boolean spellings used by the original Fire CLI."""
    try:
        return _BOOL_VALUES[value.strip().lower()]
    except KeyError as exc:
        raise argparse.ArgumentTypeError(
            f"expected True/False (or yes/no, 1/0), got {value!r}"
        ) from exc


def existing_file(value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError(f"{label} must be an existing file: {path}")
    return path


def validate_structure_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise ValueError(f"structures_path does not exist: {path}")
    if path.is_dir():
        return path
    if path.suffix not in _STRUCTURE_SUFFIXES:
        raise ValueError(
            "structures_path must be a directory or a file ending in .xyz, "
            ".extxyz, or .zip; suffixes are case-sensitive"
        )
    return path


def validate_device(device: str) -> str:
    if device == "auto" or _DEVICE_RE.fullmatch(device):
        return device
    raise argparse.ArgumentTypeError("device must be auto, cpu, mps, cuda, or cuda:N")


def validate_output_parent(value: str | None, label: str) -> None:
    if value is None:
        return
    path = Path(value).expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"cannot create parent for {label} {path}: {exc}") from exc


def validate_args(args: argparse.Namespace) -> tuple[Path, Path | None, Path | None]:
    structures_path = validate_structure_path(args.structures_path)
    energies_path = None
    reference_path = None

    if args.energies_path is not None:
        energies_path = existing_file(args.energies_path, "energies_path")
    if args.reference_dataset_path is not None:
        reference_path = existing_file(
            args.reference_dataset_path, "reference_dataset_path"
        )
        if reference_path.suffix != ".gz":
            raise ValueError(
                "reference_dataset_path must be a gzip-compressed LMDB file ending in .gz"
            )

    if args.relax:
        if energies_path is not None:
            raise ValueError(
                "relax=True cannot be combined with --energies_path; choose relaxed "
                "MatterSim energies or precomputed energies with --relax False"
            )
        if args.structures_output_path is not None:
            validate_output_parent(args.structures_output_path, "structures_output_path")
        # MatterSim may resolve/download a default model when no checkpoint is
        # supplied. Requiring a local file keeps this adapter offline and auditable.
        if args.potential_load_path is None:
            raise ValueError(
                "relax=True requires --potential_load_path pointing to an existing "
                "local MatterSim checkpoint; this adapter never downloads model assets"
            )
        existing_file(args.potential_load_path, "potential_load_path")
    else:
        if energies_path is None:
            raise ValueError(
                "relax=False requires --energies_path with one total energy per structure"
            )
        if args.potential_load_path is not None:
            raise ValueError(
                "--potential_load_path is only valid with relax=True; it is not used "
                "when energies are precomputed"
            )
        if args.structures_output_path is not None:
            raise ValueError(
                "--structures_output_path is only valid with relax=True"
            )

    for value, label in (
        (args.save_as, "save_as"),
        (args.save_detailed_as, "save_detailed_as"),
    ):
        validate_output_parent(value, label)

    return structures_path, energies_path, reference_path


def load_and_validate_energies(path: Path, structure_count: int):
    """Load a positional total-energy vector and enforce its contract."""
    import numpy as np

    try:
        raw = np.load(path, allow_pickle=False)
        energies = np.asarray(raw, dtype=float)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"could not load numeric energies from {path}: {exc}") from exc

    if energies.ndim != 1:
        raise ValueError(
            f"energies_path must contain a 1-D array of total energies; got shape {energies.shape}"
        )
    if len(energies) != structure_count:
        raise ValueError(
            "energy/structure count mismatch: "
            f"{len(energies)} energies for {structure_count} loaded structures. "
            "The array must use the loader's exact order."
        )
    if not np.all(np.isfinite(energies)):
        raise ValueError("energies_path contains NaN or infinite values")
    return energies


def resolve_device(requested: str) -> str:
    """Resolve and validate a backend only after the user explicitly runs us."""
    import torch

    if requested == "auto":
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    if requested.startswith("cuda"):
        if not torch.cuda.is_available():
            raise ValueError("CUDA was requested but torch.cuda.is_available() is False")
        if ":" in requested:
            index = int(requested.split(":", 1)[1])
            if index >= torch.cuda.device_count():
                raise ValueError(
                    f"{requested} was requested but only {torch.cuda.device_count()} CUDA device(s) are visible"
                )
    elif requested == "mps":
        if getattr(torch.backends, "mps", None) is None or not torch.backends.mps.is_available():
            raise ValueError("MPS was requested but torch.backends.mps.is_available() is False")
    return requested


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate inputs and evaluate MatterGen structures without implicit downloads."
    )
    parser.add_argument("--structures_path", required=True)
    parser.add_argument("--relax", type=parse_bool, default=True)
    parser.add_argument("--energies_path")
    parser.add_argument(
        "--structure_matcher", choices=("ordered", "disordered"), default="disordered"
    )
    parser.add_argument("--save_as")
    parser.add_argument("--save_detailed_as")
    parser.add_argument("--potential_load_path")
    parser.add_argument("--reference_dataset_path")
    parser.add_argument("--device", default="auto", type=validate_device)
    parser.add_argument("--structures_output_path")
    parser.add_argument(
        "--energy_correction_scheme", choices=("MP2020", "TRI2024"), default="MP2020"
    )
    return parser


def _json_default(value: Any) -> Any:
    # Numpy scalar values are normally converted by MatterGen, but keep the
    # explicit CLI robust across dependency patch versions.
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def run(args: argparse.Namespace) -> dict[str, Any]:
    structures_path, energies_path, reference_path = validate_args(args)

    # Heavy imports occur only after argparse and mode/path checks pass.
    from mattergen.common.utils.eval_utils import load_structures
    from mattergen.evaluation.evaluate import evaluate
    from mattergen.evaluation.reference.correction_schemes import TRI110Compatibility2024
    from mattergen.evaluation.reference.reference_dataset_serializer import LMDBGZSerializer
    from mattergen.evaluation.utils.structure_matcher import (
        DefaultDisorderedStructureMatcher,
        DefaultOrderedStructureMatcher,
    )
    from pymatgen.entries.compatibility import MaterialsProject2020Compatibility

    try:
        structures = list(load_structures(structures_path))
    except Exception as exc:
        raise ValueError(f"failed to load structures from {structures_path}: {exc}") from exc
    if not structures:
        raise ValueError(
            f"no supported structures were loaded from {structures_path}; "
            f"directory files must end in one of {sorted(_DIRECTORY_SUFFIXES)}"
        )

    energies = None
    if energies_path is not None:
        energies = load_and_validate_energies(energies_path, len(structures))

    reference = None
    if reference_path is not None:
        try:
            reference = LMDBGZSerializer().deserialize(str(reference_path))
        except Exception as exc:
            raise ValueError(
                f"failed to deserialize reference dataset {reference_path}: {exc}"
            ) from exc

    matcher = (
        DefaultDisorderedStructureMatcher()
        if args.structure_matcher == "disordered"
        else DefaultOrderedStructureMatcher()
    )
    correction = (
        MaterialsProject2020Compatibility()
        if args.energy_correction_scheme == "MP2020"
        else TRI110Compatibility2024()
    )
    device = resolve_device(args.device)

    try:
        return evaluate(
            structures=structures,
            relax=args.relax,
            energies=energies,
            reference=reference,
            structure_matcher=matcher,
            save_as=args.save_as,
            save_detailed_as=args.save_detailed_as,
            potential_load_path=args.potential_load_path,
            device=device,
            structures_output_path=args.structures_output_path,
            energy_correction_scheme=correction,
        )
    except Exception as exc:
        mode = "relaxation" if args.relax else "precomputed-energy evaluation"
        raise RuntimeError(f"MatterGen {mode} failed after preflight: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metrics = run(args)
    except (ValueError, RuntimeError) as exc:
        print(f"evaluation error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(metrics, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
