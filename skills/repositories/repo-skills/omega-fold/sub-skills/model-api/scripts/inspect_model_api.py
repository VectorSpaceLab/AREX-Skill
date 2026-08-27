#!/usr/bin/env python3
"""Safely inspect the installed OmegaFold model API without downloading weights."""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import sys
from typing import Any


def _safe_distribution_version() -> str:
    for dist_name in ("OmegaFold", "omegafold"):
        try:
            return importlib.metadata.version(dist_name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "unknown"


def _format_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {exc}>"


def _namespace_summary(ns: Any) -> dict[str, Any]:
    return {
        "alphabet_size": getattr(ns, "alphabet_size", None),
        "node_dim": getattr(ns, "node_dim", None),
        "edge_dim": getattr(ns, "edge_dim", None),
        "geo_num_blocks": getattr(ns, "geo_num_blocks", None),
        "struct_embedder": getattr(ns, "struct_embedder", None),
        "plm": {
            "alphabet_size": getattr(getattr(ns, "plm", None), "alphabet_size", None),
            "node": getattr(getattr(ns, "plm", None), "node", None),
            "edge": getattr(getattr(ns, "plm", None), "edge", None),
        },
        "struct": {
            "node_dim": getattr(getattr(ns, "struct", None), "node_dim", None),
            "edge_dim": getattr(getattr(ns, "struct", None), "edge_dim", None),
            "num_cycle": getattr(getattr(ns, "struct", None), "num_cycle", None),
            "num_bins": getattr(getattr(ns, "struct", None), "num_bins", None),
        },
    }


def _print_section(title: str) -> None:
    print(f"\n## {title}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the installed OmegaFold Python API. This script does not "
            "download or load weights; --instantiate only constructs the model."
        )
    )
    parser.add_argument(
        "--instantiate",
        action="store_true",
        help=(
            "Construct OmegaFold(make_config(MODEL)) to verify allocation and "
            "method availability. This can use substantial RAM."
        ),
    )
    parser.add_argument(
        "--model",
        type=int,
        default=1,
        choices=(1, 2),
        help="Config id to use with --instantiate; valid values are 1 and 2.",
    )
    parser.add_argument(
        "--check-invalid-model",
        action="store_true",
        help="Verify that make_config rejects an invalid model id.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of human-readable sections.",
    )
    args = parser.parse_args()

    try:
        import omegafold
        from omegafold import confidence, pipeline
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        print(f"ERROR: failed to import OmegaFold API: {exc}", file=sys.stderr)
        print(
            "Hint: install OmegaFold plus compatible torch/biopython; if torch "
            "1.12 is used, constrain numpy<2.",
            file=sys.stderr,
        )
        return 1

    report: dict[str, Any] = {
        "distribution_version": _safe_distribution_version(),
        "module_imported": True,
        "signatures": {
            "omegafold.make_config": _format_signature(omegafold.make_config),
            "omegafold.OmegaFold": _format_signature(omegafold.OmegaFold),
            "omegafold.OmegaFold.forward": _format_signature(omegafold.OmegaFold.forward),
            "omegafold.OmegaFold.deep_sequence_embed": _format_signature(
                omegafold.OmegaFold.deep_sequence_embed
            ),
            "omegafold.OmegaFold.create_initial_prev_dict": _format_signature(
                omegafold.OmegaFold.create_initial_prev_dict
            ),
            "pipeline.fasta2inputs": _format_signature(pipeline.fasta2inputs),
            "pipeline.save_pdb": _format_signature(pipeline.save_pdb),
            "pipeline._load_weights": _format_signature(pipeline._load_weights),
            "pipeline._get_device": _format_signature(pipeline._get_device),
            "confidence.get_all_confidence": _format_signature(
                confidence.get_all_confidence
            ),
        },
        "configs": {},
        "invalid_model_check": None,
        "instantiation": None,
    }

    for model_idx in (1, 2):
        cfg = omegafold.make_config(model_idx)
        report["configs"][str(model_idx)] = _namespace_summary(cfg)

    if args.check_invalid_model:
        try:
            omegafold.make_config(3)
        except Exception as exc:  # noqa: BLE001 - diagnostic output
            report["invalid_model_check"] = {
                "raised": type(exc).__name__,
                "message": str(exc),
            }
        else:
            report["invalid_model_check"] = {
                "raised": None,
                "message": "make_config(3) unexpectedly succeeded",
            }

    if args.instantiate:
        try:
            cfg = omegafold.make_config(args.model)
            model = omegafold.OmegaFold(cfg)
            parameter_count = sum(param.numel() for param in model.parameters())
            report["instantiation"] = {
                "model": args.model,
                "class": type(model).__name__,
                "training": model.training,
                "parameter_count": parameter_count,
                "has_forward": callable(getattr(model, "forward", None)),
                "has_deep_sequence_embed": callable(
                    getattr(model, "deep_sequence_embed", None)
                ),
                "has_create_initial_prev_dict": callable(
                    getattr(model, "create_initial_prev_dict", None)
                ),
                "warning": "Model constructed without weights; do not infer without load_state_dict.",
            }
        except Exception as exc:  # pragma: no cover - environment diagnostic path
            report["instantiation"] = {
                "model": args.model,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    _print_section("Package")
    print(f"distribution_version: {report['distribution_version']}")
    print(f"module_imported: {report['module_imported']}")

    _print_section("Signatures")
    for name, signature in report["signatures"].items():
        print(f"{name}{signature}")

    _print_section("Config Summaries")
    for model_idx, summary in report["configs"].items():
        print(f"model {model_idx}:")
        print(json.dumps(summary, indent=2, sort_keys=True))

    if report["invalid_model_check"] is not None:
        _print_section("Invalid Model Check")
        print(json.dumps(report["invalid_model_check"], indent=2, sort_keys=True))

    if report["instantiation"] is not None:
        _print_section("Instantiation")
        print(json.dumps(report["instantiation"], indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
