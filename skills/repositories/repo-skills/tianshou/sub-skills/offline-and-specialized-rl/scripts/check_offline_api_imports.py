#!/usr/bin/env python3
"""Safely inspect Tianshou offline/specialized RL API availability.

The default smoke imports selected Tianshou classes and prints concise
constructor signatures. It does not read the original repository checkout, load
external datasets, create environments, start training, spawn workers, use the
network, or launch benchmarks.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Probe:
    label: str
    module: str
    names: tuple[str, ...]
    optional: bool = False


PROBES: tuple[Probe, ...] = (
    Probe(
        "continuous-offline",
        "tianshou.algorithm.imitation.bcq",
        ("BCQPolicy", "BCQ"),
    ),
    Probe(
        "continuous-cql",
        "tianshou.algorithm.imitation.cql",
        ("CQL",),
    ),
    Probe(
        "continuous-td3bc",
        "tianshou.algorithm.imitation.td3_bc",
        ("TD3BC",),
    ),
    Probe(
        "discrete-bcq",
        "tianshou.algorithm.imitation.discrete_bcq",
        ("DiscreteBCQPolicy", "DiscreteBCQ"),
    ),
    Probe(
        "discrete-cql-crr",
        "tianshou.algorithm.imitation.discrete_cql",
        ("DiscreteCQL",),
    ),
    Probe(
        "discrete-crr",
        "tianshou.algorithm.imitation.discrete_crr",
        ("DiscreteCRR",),
    ),
    Probe(
        "imitation-base",
        "tianshou.algorithm.imitation.imitation_base",
        ("ImitationPolicy", "OffPolicyImitationLearning", "OfflineImitationLearning"),
    ),
    Probe(
        "gail",
        "tianshou.algorithm.imitation.gail",
        ("GAIL",),
    ),
    Probe(
        "icm",
        "tianshou.algorithm.modelbased.icm",
        ("ICMOffPolicyWrapper", "ICMOnPolicyWrapper"),
    ),
    Probe(
        "psrl",
        "tianshou.algorithm.modelbased.psrl",
        ("PSRLPolicy", "PSRL"),
    ),
    Probe(
        "multiagent",
        "tianshou.algorithm.multiagent.marl",
        ("MultiAgentPolicy", "MultiAgentOffPolicyAlgorithm", "MultiAgentOnPolicyAlgorithm"),
    ),
    Probe(
        "random-marl",
        "tianshou.algorithm.random",
        ("MARLRandomDiscreteMaskedOffPolicyAlgorithm",),
    ),
    Probe(
        "evaluation-launcher",
        "tianshou.evaluation.launcher",
        ("JoblibConfig", "SequentialExpLauncher", "JoblibExpLauncher", "RegisteredExpLauncher"),
        optional=True,
    ),
    Probe(
        "rliable-evaluation",
        "tianshou.evaluation.rliable_evaluation",
        ("EvaluationSequenceEntry", "MultiRunExperimentResult", "load_and_eval_experiment"),
        optional=True,
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import Tianshou offline/specialized RL classes and print concise "
            "signatures without datasets, training, networking, or benchmark execution."
        ),
    )
    parser.add_argument(
        "--include-optional",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include optional evaluation probes such as joblib/rliable imports (default: true)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any selected probe fails, including optional probes",
    )
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="print importable class/function names without inspect.signature output",
    )
    return parser


def format_signature(obj: object) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def run_probe(probe: Probe, names_only: bool) -> bool:
    print(f"[{probe.label}] {probe.module}")
    try:
        module = importlib.import_module(probe.module)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report import exceptions clearly.
        status = "optional-missing" if probe.optional else "missing"
        print(f"  {status}: {exc.__class__.__name__}: {exc}")
        return probe.optional

    ok = True
    for name in probe.names:
        if not hasattr(module, name):
            print(f"  missing attribute: {name}")
            ok = False
            continue
        obj = getattr(module, name)
        if names_only:
            print(f"  ok: {name}")
        else:
            print(f"  ok: {name}{format_signature(obj)}")
    return ok


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected = [probe for probe in PROBES if args.include_optional or not probe.optional]

    print("Tianshou offline/specialized RL API import smoke")
    print("No datasets, training, networking, subprocesses, or benchmark launchers are executed.\n")

    results = [run_probe(probe, args.names_only) for probe in selected]
    failed = len(results) - sum(results)
    print(f"\nSummary: {sum(results)}/{len(results)} probe groups importable")
    if failed and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
