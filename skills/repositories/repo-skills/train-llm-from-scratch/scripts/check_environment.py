#!/usr/bin/env python3
"""Safe environment smoke checks for train-llm-from-scratch.

This helper imports the public package modules, reports dependency/backends, and
optionally runs a tiny Transformer forward/loss on CPU or CUDA. It does not read
user datasets, download models, launch training, or write checkpoints.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass


@dataclass
class CheckResult:
    python: str
    imports: dict[str, str]
    dependencies: dict[str, str]
    cuda: dict[str, object]
    tiny_model: dict[str, object]
    ok: bool


def version_of(dist: str) -> str:
    try:
        from importlib.metadata import version

        return version(dist)
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {exc}"


def try_import(name: str) -> str:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        return f"FAIL: {exc.__class__.__name__}: {exc}"
    return f"ok: {getattr(mod, '__file__', '<built-in>')}"


def run_tiny_model(device: str) -> dict[str, object]:
    try:
        import torch
        from src.models.transformer import Transformer
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": f"import failed: {exc}"}

    if device == "cuda" and not torch.cuda.is_available():
        return {"status": "skipped", "reason": "CUDA requested but torch.cuda.is_available() is false"}

    try:
        torch.manual_seed(0)
        dev = torch.device(device)
        model = Transformer(n_head=2, n_embed=16, context_length=8, vocab_size=64, N_BLOCKS=1).to(dev)
        model.eval()
        idx = torch.randint(0, 64, (2, 8), device=dev)
        with torch.no_grad():
            logits, loss = model(idx, idx)
        return {
            "status": "passed",
            "device": device,
            "logits_shape": list(logits.shape),
            "loss": float(loss.item()),
            "parameters": int(sum(p.numel() for p in model.parameters())),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "device": device, "error": f"{exc.__class__.__name__}: {exc}"}


def collect(args: argparse.Namespace) -> CheckResult:
    imports = {name: try_import(name) for name in [
        "config",
        "data_loader",
        "src",
        "src.models.transformer",
        "src.post_training.chat_template",
        "src.post_training.dpo",
        "src.post_training.ppo",
        "src.post_training.grpo",
        "src.post_training.inference",
        "ui",
    ]}

    dependencies = {dist: version_of(dist) for dist in [
        "train-llm-from-scratch",
        "torch",
        "numpy",
        "h5py",
        "tiktoken",
        "zstandard",
        "datasets",
        "streamlit",
        "pandas",
        "altair",
        "wandb",
    ]}

    cuda: dict[str, object] = {}
    try:
        import torch

        cuda = {
            "torch_version": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            cuda.update({
                "device_name_0": torch.cuda.get_device_name(0),
                "capability_0": list(torch.cuda.get_device_capability(0)),
            })
            try:
                x = torch.empty((1,), device="cuda")
                cuda["tiny_allocation"] = f"passed: {x.device.type}:{x.numel()}"
            except Exception as exc:  # noqa: BLE001
                cuda["tiny_allocation"] = f"failed: {exc}"
    except Exception as exc:  # noqa: BLE001
        cuda = {"status": "failed", "error": f"{exc.__class__.__name__}: {exc}"}

    if args.backend == "auto":
        model_device = "cuda" if cuda.get("available") else "cpu"
    else:
        model_device = args.backend
    tiny = run_tiny_model(model_device)

    ok = all(v.startswith("ok:") for v in imports.values()) and tiny.get("status") == "passed"
    if args.backend == "cuda":
        ok = ok and bool(cuda.get("available")) and str(cuda.get("tiny_allocation", "")).startswith("passed")

    return CheckResult(
        python=sys.version.replace("\n", " "),
        imports=imports,
        dependencies=dependencies,
        cuda=cuda,
        tiny_model=tiny,
        ok=bool(ok),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run safe import/backend smoke checks for train-llm-from-scratch.")
    p.add_argument("--backend", choices=("auto", "cpu", "cuda"), default="auto", help="Tiny model device to require/check.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = collect(args)
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"python: {result.python}")
        print("imports:")
        for name, status in result.imports.items():
            print(f"  {name}: {status}")
        print("dependencies:")
        for name, status in result.dependencies.items():
            print(f"  {name}: {status}")
        print("cuda:")
        for key, value in result.cuda.items():
            print(f"  {key}: {value}")
        print("tiny_model:")
        for key, value in result.tiny_model.items():
            print(f"  {key}: {value}")
        print(f"overall_ok: {result.ok}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
