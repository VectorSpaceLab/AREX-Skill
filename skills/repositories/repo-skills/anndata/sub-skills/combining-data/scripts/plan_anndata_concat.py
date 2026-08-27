#!/usr/bin/env python3
"""Plan AnnData concat parameters from simple JSON batch metadata.

The helper is deterministic and does not import anndata. It reads metadata like:

{
  "axis": "obs",
  "prefer_outer": false,
  "memory_limit_cells": 10000000,
  "batches": [
    {"name": "a", "n_obs": 100, "var_names": ["g1", "g2"], "obs_names_unique": true,
     "obsp_keys": ["connectivities"], "uns_keys": ["neighbors"], "storage": "h5ad"},
    {"name": "b", "n_obs": 150, "var_names": ["g2", "g3"], "obs_names_unique": false,
     "obsp_keys": [], "uns_keys": ["neighbors"], "storage": "h5ad"}
  ]
}
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

SUPPORTED_AXIS = {"obs", "var", 0, 1, "0", "1"}
ON_DISK_STORAGES = {"h5ad", "zarr", "file", "path", "store", "backed"}
MEMORY_HEAVY_CELLS = 5_000_000


def normalize_axis(value: Any) -> str:
    if value not in SUPPORTED_AXIS:
        return "obs"
    return "var" if value in {"var", 1, "1"} else "obs"


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def load_payload(path: str | None) -> dict[str, Any]:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        data = json.load(sys.stdin)
    if isinstance(data, list):
        data = {"batches": data}
    if not isinstance(data, dict):
        raise SystemExit("Input JSON must be an object or a list of batch objects.")
    batches = data.get("batches") or data.get("adatas") or data.get("inputs")
    if not isinstance(batches, list) or not batches:
        raise SystemExit("Input JSON must include a non-empty 'batches' list.")
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            raise SystemExit(f"Batch {index} must be a JSON object.")
    data["batches"] = batches
    return data


def ordered_intersection(sequences: list[list[str]]) -> list[str]:
    if not sequences:
        return []
    common = set(sequences[0])
    for seq in sequences[1:]:
        common &= set(seq)
    return [item for item in sequences[0] if item in common]


def ordered_union(sequences: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for seq in sequences:
        for item in seq:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def unique_names(names: list[str]) -> list[str]:
    result: list[str] = []
    used: set[str] = set()
    for idx, name in enumerate(names):
        candidate = name or f"batch_{idx + 1}"
        if candidate in used:
            suffix = 2
            while f"{candidate}_{suffix}" in used:
                suffix += 1
            candidate = f"{candidate}_{suffix}"
        used.add(candidate)
        result.append(candidate)
    return result


def get_axis_names(batch: Mapping[str, Any], axis: str) -> list[str]:
    key = "obs_names" if axis == "obs" else "var_names"
    return as_list(batch.get(key))


def has_known_unique_names(batch: Mapping[str, Any], axis: str) -> bool | None:
    key = "obs_names_unique" if axis == "obs" else "var_names_unique"
    value = batch.get(key)
    if isinstance(value, bool):
        return value
    return None


def estimate_cells(batches: list[Mapping[str, Any]], axis: str, join_size: int) -> int | None:
    total_axis = 0
    for batch in batches:
        size = batch.get("n_obs" if axis == "obs" else "n_vars")
        if not isinstance(size, int):
            return None
        total_axis += size
    return total_axis * join_size if join_size else None


def choose_join(data: Mapping[str, Any], other_names: list[list[str]]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if data.get("join") in {"inner", "outer"}:
        return str(data["join"]), warnings
    if data.get("prefer_outer") is True or data.get("keep_union") is True:
        return "outer", warnings
    if any(not names for names in other_names):
        warnings.append("some batches omit names for the non-concatenated axis; defaulting to join='inner'")
        return "inner", warnings
    inner = ordered_intersection(other_names)
    union = ordered_union(other_names)
    if len(inner) == len(union):
        return "inner", warnings
    warnings.append(
        f"non-concatenated axis differs across batches: intersection={len(inner)}, union={len(union)}"
    )
    return "inner", warnings


def plan(data: Mapping[str, Any]) -> dict[str, Any]:
    batches: list[Mapping[str, Any]] = data["batches"]
    axis = normalize_axis(data.get("axis", "obs"))
    other_axis = "var" if axis == "obs" else "obs"
    names = unique_names([str(batch.get("name") or batch.get("key") or "") for batch in batches])

    other_names = [get_axis_names(batch, other_axis) for batch in batches]
    concat_names = [get_axis_names(batch, axis) for batch in batches]
    join, join_warnings = choose_join(data, other_names)
    joined_names = ordered_union(other_names) if join == "outer" else ordered_intersection(other_names)

    duplicate_risk = False
    for batch, batch_names in zip(batches, concat_names, strict=True):
        known_unique = has_known_unique_names(batch, axis)
        if known_unique is False:
            duplicate_risk = True
        if batch_names and len(batch_names) != len(set(batch_names)):
            duplicate_risk = True
    if concat_names and all(concat_names):
        all_concat_names = [item for seq in concat_names for item in seq]
        if any(count > 1 for count in Counter(all_concat_names).values()):
            duplicate_risk = True

    obsp_sets = [set(as_list(batch.get("obsp_keys"))) for batch in batches]
    varp_sets = [set(as_list(batch.get("varp_keys"))) for batch in batches]
    pairwise_sets = obsp_sets if axis == "obs" else varp_sets
    pairwise_common = sorted(set.intersection(*pairwise_sets)) if pairwise_sets else []
    pairwise_requested = bool(data.get("pairwise"))

    uns_sets = [set(as_list(batch.get("uns_keys"))) for batch in batches]
    uns_union = sorted(set.union(*uns_sets)) if uns_sets else []
    uns_common = sorted(set.intersection(*uns_sets)) if uns_sets else []
    uns_conflict_keys = sorted(set(as_list(data.get("conflicting_uns_keys"))))
    if not uns_conflict_keys and data.get("uns_conflicts"):
        uns_conflict_keys = sorted(set(as_list(data.get("uns_conflicts"))))

    storages = [str(batch.get("storage", "memory")).lower() for batch in batches]
    any_on_disk = any(storage in ON_DISK_STORAGES or storage.endswith((".h5ad", ".zarr")) for storage in storages)
    total_cells = estimate_cells(batches, axis, len(joined_names))
    memory_limit = data.get("memory_limit_cells", MEMORY_HEAVY_CELLS)
    memory_heavy = isinstance(total_cells, int) and isinstance(memory_limit, int) and total_cells > memory_limit

    recommendations: dict[str, Any] = {
        "api": "anndata.concat",
        "axis": axis,
        "join": join,
        "label": data.get("label", "batch"),
        "keys": names,
        "index_unique": "-" if duplicate_risk or data.get("force_index_unique", True) else None,
        "merge": "same",
        "uns_merge": "unique" if uns_union and uns_common != uns_union else "same",
        "fill_value": data.get("fill_value", None),
        "pairwise": pairwise_requested or False,
        "force_lazy": bool(data.get("force_lazy", False)),
    }

    risks = list(join_warnings)
    checks = [
        "validate result shape against expected axis sums and joined-axis size",
        f"check {axis}_names.is_unique",
        "check batch label counts",
        "inspect retained uns keys and merged metadata keys",
    ]

    if join == "outer":
        risks.append("outer join introduces filled values; sparse arrays fill absent entries with zero by default")
        checks.append("inspect fill values for labels absent from each batch")
    if duplicate_risk:
        risks.append(f"duplicate {axis} names detected or declared; keep index_unique='-'")
    if uns_conflict_keys:
        risks.append("declared conflicting uns keys: " + ", ".join(uns_conflict_keys))
        recommendations["uns_merge"] = "unique"
    elif uns_union and uns_common != uns_union:
        risks.append("uns keys differ across batches; uns_merge='unique' keeps non-conflicting nested values")
    if pairwise_sets and not pairwise_common:
        risks.append(f"no shared {'obsp' if axis == 'obs' else 'varp'} keys for pairwise concat")
    if pairwise_requested:
        risks.append("pairwise=True creates block-diagonal arrays with zero cross-batch blocks")
    if any_on_disk or memory_heavy or data.get("prefer_on_disk"):
        recommendations["api"] = "anndata.experimental.concat_on_disk"
        recommendations["on_disk"] = True
        recommendations["max_loaded_elems"] = int(data.get("max_loaded_elems", 100_000_000))
        risks.append("on-disk concat is recommended for declared file inputs or memory pressure")
        checks.append("read output in backed mode and validate shape/labels before full load")
        if pairwise_requested:
            recommendations["pairwise"] = False
            risks.append("concat_on_disk does not support pairwise=True; recompute pairwise arrays after combining")
    else:
        recommendations["on_disk"] = False
    if data.get("lazy_collection"):
        recommendations["anncollection"] = {
            "join_vars": "inner" if axis == "obs" and join == "inner" else None,
            "label": recommendations["label"],
            "index_unique": recommendations["index_unique"],
        }
        risks.append("AnnCollection lazily concatenates along observations and requires join_vars='inner' when variables differ")

    return {
        "summary": {
            "batch_count": len(batches),
            "batch_names": names,
            "axis": axis,
            "non_concatenated_axis": other_axis,
            "intersection_size": len(ordered_intersection(other_names)) if all(other_names) else None,
            "union_size": len(ordered_union(other_names)) if all(other_names) else None,
            "estimated_result_cells": total_cells,
            "storage_kinds": storages,
        },
        "recommendations": recommendations,
        "risks": risks,
        "validation_checks": checks,
        "native_call_template": build_call_template(recommendations),
    }


def build_call_template(recommendations: Mapping[str, Any]) -> str:
    api = recommendations["api"]
    kwargs = []
    for key in ["axis", "join", "label", "keys", "index_unique", "merge", "uns_merge", "fill_value", "pairwise", "force_lazy"]:
        if key not in recommendations:
            continue
        value = recommendations[key]
        if key == "force_lazy" and api.endswith("concat_on_disk"):
            continue
        if value is None and key in {"fill_value", "index_unique"}:
            kwargs.append(f"{key}=None")
        elif value is not None:
            kwargs.append(f"{key}={value!r}")
    if api.endswith("concat_on_disk"):
        kwargs.append(f"max_loaded_elems={recommendations.get('max_loaded_elems', 100_000_000)!r}")
        return api + "(input_files, out_file, " + ", ".join(kwargs) + ")"
    return api + "(adatas, " + ", ".join(kwargs) + ")"


def print_text(result: Mapping[str, Any]) -> None:
    print("AnnData concat plan")
    print("===================")
    summary = result["summary"]
    recs = result["recommendations"]
    print(f"API: {recs['api']}")
    print(f"Axis: {recs['axis']}")
    print(f"Join: {recs['join']}")
    print(f"Keys: {', '.join(recs['keys'])}")
    print(f"Index unique: {recs['index_unique']!r}")
    print(f"Merge: {recs['merge']}; uns_merge: {recs['uns_merge']}")
    print(f"Pairwise: {recs['pairwise']}")
    print(f"Estimated result cells: {summary['estimated_result_cells']}")
    print("\nTemplate:")
    print("  " + result["native_call_template"])
    print("\nRisks:")
    for risk in result["risks"] or ["no major risks detected from provided metadata"]:
        print(f"  - {risk}")
    print("\nValidation checks:")
    for check in result["validation_checks"]:
        print(f"  - {check}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read JSON metadata for AnnData batches and suggest concat parameters/risks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", "-i", help="Path to JSON metadata. Reads stdin when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args()

    payload = load_payload(args.input)
    result = plan(payload)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)


if __name__ == "__main__":
    main()
