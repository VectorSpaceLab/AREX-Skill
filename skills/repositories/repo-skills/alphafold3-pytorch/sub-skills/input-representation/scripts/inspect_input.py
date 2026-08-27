#!/usr/bin/env python3
"""Safely inspect a small AlphaFold 3 input JSON specification.

This tool constructs input dataclasses and tensor features only.  It never
loads a checkpoint, runs a model, downloads data, starts a server, or writes a
persistent output file.  ``--roundtrip`` uses a temporary directory.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

MAX_SPEC_BYTES = 256 * 1024
MAX_SAMPLES = 8
MAX_ENTITY_LENGTH = 4096

SAMPLE_FIELDS = {
    "proteins",
    "ss_dna",
    "ss_rna",
    "metal_ions",
    "misc_molecule_ids",
    "ligands",
    "ds_dna",
    "ds_rna",
    "atom_parent_ids",
    "missing_atom_indices",
    "additional_msa_feats",
    "additional_token_feats",
    "templates",
    "msa",
    "atom_pos",
    "template_mask",
    "msa_mask",
    "distance_labels",
    "resolved_labels",
    "token_constraints",
    "chains",
    "add_atom_ids",
    "add_atompair_ids",
    "directed_bonds",
    "custom_atoms",
    "custom_bonds",
}

TENSOR_FIELDS = {
    "atom_parent_ids": "long",
    "additional_msa_feats": "float",
    "additional_token_feats": "float",
    "templates": "float",
    "msa": "float",
    "template_mask": "bool",
    "msa_mask": "bool",
    "distance_labels": "long",
    "resolved_labels": "long",
    "token_constraints": "float",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct and inspect small AlphaFold 3 inputs from JSON without "
            "model inference, downloads, training, or server launch."
        ),
        epilog=(
            "SPEC may be a JSON object, a JSON list for an unequal batch, or "
            "@FILE/- for a JSON file/stdin. A wrapper object may contain "
            "inputs and atoms_per_window."
        ),
    )
    parser.add_argument(
        "spec",
        nargs="?",
        help='JSON object/list, @FILE, or - for stdin (example: \'{"proteins":["AG"]}\')',
    )
    parser.add_argument("--spec-file", type=Path, help="Read the JSON specification from a file.")
    parser.add_argument(
        "--atoms-per-window",
        type=int,
        help="Window full atom-pair features with this positive window size.",
    )
    parser.add_argument(
        "--roundtrip",
        action="store_true",
        help="Save/reload each AtomInput in a temporary directory and compare tensor fields.",
    )
    parser.add_argument(
        "--validate-output-shape",
        metavar="N,47,3",
        help="Validate standalone Biomolecule conversion with zero coordinates of this shape.",
    )
    return parser


def _read_spec(args: argparse.Namespace) -> tuple[Any, int | None]:
    if args.spec_file is not None and args.spec is not None:
        raise ValueError("provide either SPEC or --spec-file, not both")

    if args.spec_file is not None:
        raw_bytes = args.spec_file.read_bytes()
        source = raw_bytes.decode("utf-8")
    elif args.spec is None:
        raise ValueError("a JSON SPEC or --spec-file is required")
    elif args.spec == "-":
        source = sys.stdin.read()
    elif args.spec.startswith("@"):
        source = Path(args.spec[1:]).read_text(encoding="utf-8")
    else:
        source = args.spec

    if len(source.encode("utf-8")) > MAX_SPEC_BYTES:
        raise ValueError(f"JSON specification exceeds the {MAX_SPEC_BYTES} byte safety limit")

    parsed = json.loads(source)
    wrapper_window = None
    if isinstance(parsed, dict) and "inputs" in parsed:
        unknown_wrapper = set(parsed) - {"inputs", "atoms_per_window"}
        if unknown_wrapper:
            raise ValueError(f"unknown wrapper keys: {sorted(unknown_wrapper)}")
        entries = parsed["inputs"]
        wrapper_window = parsed.get("atoms_per_window")
    elif isinstance(parsed, list):
        entries = parsed
    else:
        entries = [parsed]

    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise ValueError("the specification must contain a JSON object or a list of JSON objects")
    if not entries:
        raise ValueError("the specification contains no input objects")
    if len(entries) > MAX_SAMPLES:
        raise ValueError(f"at most {MAX_SAMPLES} input objects are accepted by this bounded helper")

    window = args.atoms_per_window if args.atoms_per_window is not None else wrapper_window
    if window is not None and (not isinstance(window, int) or isinstance(window, bool) or window <= 0):
        raise ValueError("atoms_per_window must be a positive integer")
    return entries, window


@contextlib.contextmanager
def _suppress_native_output():
    """Suppress native-library import diagnostics without hiding our JSON result."""
    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    try:
        sys.stdout.flush()
        sys.stderr.flush()
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
            yield
    finally:
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)


def _json_tensor(value: Any, kind: str):
    import torch

    dtype = {
        "long": torch.long,
        "float": torch.float32,
        "bool": torch.bool,
    }[kind]
    return torch.tensor(value, dtype=dtype)


def _coerce_atom_pos(value: Any):
    import torch

    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("atom_pos must be a JSON list")
    if not value:
        return torch.empty((0, 3), dtype=torch.float32)
    first = value[0]
    if isinstance(first, list) and (not first or isinstance(first[0], (int, float))):
        return torch.tensor(value, dtype=torch.float32)
    if isinstance(first, list):
        return [torch.tensor(part, dtype=torch.float32) for part in value]
    raise ValueError("atom_pos must be [atoms,3] or a list of [atoms,3] arrays")


def _coerce_sample(sample: dict[str, Any]) -> dict[str, Any]:
    unknown = set(sample) - SAMPLE_FIELDS
    if unknown:
        raise ValueError(f"unknown input keys: {sorted(unknown)}")
    out = dict(sample)
    if "atom_pos" in out:
        out["atom_pos"] = _coerce_atom_pos(out["atom_pos"])
    for key, kind in TENSOR_FIELDS.items():
        if key in out and out[key] is not None:
            out[key] = _json_tensor(out[key], kind)
    if "chains" in out and out["chains"] is not None:
        if not isinstance(out["chains"], (list, tuple)) or len(out["chains"]) != 2:
            raise ValueError("chains must be a two-item JSON list")
        out["chains"] = tuple(out["chains"])
    for key in ("proteins", "ss_dna", "ss_rna", "ds_dna", "ds_rna", "ligands", "metal_ions"):
        values = out.get(key, [])
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a JSON list")
        for value in values:
            if isinstance(value, str) and len(value) > MAX_ENTITY_LENGTH:
                raise ValueError(f"{key} contains an entity over the safety length limit")
    return out


def _shape(value: Any) -> list[int] | None:
    return list(value.shape) if value is not None and hasattr(value, "shape") else None


def _integer_info(value: Any) -> dict[str, Any] | None:
    import torch

    if value is None or not torch.is_tensor(value):
        return None
    result = {"shape": _shape(value), "dtype": str(value.dtype)}
    if value.numel() and (value.dtype == torch.bool or not value.dtype.is_floating_point):
        result["min"] = int(value.min().item())
        result["max"] = int(value.max().item())
    return result


def _ascending(value: Any) -> bool | None:
    import torch

    if value is None or not torch.is_tensor(value):
        return None
    x = value
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2:
        return None
    present = (x >= 0).all(dim=-1)
    x = x[present]
    if x.shape[0] <= 1:
        return True
    pairwise_difference = x[1:, :, None] - x[:-1, None, :]
    return bool((pairwise_difference >= 0).all().item())


def _index_range_ok(value: Any, atom_count: int) -> bool | None:
    import torch

    if value is None or not torch.is_tensor(value):
        return None
    if not bool((value >= -1).all().item()):
        return False
    present = value[value >= 0]
    return bool((present < atom_count).all().item()) if present.numel() else True


def _atom_summary(atom_input: Any) -> dict[str, Any]:
    import torch

    m = int(atom_input.atom_inputs.shape[0])
    n = int(atom_input.molecule_ids.shape[0])
    type_counts = [int(v) for v in atom_input.is_molecule_types.sum(dim=0).tolist()]
    pair_ids = atom_input.atompair_ids
    pair_id_values = sorted(int(v) for v in torch.unique(pair_ids).tolist()) if pair_ids is not None else None
    summary: dict[str, Any] = {
        "atoms": m,
        "tokens": n,
        "atom_inputs": {"shape": _shape(atom_input.atom_inputs), "dtype": str(atom_input.atom_inputs.dtype)},
        "atompair_inputs": {"shape": _shape(atom_input.atompair_inputs), "dtype": str(atom_input.atompair_inputs.dtype)},
        "molecule_type_token_counts": {
            key: type_counts[index]
            for index, key in enumerate(("protein", "rna", "dna", "ligand", "metal_ion"))
        },
        "molecule_atom_lens": [int(v) for v in atom_input.molecule_atom_lens.tolist()],
        "additional_molecule_feats_shape": _shape(atom_input.additional_molecule_feats),
        "token_bonds": int(atom_input.token_bonds.sum().item()),
        "missing_atoms": int(atom_input.missing_atom_mask.sum().item()) if atom_input.missing_atom_mask is not None else 0,
        "optional_fields": sorted(
            key for key, value in atom_input.dict().items() if value is not None
        ),
        "atom_ids": _integer_info(atom_input.atom_ids),
        "atompair_ids": {
            "shape": _shape(pair_ids),
            "dtype": str(pair_ids.dtype),
            "unique": pair_id_values,
        } if pair_ids is not None else None,
        "index_checks": {
            key: {
                "ascending": _ascending(getattr(atom_input, key)),
                "in_atom_range": _index_range_ok(getattr(atom_input, key), m),
            }
            for key in ("molecule_atom_indices", "distogram_atom_indices", "atom_indices_for_frame")
        },
    }
    if atom_input.atom_pos is not None:
        summary["atom_pos_shape"] = _shape(atom_input.atom_pos)
    return summary


def _same_value(left: Any, right: Any) -> bool:
    import torch

    if torch.is_tensor(left) or torch.is_tensor(right):
        return torch.is_tensor(left) and torch.is_tensor(right) and torch.equal(left, right)
    return left == right


def _roundtrip(atom_inputs: list[Any], atom_input_to_file: Any, file_to_atom_input: Any) -> None:
    with tempfile.TemporaryDirectory(prefix="af3-input-inspection-") as folder:
        for index, atom_input in enumerate(atom_inputs):
            restored = file_to_atom_input(atom_input_to_file(atom_input, Path(folder) / f"{index}.pt"))
            for key, value in atom_input.dict().items():
                if not _same_value(value, getattr(restored, key)):
                    raise ValueError(f"serialization mismatch in sample {index}, field {key}")


def _output_summary(af3_input: Any, shape_text: str, converter: Any) -> dict[str, Any]:
    import numpy as np

    try:
        shape = tuple(int(part.strip()) for part in shape_text.split(","))
    except ValueError as exc:
        raise ValueError("--validate-output-shape must look like N,47,3") from exc
    if shape[-2:] != (47, 3) or len(shape) != 3 or shape[0] <= 0:
        raise ValueError("--validate-output-shape must be a positive three-dimensional N,47,3 shape")
    biomol = converter(af3_input, np.zeros(shape, dtype=np.float32))
    return {
        "coordinate_shape": list(shape),
        "atom_positions_shape": list(biomol.atom_positions.shape),
        "atom_mask_shape": list(biomol.atom_mask.shape),
        "tokens": int(len(biomol.restype)),
        "chemical_type_counts": {
            str(int(value)): int((biomol.chemtype == value).sum())
            for value in sorted(set(int(v) for v in biomol.chemtype.tolist()))
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        entries, wrapper_window = _read_spec(args)
        samples = [_coerce_sample(entry) for entry in entries]
    except Exception as exc:
        print(json.dumps({"error": "invalid_spec", "detail": str(exc)}, sort_keys=True))
        return 2

    # Keep optional dependency import noise out of the deterministic JSON result.
    captured = io.StringIO()
    try:
        with _suppress_native_output(), contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            import torch
            from alphafold3_pytorch import (
                Alphafold3Input,
                alphafold3_input_to_biomolecule,
                alphafold3_inputs_to_batched_atom_input,
                atom_input_to_file,
                file_to_atom_input,
                maybe_transform_to_atom_input,
            )
    except Exception as exc:
        print(json.dumps({"error": "package_import_failed", "detail": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 3

    try:
        af3_inputs = [Alphafold3Input(**sample) for sample in samples]
        atom_inputs = [maybe_transform_to_atom_input(item, raise_exception=True) for item in af3_inputs]
        assert all(item is not None for item in atom_inputs)
        collate_kwargs = {}
        if wrapper_window is not None:
            collate_kwargs["atoms_per_window"] = wrapper_window
        batch = alphafold3_inputs_to_batched_atom_input(af3_inputs, **collate_kwargs)

        result: dict[str, Any] = {
            "status": "ok",
            "samples": [_atom_summary(item) for item in atom_inputs],
            "batch": {
                "atom_inputs_shape": _shape(batch.atom_inputs),
                "atompair_inputs_shape": _shape(batch.atompair_inputs),
                "molecule_ids_shape": _shape(batch.molecule_ids),
                "molecule_atom_lens_shape": _shape(batch.molecule_atom_lens),
                "missing_atom_mask_shape": _shape(batch.missing_atom_mask),
                "padded_token_count": int((batch.molecule_atom_lens == 0).sum().item()),
                "padded_atom_count": sum(
                    int(batch.atom_inputs.shape[1] - item.atom_inputs.shape[0]) for item in atom_inputs
                ),
                "masked_atom_count": int(batch.missing_atom_mask.sum().item()) if batch.missing_atom_mask is not None else 0,
            },
        }
        if "misc_molecule_ids" in samples[0] or any("misc_molecule_ids" in sample for sample in samples):
            result["warning"] = "misc_molecule_ids is accepted by the dataclass but not consumed by the current direct converter"
        if args.roundtrip:
            _roundtrip(atom_inputs, atom_input_to_file, file_to_atom_input)
            result["serialization_roundtrip"] = "ok"
        if args.validate_output_shape:
            if len(af3_inputs) != 1:
                raise ValueError("--validate-output-shape requires exactly one input object")
            result["biomolecule"] = _output_summary(
                af3_inputs[0], args.validate_output_shape, alphafold3_input_to_biomolecule
            )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"error": "input_validation_failed", "detail": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
