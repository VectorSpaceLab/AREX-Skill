#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Print DeepSpeed parallelism/MoE API import availability and signatures.

This script is intentionally read-only. It imports selected DeepSpeed modules and
prints signatures when available; it does not initialize distributed process
groups, allocate models, or launch training.
"""

import argparse
import importlib
import inspect
from typing import Iterable, Tuple

API_TARGETS: Tuple[Tuple[str, str], ...] = (
    ("deepspeed.pipe", "PipelineModule"),
    ("deepspeed.pipe", "LayerSpec"),
    ("deepspeed.pipe", "TiedLayerSpec"),
    ("deepspeed.runtime.pipe", "ProcessTopology"),
    ("deepspeed.moe.layer", "MoE"),
    ("deepspeed.moe.utils", "split_params_into_different_moe_groups_for_optimizer"),
    ("deepspeed.sequence.layer", "DistributedAttention"),
    ("deepspeed.runtime.sequence_parallel.ulysses_sp", "UlyssesSPAttentionHF"),
    ("deepspeed.runtime.sequence_parallel.ulysses_sp", "UlyssesSPDataLoaderAdapter"),
    ("deepspeed.runtime.sequence_parallel.parallel_state_sp", "initialize_sequence_parallel"),
    ("deepspeed.sequence.auto_sp", "auto_wrap_model_for_sp"),
    ("deepspeed.checkpointing", "configure"),
    ("deepspeed.checkpointing", "checkpoint"),
    ("deepspeed.checkpointing", "reset"),
)

METHOD_TARGETS: Tuple[Tuple[str, str, str], ...] = (
    ("deepspeed.runtime.pipe.engine", "PipelineEngine", "train_batch"),
    ("deepspeed.runtime.pipe.engine", "PipelineEngine", "eval_batch"),
    ("deepspeed.runtime.sequence_parallel.ulysses_sp", "UlyssesSPAttentionHF", "register_with_transformers"),
)


def safe_signature(obj: object) -> str:
    """Return a best-effort inspect signature for an object."""
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def inspect_objects(targets: Iterable[Tuple[str, str]]) -> None:
    for module_name, object_name in targets:
        label = f"{module_name}.{object_name}"
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, object_name)
        except Exception as exc:  # noqa: BLE001 - report import availability without failing early.
            print(f"MISSING {label}: {type(exc).__name__}: {exc}")
            continue
        print(f"FOUND   {label}: {safe_signature(obj)}")


def inspect_methods(targets: Iterable[Tuple[str, str, str]]) -> None:
    for module_name, class_name, method_name in targets:
        label = f"{module_name}.{class_name}.{method_name}"
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            method = getattr(cls, method_name)
        except Exception as exc:  # noqa: BLE001 - report import availability without failing early.
            print(f"MISSING {label}: {type(exc).__name__}: {exc}")
            continue
        print(f"FOUND   {label}: {safe_signature(method)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print import availability and signatures for DeepSpeed parallelism, MoE, sequence, and checkpointing APIs."
    )
    parser.add_argument("--methods", action="store_true", help="Also inspect selected class methods such as PipelineEngine.train_batch.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inspect_objects(API_TARGETS)
    if args.methods:
        inspect_methods(METHOD_TARGETS)


if __name__ == "__main__":
    main()
