#!/usr/bin/env python3
"""Report Tevatron and optional workflow dependency availability.

This script is intentionally read-only: it imports lightweight modules when
possible, never downloads models or datasets, and never launches training.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class Probe:
    name: str
    import_name: str
    required_for: str
    ok: bool
    version: str | None = None
    error: str | None = None


def distribution_version(names: Iterable[str]) -> str | None:
    for name in names:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return None


def probe(name: str, import_name: str, required_for: str, distributions: Iterable[str] = ()) -> Probe:
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", None) or distribution_version(distributions or [name])
        return Probe(name=name, import_name=import_name, required_for=required_for, ok=True, version=version)
    except Exception as exc:  # noqa: BLE001 - report import-time optional dependency failures.
        return Probe(
            name=name,
            import_name=import_name,
            required_for=required_for,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def build_probes() -> list[Probe]:
    return [
        probe("tevatron", "tevatron", "all Tevatron workflows", ["tevatron"]),
        probe("transformers", "transformers", "model/tokenizer argument parsing and most drivers"),
        probe("datasets", "datasets", "Hugging Face and local JSON/JSONL dataset loading"),
        probe("numpy", "numpy", "embedding arrays and FAISS search helpers"),
        probe("faiss-cpu/faiss-gpu", "faiss", "retrieval search and tiny FAISS smoke checks", ["faiss-cpu", "faiss-gpu"]),
        probe("torch", "torch", "PyTorch training, encoding, reranking, LoRA, and most model execution"),
        probe("peft", "peft", "LoRA retriever/reranker workflows"),
        probe("deepspeed", "deepspeed", "DeepSpeed ZeRO training launchers"),
        probe("accelerate", "accelerate", "distributed/model loading helper paths"),
        probe("Pillow", "PIL", "image dataset fields and multimodal workflows", ["Pillow"]),
        probe("qwen-omni-utils", "qwen_omni_utils", "Qwen-Omni multimodal processing", ["qwen-omni-utils"]),
        probe("vllm", "vllm", "vLLM encoding drivers"),
        probe("jax", "jax", "JAX/TPU retriever routes"),
        probe("flax", "flax", "JAX/TPU retriever routes"),
        probe("optax", "optax", "JAX/Tevax optimization routes"),
    ]


def summarize(probes: list[Probe]) -> dict[str, object]:
    missing_required = [p for p in probes[:3] if not p.ok]
    optional_missing = [p for p in probes[3:] if not p.ok]
    return {
        "python": sys.version.split()[0],
        "ok_for_base_import": not missing_required,
        "missing_base": [asdict(p) for p in missing_required],
        "missing_optional": [asdict(p) for p in optional_missing],
        "probes": [asdict(p) for p in probes],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Tevatron base imports and optional workflow dependencies.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        choices=["search", "torch", "lora", "deepspeed", "multimodal", "vllm", "jax"],
        help="Require an optional dependency group for the selected workflow.",
    )
    args = parser.parse_args()

    probes = build_probes()
    result = summarize(probes)

    requirements = {
        "search": {"faiss-cpu/faiss-gpu"},
        "torch": {"torch"},
        "lora": {"torch", "peft"},
        "deepspeed": {"torch", "deepspeed"},
        "multimodal": {"torch", "Pillow"},
        "vllm": {"torch", "vllm"},
        "jax": {"jax", "flax", "optax"},
    }
    required_names = set().union(*(requirements[item] for item in args.require)) if args.require else set()
    missing_required_optional = [p for p in probes if p.name in required_names and not p.ok]
    result["required_groups"] = args.require
    result["ok_for_required_groups"] = not missing_required_optional
    result["missing_required_optional"] = [asdict(p) for p in missing_required_optional]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        for item in probes:
            status = "ok" if item.ok else "missing"
            suffix = f" ({item.version})" if item.version else ""
            print(f"{status:7} {item.name:18} {item.required_for}{suffix}")
        if missing_required_optional:
            print("\nMissing dependencies for requested groups:")
            for item in missing_required_optional:
                print(f"- {item.name}: {item.error}")

    return 0 if result["ok_for_base_import"] and result["ok_for_required_groups"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
