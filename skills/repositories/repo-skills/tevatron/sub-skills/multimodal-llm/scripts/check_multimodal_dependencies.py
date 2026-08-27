#!/usr/bin/env python3
"""Report optional Tevatron multimodal/LLM workflow dependencies.

This script is intentionally import-discovery only: it does not import
Tevatron drivers, load models, initialize GPUs, or touch network resources. It
helps agents decide which optional workflow dependencies are available before
planning Qwen/ColPali/DSE/RepLLaMA, RankLLaMA, or vLLM commands.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from importlib import metadata
except ImportError:  # pragma: no cover - Python 3.7 without importlib_metadata.
    metadata = None


@dataclass(frozen=True)
class Dependency:
    key: str
    module: str
    distribution: Optional[str]
    purpose: str
    required_for: Tuple[str, ...]


@dataclass
class DependencyStatus:
    key: str
    module: str
    installed: bool
    version: Optional[str]
    purpose: str
    required_for: List[str]


DEPENDENCIES: Tuple[Dependency, ...] = (
    Dependency(
        key="transformers",
        module="transformers",
        distribution="transformers",
        purpose="Core model, tokenizer, processor, and argument parsing support.",
        required_for=("all Tevatron model workflows",),
    ),
    Dependency(
        key="datasets",
        module="datasets",
        distribution="datasets",
        purpose="Hugging Face dataset loading for local JSON/JSONL and public datasets.",
        required_for=("training", "encoding"),
    ),
    Dependency(
        key="torch",
        module="torch",
        distribution="torch",
        purpose="PyTorch model execution, training, standard encoding, and reranking.",
        required_for=("train", "train_mm", "encode", "encode_mm", "rerank"),
    ),
    Dependency(
        key="PIL",
        module="PIL",
        distribution="Pillow",
        purpose="Image object support used by multimodal datasets and vLLM image encoding paths.",
        required_for=("image datasets", "DSE", "ColPali", "vllm_encode_mm"),
    ),
    Dependency(
        key="qwen_omni_utils",
        module="qwen_omni_utils",
        distribution="qwen-omni-utils",
        purpose="Qwen multimodal message preprocessing via process_mm_info in packaged collators.",
        required_for=("train_mm", "encode_mm", "vllm_encode_mm", "Qwen-Omni"),
    ),
    Dependency(
        key="qwen_vl_utils",
        module="qwen_vl_utils",
        distribution="qwen-vl-utils",
        purpose="Qwen-VL vision preprocessing used by several example-local DSE/ColPali evaluators.",
        required_for=("Qwen2.5-VL example evaluators", "DSE-Qwen examples", "ColPali examples"),
    ),
    Dependency(
        key="peft",
        module="peft",
        distribution="peft",
        purpose="LoRA adapter training, loading, and merging.",
        required_for=("--lora", "--lora_name_or_path", "RepLLaMA", "RankLLaMA"),
    ),
    Dependency(
        key="vllm",
        module="vllm",
        distribution="vllm",
        purpose="vLLM embedding inference through tevatron.retriever.driver.vllm_encode*.",
        required_for=("vllm_encode", "vllm_encode_mm"),
    ),
    Dependency(
        key="flash_attn",
        module="flash_attn",
        distribution="flash-attn",
        purpose="Optional FlashAttention 2 backend; Tevatron model args default to flash_attention_2.",
        required_for=("large Qwen/LLM acceleration",),
    ),
    Dependency(
        key="deepspeed",
        module="deepspeed",
        distribution="deepspeed",
        purpose="Distributed training launcher and ZeRO configs used by large-model examples.",
        required_for=("large LoRA training", "train_mm examples"),
    ),
)


WORKFLOW_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "minimal": ("transformers", "datasets"),
    "text-llm": ("transformers", "datasets", "torch", "peft"),
    "qwen3": ("transformers", "datasets", "torch"),
    "qwen-vl": ("transformers", "datasets", "torch", "PIL", "qwen_omni_utils"),
    "qwen-omni": ("transformers", "datasets", "torch", "PIL", "qwen_omni_utils"),
    "multimodal": ("transformers", "datasets", "torch", "PIL", "qwen_omni_utils", "peft"),
    "vllm-text": ("transformers", "datasets", "vllm", "peft"),
    "vllm-mm": ("transformers", "datasets", "PIL", "qwen_omni_utils", "vllm", "peft"),
    "colpali": ("transformers", "datasets", "torch", "PIL"),
    "dse-example": ("transformers", "datasets", "torch", "PIL"),
    "training-large": ("transformers", "datasets", "torch", "peft", "deepspeed"),
}


def distribution_version(distribution: Optional[str]) -> Optional[str]:
    if distribution is None or metadata is None:
        return None
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def inspect_dependency(dep: Dependency) -> DependencyStatus:
    installed = importlib.util.find_spec(dep.module) is not None
    version = distribution_version(dep.distribution) if installed else None
    return DependencyStatus(
        key=dep.key,
        module=dep.module,
        installed=installed,
        version=version,
        purpose=dep.purpose,
        required_for=list(dep.required_for),
    )


def statuses() -> List[DependencyStatus]:
    return [inspect_dependency(dep) for dep in DEPENDENCIES]


def missing_for_workflow(items: Iterable[DependencyStatus], workflow: str) -> List[str]:
    required = set(WORKFLOW_REQUIREMENTS[workflow])
    return [item.key for item in items if item.key in required and not item.installed]


def print_text_report(items: List[DependencyStatus], workflow: Optional[str]) -> None:
    width = max(len(item.key) for item in items)
    print("Tevatron multimodal/LLM dependency report")
    print("No Tevatron drivers, models, GPUs, or network resources were loaded.\n")
    for item in items:
        state = "ok" if item.installed else "missing"
        version = f" ({item.version})" if item.version else ""
        print(f"{item.key:<{width}}  {state}{version}")
        print(f"{'':<{width}}  module: {item.module}")
        print(f"{'':<{width}}  use: {item.purpose}")
    if workflow:
        missing = missing_for_workflow(items, workflow)
        print(f"\nWorkflow: {workflow}")
        if missing:
            print("Missing required optional packages: " + ", ".join(missing))
        else:
            print("Required packages for this workflow are import-detectable.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow",
        choices=sorted(WORKFLOW_REQUIREMENTS),
        help="Highlight missing packages for one workflow profile.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    items = statuses()
    payload = {
        "ok": True,
        "python": sys.version.split()[0],
        "workflow": args.workflow,
        "dependencies": [asdict(item) for item in items],
        "missing_for_workflow": missing_for_workflow(items, args.workflow) if args.workflow else [],
        "notes": [
            "This script performs import discovery only and never loads Tevatron drivers or models.",
            "Missing optional packages may be acceptable for workflows that do not need them.",
            "qwen_omni_utils is required by packaged multimodal collators; qwen_vl_utils appears in example-local vision utilities.",
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text_report(items, args.workflow)

    return 0 if not payload["missing_for_workflow"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
