#!/usr/bin/env python3
"""Inspect TorchDrug layer/model signatures without downloads or training."""

import argparse
import importlib
import inspect
import sys
import warnings


def import_torchdrug():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=Warning)
        import torchdrug
        from torchdrug import layers, models
        from torchdrug.layers import functional
    return torchdrug, layers, models, functional


def safe_signature(obj):
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def print_signature(title, obj):
    print(f"{title}: {safe_signature(obj)}")


def section(title):
    print(f"\n[{title}]")


def inspect_optional():
    section("optional imports")
    for name in ["torch_scatter", "torch_cluster"]:
        try:
            module = importlib.import_module(name)
        except Exception as error:  # pragma: no cover - diagnostic helper
            print(f"{name}: unavailable ({error.__class__.__name__}: {error})")
        else:
            version = getattr(module, "__version__", "unknown")
            print(f"{name}: available (version={version})")


def inspect_layers(layers):
    section("layers")
    names = [
        "MessagePassingBase",
        "GraphConv",
        "GraphAttentionConv",
        "GraphIsomorphismConv",
        "RelationalGraphConv",
        "NeuralFingerprintConv",
        "ContinuousFilterConv",
        "MessagePassing",
        "ChebyshevConv",
        "GeometricRelationalGraphConv",
        "MeanReadout",
        "SumReadout",
        "MaxReadout",
        "AttentionReadout",
        "Set2Set",
        "NodeSampler",
        "EdgeSampler",
    ]
    for name in names:
        obj = getattr(layers, name, None)
        if obj is not None:
            print_signature(f"layers.{name}", obj)


def inspect_geometry(layers):
    section("geometry")
    for name in ["GraphConstruction", "SpatialLineGraph"]:
        obj = getattr(layers, name, None)
        if obj is not None:
            print_signature(f"layers.{name}", obj)
    geometry = getattr(layers, "geometry", None)
    for name in [
        "BondEdge",
        "KNNEdge",
        "SpatialEdge",
        "SequentialEdge",
        "AlphaCarbonNode",
        "IdentityNode",
        "RandomEdgeMask",
        "SubsequenceNode",
        "SubspaceNode",
    ]:
        obj = getattr(geometry, name, None) if geometry is not None else None
        if obj is not None:
            print_signature(f"layers.geometry.{name}", obj)


def inspect_models(models):
    section("models")
    names = [
        "GCN",
        "GAT",
        "GIN",
        "RGCN",
        "MPNN",
        "SchNet",
        "ChebNet",
        "GearNet",
        "GraphAF",
        "InfoGraph",
        "MultiviewContrast",
        "TransE",
        "DistMult",
        "ComplEx",
        "RotatE",
        "SimplE",
        "NeuralLP",
        "KBGAT",
        "ProteinCNN",
        "ProteinResNet",
        "ProteinLSTM",
        "ProteinBERT",
        "ESM",
    ]
    for name in names:
        obj = getattr(models, name, None)
        if obj is not None:
            print_signature(f"models.{name}", obj)


def inspect_variadic(functional):
    section("variadic helpers")
    names = [
        "variadic_sum",
        "variadic_mean",
        "variadic_max",
        "variadic_softmax",
        "variadic_log_softmax",
        "variadic_cross_entropy",
        "variadic_topk",
        "variadic_sort",
        "variadic_arange",
        "variadic_randperm",
        "variadic_sample",
        "variadic_meshgrid",
        "variadic_to_padded",
        "multi_slice",
        "multi_slice_mask",
        "as_mask",
    ]
    for name in names:
        obj = getattr(functional, name, None)
        if obj is not None:
            print_signature(f"functional.{name}", obj)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Print TorchDrug layer/model signatures and optional extension import status."
    )
    parser.add_argument("--all", action="store_true", help="print all available sections")
    parser.add_argument("--layers", action="store_true", help="print layer signatures")
    parser.add_argument("--models", action="store_true", help="print model signatures")
    parser.add_argument("--geometry", action="store_true", help="print graph construction signatures")
    parser.add_argument("--variadic", action="store_true", help="print variadic helper signatures")
    parser.add_argument("--optional", action="store_true", help="print optional import status")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not any(vars(args).values()):
        args.all = True

    needs_torchdrug = args.all or args.layers or args.models or args.geometry or args.variadic

    if args.optional:
        inspect_optional()
        if not needs_torchdrug:
            return 0

    try:
        torchdrug, layers, models, functional = import_torchdrug()
    except Exception as error:  # pragma: no cover - diagnostic helper
        print(f"failed to import torchdrug: {error.__class__.__name__}: {error}", file=sys.stderr)
        return 2

    version = getattr(torchdrug, "__version__", "unknown")
    print(f"torchdrug version: {version}")

    if args.all:
        inspect_optional()
    if args.all or args.layers:
        inspect_layers(layers)
    if args.all or args.geometry:
        inspect_geometry(layers)
    if args.all or args.models:
        inspect_models(models)
    if args.all or args.variadic:
        inspect_variadic(functional)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
