#!/usr/bin/env python3
"""Inspect common DeepChem featurizer outputs for tiny SMILES/FASTA inputs."""

import argparse
import json
import sys
from typing import Any, Dict, Iterable, List



def _json_default(value: Any) -> Any:
    np_module = globals().get("np")
    if np_module is not None:
        if isinstance(value, np_module.generic):
            return value.item()
        if isinstance(value, np_module.ndarray):
            return value.tolist()
    return str(value)


def _shape(value: Any) -> Any:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    return list(shape)


def _is_empty_feature(value: Any) -> bool:
    shape = getattr(value, "shape", None)
    if shape is not None and tuple(shape) == (0,):
        return True
    if value is None:
        return True
    return False


def _summarize_graph(value: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "type": type(value).__name__,
        "empty": False,
        "num_nodes": getattr(value, "num_nodes", None),
        "num_edges": getattr(value, "num_edges", None),
        "node_features_shape": _shape(getattr(value, "node_features", None)),
        "edge_index_shape": _shape(getattr(value, "edge_index", None)),
        "edge_features_shape": _shape(getattr(value, "edge_features", None)),
    }
    if hasattr(value, "num_node_features"):
        summary["num_node_features"] = value.num_node_features
    if hasattr(value, "num_edge_features"):
        summary["num_edge_features"] = value.num_edge_features
    return summary


def _summarize_feature(value: Any) -> Dict[str, Any]:
    if hasattr(value, "node_features") and hasattr(value, "edge_index"):
        return _summarize_graph(value)

    summary: Dict[str, Any] = {
        "type": type(value).__name__,
        "shape": _shape(value),
        "empty": _is_empty_feature(value),
    }

    if isinstance(value, np.ndarray):
        summary["dtype"] = str(value.dtype)
        if value.size and value.dtype != object:
            summary["min"] = float(np.nanmin(value))
            summary["max"] = float(np.nanmax(value))
            summary["nonzero"] = int(np.count_nonzero(value))
        elif value.dtype == object:
            summary["length"] = int(len(value))
    elif isinstance(value, dict):
        summary["length"] = len(value)
        sample_keys = list(value.keys())[:5]
        summary["sample_keys"] = [str(key) for key in sample_keys]
        if sample_keys:
            summary["sample_value_type"] = type(value[sample_keys[0]]).__name__
    elif hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            summary["length"] = len(value)
        except TypeError:
            pass

    return summary


def _construct_featurizer(name: str, args: argparse.Namespace) -> Any:
    import deepchem as dc

    if name == "circular":
        return dc.feat.CircularFingerprint(
            radius=args.radius,
            size=args.size,
            chiral=args.chiral,
            sparse=args.sparse,
            smiles=args.fragment_smiles,
            is_counts_based=args.counts,
        )
    if name == "molgraph":
        return dc.feat.MolGraphConvFeaturizer(
            use_edges=args.use_edges,
            use_chirality=args.chiral,
            use_partial_charge=args.use_partial_charge,
        )
    if name == "rdkit":
        return dc.feat.RDKitDescriptors(
            is_normalized=args.normalized,
            use_fragment=not args.no_fragment,
            use_bcut2d=not args.no_bcut2d,
            labels_only=args.labels_only,
        )
    if name == "coulomb":
        if args.max_atoms is None:
            raise ValueError("--max-atoms is required for the coulomb featurizer")
        return dc.feat.CoulombMatrix(max_atoms=args.max_atoms, upper_tri=args.upper_tri)
    if name == "fasta":
        if not hasattr(dc.feat, "FASTAFeaturizer"):
            raise ImportError("FASTAFeaturizer is unavailable; install the optional sequence dependency")
        return dc.feat.FASTAFeaturizer()
    raise ValueError(f"Unknown featurizer: {name}")


def _summarize_featurizer_config(featurizer: Any) -> Dict[str, Any]:
    config: Dict[str, Any] = {"class": type(featurizer).__name__}
    for key, value in vars(featurizer).items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            config[key] = value
        elif isinstance(value, list) and len(value) <= 20 and all(isinstance(item, str) for item in value):
            config[key] = value
        elif key == "reqd_properties" and hasattr(value, "keys"):
            config["num_required_properties"] = len(value)
            config["first_required_properties"] = list(value.keys())[:10]
    return config


def _inspect_batch(featurizer: Any, inputs: Iterable[str]) -> Dict[str, Any]:
    inputs = list(inputs)
    features = featurizer.featurize(inputs)
    batch_summary: Dict[str, Any] = {
        "featurizer": _summarize_featurizer_config(featurizer),
        "batch_type": type(features).__name__,
        "batch_shape": _shape(features),
        "batch_dtype": str(getattr(features, "dtype", "")),
        "entries": [],
    }
    for index, raw in enumerate(inputs):
        try:
            feature = features[index]
        except Exception as exc:  # defensive: keep diagnostics printable
            batch_summary["entries"].append({
                "index": index,
                "input": raw,
                "error": f"could not index feature batch: {exc}",
            })
            continue
        entry = {"index": index, "input": raw}
        entry.update(_summarize_feature(feature))
        batch_summary["entries"].append(entry)
    return batch_summary


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect DeepChem featurizer output types, shapes, and failed entries for tiny inputs."
    )
    parser.add_argument("--smiles", nargs="*", default=["CCO"], help="SMILES strings to inspect.")
    parser.add_argument("--fasta", nargs="*", default=[], help="Optional FASTA file paths for FASTAFeaturizer.")
    parser.add_argument(
        "--featurizers",
        nargs="+",
        default=["circular", "molgraph", "rdkit"],
        choices=["circular", "molgraph", "rdkit", "coulomb", "fasta"],
        help="Featurizers to run.",
    )
    parser.add_argument("--size", type=int, default=16, help="Circular fingerprint size.")
    parser.add_argument("--radius", type=int, default=2, help="Circular fingerprint radius.")
    parser.add_argument("--chiral", action="store_true", help="Enable chirality for supported featurizers.")
    parser.add_argument("--counts", action="store_true", help="Use count-based circular fingerprints.")
    parser.add_argument("--sparse", action="store_true", help="Use sparse circular fingerprints.")
    parser.add_argument("--fragment-smiles", action="store_true", help="Include fragment SMILES for sparse fingerprints.")
    parser.add_argument("--use-edges", action="store_true", help="Include MolGraphConv edge features.")
    parser.add_argument("--use-partial-charge", action="store_true", help="Include MolGraphConv partial charges.")
    parser.add_argument("--normalized", action="store_true", help="Normalize RDKit descriptors.")
    parser.add_argument("--no-fragment", action="store_true", help="Disable RDKit fragment descriptors.")
    parser.add_argument("--no-bcut2d", action="store_true", help="Disable RDKit BCUT2D descriptors.")
    parser.add_argument("--labels-only", action="store_true", help="Convert nonzero RDKit descriptor values to labels.")
    parser.add_argument("--max-atoms", type=int, default=None, help="Required max_atoms for CoulombMatrix.")
    parser.add_argument("--upper-tri", action="store_true", help="Flatten CoulombMatrix upper triangle.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any entry is empty or a featurizer errors.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    global np
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        report = {"ok": False, "results": {}, "error": f"NumPy is required to inspect features: {exc}"}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    report: Dict[str, Any] = {"ok": True, "results": {}}

    for name in args.featurizers:
        inputs = args.fasta if name == "fasta" else args.smiles
        if not inputs:
            report["results"][name] = {"skipped": "no inputs supplied"}
            continue
        try:
            featurizer = _construct_featurizer(name, args)
            result = _inspect_batch(featurizer, inputs)
            failed = [entry for entry in result["entries"] if entry.get("empty") or entry.get("error")]
            result["failed_count"] = len(failed)
            if failed:
                report["ok"] = False
            report["results"][name] = result
        except Exception as exc:
            report["ok"] = False
            report["results"][name] = {"error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
