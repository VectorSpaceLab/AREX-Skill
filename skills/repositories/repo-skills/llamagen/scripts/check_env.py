#!/usr/bin/env python3
"""Quick import and backend smoke for the LlamaGen skill."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Iterable


def import_modules(module_names: Iterable[str], *, section: str, optional: bool = False) -> bool:
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            missing = exc.name or module_name
            message = f"{section}: missing dependency while importing {module_name} (missing {missing})"
            if optional:
                print(message)
                return False
            raise SystemExit(message) from exc
        print(f"ok {module_name}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the key LlamaGen imports and the active CUDA backend."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Repository root to add to sys.path before imports.",
    )
    parser.add_argument(
        "--skip-cuda",
        action="store_true",
        help="Skip the CUDA availability and tiny allocation check.",
    )
    parser.add_argument(
        "--with-serving",
        action="store_true",
        help="Also import the vLLM serving path.",
    )
    parser.add_argument(
        "--with-eval",
        action="store_true",
        help="Also import the TensorFlow-backed evaluation modules.",
    )
    parser.add_argument(
        "--with-gradio",
        action="store_true",
        help="Also import the Gradio demo dependency.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    sys.path.insert(0, repo_root.as_posix())

    import torch

    print(f"torch={torch.__version__} cuda={torch.version.cuda}")
    if not args.skip_cuda:
        available = torch.cuda.is_available()
        print(f"cuda_available={available} count={torch.cuda.device_count()}")
        if not available:
            raise SystemExit("CUDA is not available in the current environment")
        print(f"device0={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
        _ = torch.empty((1,), device="cuda")
        print("cuda_allocation=ok")

    core_modules = [
        "tokenizer.tokenizer_image.vq_model",
        "autoregressive.models.gpt",
        "autoregressive.models.generate",
        "language.t5",
        "dataset.build",
    ]
    import_modules(core_modules, section="core imports")

    overall_ok = True

    if args.with_serving:
        overall_ok &= import_modules([
            "autoregressive.serve.llm",
            "autoregressive.serve.llm_engine",
            "autoregressive.serve.model_runner",
            "autoregressive.serve.sample_c2i",
        ], section="serving imports", optional=True)

    if args.with_eval:
        overall_ok &= import_modules([
            "evaluations.c2i.evaluator",
            "evaluations.t2i.evaluation",
        ], section="evaluation imports", optional=True)

    if args.with_gradio:
        overall_ok &= import_modules(["gradio"], section="gradio import", optional=True)

    if overall_ok:
        print("environment=ok")
        return 0

    print("environment=partial")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
