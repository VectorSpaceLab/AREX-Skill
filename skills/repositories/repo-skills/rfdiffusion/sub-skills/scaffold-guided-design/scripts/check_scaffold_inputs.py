#!/usr/bin/env python3
"""Validate RFdiffusion scaffold-guided input files before inference.

The checker is intentionally safe: it never runs RFdiffusion, never imports
PyRosetta, and only inspects paths, names, simple option compatibility, and
PyTorch tensor shapes when torch is available.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

HOTSPOT_RE = re.compile(r"^[A-Za-z][0-9]+[A-Za-z]?$")
RANGE_RE = re.compile(r"^(\d+)(?:-(\d+))?$")


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def parse_range(value: str, label: str) -> tuple[int, int]:
    match = RANGE_RE.match(str(value))
    if not match:
        raise ValueError(f"{label} must be a non-negative integer or MIN-MAX range, got {value!r}")
    start = int(match.group(1))
    end = int(match.group(2) or start)
    if end < start:
        raise ValueError(f"{label} range end must be >= start, got {value!r}")
    return start, end


def load_ids_from_scaffold_list(path_or_items: str | None) -> list[str] | None:
    if not path_or_items:
        return None
    candidate = Path(path_or_items)
    if candidate.exists():
        return [line.strip() for line in candidate.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return [item.strip() for item in path_or_items.split(",") if item.strip()]


def scaffold_ids(scaffold_dir: Path) -> tuple[set[str], set[str]]:
    ss_ids = {path.name[: -len("_ss.pt")] for path in scaffold_dir.glob("*_ss.pt")}
    adj_ids = {path.name[: -len("_adj.pt")] for path in scaffold_dir.glob("*_adj.pt")}
    return ss_ids, adj_ids


def try_import_torch():
    try:
        import torch  # type: ignore
    except Exception:
        return None
    return torch


def tensor_shape(torch_module, path: Path):
    tensor = torch_module.load(path, map_location="cpu")
    shape = tuple(tensor.shape) if hasattr(tensor, "shape") else None
    return tensor, shape


def validate_pair_shapes(torch_module, scaffold_dir: Path, ids: Iterable[str], errors: list[str], warnings: list[str]) -> None:
    if torch_module is None:
        warnings.append("PyTorch is not importable; skipped tensor shape/value checks.")
        return
    for scaffold_id in ids:
        ss_path = scaffold_dir / f"{scaffold_id}_ss.pt"
        adj_path = scaffold_dir / f"{scaffold_id}_adj.pt"
        try:
            ss_tensor, ss_shape = tensor_shape(torch_module, ss_path)
            adj_tensor, adj_shape = tensor_shape(torch_module, adj_path)
        except Exception as exc:
            errors.append(f"failed to load tensors for {scaffold_id}: {exc}")
            continue
        if ss_shape is None or len(ss_shape) != 1:
            errors.append(f"{ss_path} should be a 1D tensor, got shape {ss_shape}")
            continue
        if adj_shape is None or len(adj_shape) != 2 or adj_shape[0] != adj_shape[1]:
            errors.append(f"{adj_path} should be a square 2D tensor, got shape {adj_shape}")
            continue
        if ss_shape[0] != adj_shape[0]:
            errors.append(f"{scaffold_id} length mismatch: ss length {ss_shape[0]} vs adj shape {adj_shape}")
        check_values(torch_module, ss_tensor, {0, 1, 2, 3}, ss_path, warnings)
        check_values(torch_module, adj_tensor, {0, 1, 2}, adj_path, warnings)


def check_values(torch_module, tensor, allowed: set[int], path: Path, warnings: list[str]) -> None:
    try:
        unique_values = {int(value) for value in torch_module.unique(tensor).tolist()}
    except Exception as exc:
        warnings.append(f"could not inspect values for {path}: {exc}")
        return
    unexpected = sorted(unique_values - allowed)
    if unexpected:
        warnings.append(f"{path} contains values outside expected classes {sorted(allowed)}: {unexpected}")


def validate_target_tensors(torch_module, target_ss: Path | None, target_adj: Path | None, errors: list[str], warnings: list[str]) -> None:
    if target_ss is None and target_adj is None:
        return
    if target_ss is None or target_adj is None:
        errors.append("provide both --target-ss and --target-adj, or neither")
        return
    if not target_ss.exists():
        errors.append(f"target secondary-structure tensor does not exist: {target_ss}")
    if not target_adj.exists():
        errors.append(f"target adjacency tensor does not exist: {target_adj}")
    if errors or torch_module is None:
        if torch_module is None:
            warnings.append("PyTorch is not importable; skipped target tensor shape/value checks.")
        return
    try:
        ss_tensor, ss_shape = tensor_shape(torch_module, target_ss)
        adj_tensor, adj_shape = tensor_shape(torch_module, target_adj)
    except Exception as exc:
        errors.append(f"failed to load target tensors: {exc}")
        return
    if ss_shape is None or len(ss_shape) != 1:
        errors.append(f"{target_ss} should be a 1D tensor, got shape {ss_shape}")
    if adj_shape is None or len(adj_shape) != 2 or adj_shape[0] != adj_shape[1]:
        errors.append(f"{target_adj} should be a square 2D tensor, got shape {adj_shape}")
    if ss_shape and adj_shape and len(ss_shape) == 1 and len(adj_shape) == 2 and ss_shape[0] != adj_shape[0]:
        errors.append(f"target tensor length mismatch: ss length {ss_shape[0]} vs adj shape {adj_shape}")
    check_values(torch_module, ss_tensor, {0, 1, 2, 3}, target_ss, warnings)
    check_values(torch_module, adj_tensor, {0, 1, 2}, target_adj, warnings)


def normalize_list_id(item: str) -> str:
    name = Path(item).name
    if name.endswith("_ss.pt"):
        return name[: -len("_ss.pt")]
    if name.endswith("_adj.pt"):
        return name[: -len("_adj.pt")]
    if name.endswith(".pt"):
        return name[:-3]
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate RFdiffusion scaffold-guided inputs without running inference.")
    parser.add_argument("--scaffold-dir", help="Directory containing paired ID_ss.pt and ID_adj.pt files.")
    parser.add_argument("--scaffold-list", help="Text file or comma-separated IDs restricting scaffold_dir.")
    parser.add_argument("--target-pdb", help="Target PDB path when scaffoldguided.target_pdb=True.")
    parser.add_argument("--target-ss", type=Path, help="Target secondary-structure tensor path.")
    parser.add_argument("--target-adj", type=Path, help="Target block-adjacency tensor path.")
    parser.add_argument("--hotspots", help="Comma-separated chain-qualified hotspot residues, such as A59,A83,A91.")
    parser.add_argument("--mask-loops", type=parse_bool, default=True, help="Whether scaffoldguided.mask_loops is true.")
    parser.add_argument("--sampled-insertion", default="0", help="sampled_insertion value: N or MIN-MAX.")
    parser.add_argument("--sampled-n", default="0", help="sampled_N value: N or MIN-MAX.")
    parser.add_argument("--sampled-c", default="0", help="sampled_C value: N or MIN-MAX.")
    parser.add_argument("--per-residue-ss", action="store_true", help="Set when using contigmap.inpaint_str_helix/strand/loop instead of scaffold_dir.")
    parser.add_argument("--target-pdb-mode", type=parse_bool, default=None, help="Value intended for scaffoldguided.target_pdb.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    try:
        sampled_insertion = parse_range(args.sampled_insertion, "sampled_insertion")
        sampled_n = parse_range(args.sampled_n, "sampled_N")
        sampled_c = parse_range(args.sampled_c, "sampled_C")
    except ValueError as exc:
        errors.append(str(exc))
        sampled_insertion = sampled_n = sampled_c = (0, 0)

    if not args.mask_loops and any(value[1] > 0 for value in (sampled_insertion, sampled_n, sampled_c)):
        errors.append("mask_loops=False cannot be combined with sampled_insertion, sampled_N, or sampled_C above zero")

    scaffold_dir = Path(args.scaffold_dir) if args.scaffold_dir else None
    if scaffold_dir and args.per_residue_ss:
        errors.append("scaffold_dir is mutually exclusive with per-residue secondary-structure masks")
    if not scaffold_dir and not args.per_residue_ss:
        errors.append("provide --scaffold-dir or --per-residue-ss")

    ids_to_check: list[str] = []
    if scaffold_dir:
        if not scaffold_dir.is_dir():
            errors.append(f"scaffold directory does not exist: {scaffold_dir}")
        else:
            ss_ids, adj_ids = scaffold_ids(scaffold_dir)
            missing_adj = sorted(ss_ids - adj_ids)
            missing_ss = sorted(adj_ids - ss_ids)
            if missing_adj:
                errors.append(f"missing adjacency files for scaffold IDs: {', '.join(missing_adj)}")
            if missing_ss:
                errors.append(f"missing secondary-structure files for scaffold IDs: {', '.join(missing_ss)}")
            paired_ids = sorted(ss_ids & adj_ids)
            if not paired_ids:
                errors.append(f"no paired *_ss.pt/*_adj.pt files found in {scaffold_dir}")
            listed = load_ids_from_scaffold_list(args.scaffold_list)
            if listed is not None:
                normalized = [normalize_list_id(item) for item in listed]
                missing = sorted(set(normalized) - set(paired_ids))
                if missing:
                    errors.append(f"scaffold_list entries without paired tensors: {', '.join(missing)}")
                ids_to_check = [item for item in normalized if item in paired_ids]
                if len(ids_to_check) != len(normalized):
                    warnings.append("only valid scaffold_list entries will be shape-checked")
            else:
                ids_to_check = paired_ids

    if args.target_pdb_mode is True and not args.target_pdb:
        errors.append("target_pdb mode requires --target-pdb")
    if args.target_pdb and not Path(args.target_pdb).exists():
        errors.append(f"target PDB does not exist: {args.target_pdb}")

    if args.hotspots:
        for hotspot in [item.strip() for item in args.hotspots.split(",") if item.strip()]:
            if not HOTSPOT_RE.match(hotspot):
                errors.append(f"hotspot {hotspot!r} should look like A59 or B165")
    elif args.target_pdb_mode is True:
        warnings.append("target_pdb mode was requested without hotspots; binder routing may be weak unless intentionally hotspot-free")

    torch_module = try_import_torch()
    if scaffold_dir and scaffold_dir.is_dir() and ids_to_check:
        validate_pair_shapes(torch_module, scaffold_dir, ids_to_check, errors, warnings)
    validate_target_tensors(torch_module, args.target_ss, args.target_adj, errors, warnings)

    if warnings:
        print("Warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)
    if errors:
        print("Errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    checked = len(ids_to_check)
    print(f"OK: scaffold-guided inputs passed preflight checks ({checked} scaffold pair(s) checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
