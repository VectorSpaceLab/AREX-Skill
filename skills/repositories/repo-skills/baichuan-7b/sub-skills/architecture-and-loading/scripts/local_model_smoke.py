#!/usr/bin/env python3
"""Safe Baichuan-7B local-source smoke test.

This helper imports the repository's local `models/` source via `--repo-root`,
builds a tiny `BaiChuanForCausalLM`, runs an eval-mode forward pass, verifies
cache preparation, and optionally checks basic CUDA availability. It does not
load official 7B weights, download tokenizer files, read datasets, or call
network services.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _is_baichuan_repo_root(path: Path) -> bool:
    return (
        (path / "models" / "configuration_baichuan.py").is_file()
        and (path / "models" / "modeling_baichuan.py").is_file()
    )


def _discover_repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not _is_baichuan_repo_root(root):
            raise FileNotFoundError(
                f"--repo-root must contain models/configuration_baichuan.py and "
                f"models/modeling_baichuan.py; got {root}"
            )
        return root

    starts = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    seen = set()
    for start in starts:
        for candidate in (start, *start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if _is_baichuan_repo_root(candidate):
                return candidate

    raise FileNotFoundError(
        "Could not auto-discover a Baichuan-7B checkout. Re-run with "
        "--repo-root /path/to/Baichuan-7B."
    )


def _import_local_classes(repo_root: Path):
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    try:
        from models.configuration_baichuan import BaiChuanConfig
        from models.modeling_baichuan import BaiChuanForCausalLM
    except Exception as exc:  # import errors often include torch/xformers version issues
        raise RuntimeError(
            "Failed to import local Baichuan model source. Ensure --repo-root is "
            "correct and the Python environment has compatible torch, transformers, "
            "and xformers packages."
        ) from exc
    return BaiChuanConfig, BaiChuanForCausalLM


def _tiny_config(BaiChuanConfig):
    return BaiChuanConfig(
        vocab_size=32,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=4,
        hidden_act="silu",
        max_position_embeddings=16,
        use_cache=True,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
        tie_word_embeddings=False,
    )


def _assert_shape(actual: Tuple[int, ...], expected: Tuple[int, ...], label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label} shape mismatch: expected {expected}, got {actual}")


def _run_forward_and_generation_prep(BaiChuanConfig, BaiChuanForCausalLM, seed: int) -> Dict[str, Any]:
    import torch

    torch.manual_seed(seed)
    config = _tiny_config(BaiChuanConfig)
    model = BaiChuanForCausalLM(config)
    model.eval()

    input_ids = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
    attention_mask = torch.ones_like(input_ids)

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=input_ids,
            use_cache=True,
            return_dict=True,
        )

    _assert_shape(tuple(outputs.logits.shape), (1, 4, 32), "logits")
    if outputs.loss is None or not torch.isfinite(outputs.loss).item():
        raise AssertionError("Expected a finite causal-LM loss from the tiny forward pass")
    if not outputs.past_key_values or len(outputs.past_key_values) != config.num_hidden_layers:
        raise AssertionError("Expected one cache entry per decoder layer when use_cache=True")

    past_key_values = outputs.past_key_values
    first_key, first_value = past_key_values[0]
    _assert_shape(tuple(first_key.shape), (1, 4, 4, 8), "first past key")
    _assert_shape(tuple(first_value.shape), (1, 4, 4, 8), "first past value")

    prepared_initial = model.prepare_inputs_for_generation(
        input_ids,
        attention_mask=attention_mask,
        use_cache=True,
    )
    expected_keys = {"input_ids", "position_ids", "past_key_values", "use_cache", "attention_mask"}
    if set(prepared_initial) != expected_keys:
        raise AssertionError(
            f"Initial prepare_inputs_for_generation keys mismatch: {sorted(prepared_initial)}"
        )
    _assert_shape(tuple(prepared_initial["input_ids"].shape), (1, 4), "initial prepared input_ids")
    _assert_shape(tuple(prepared_initial["position_ids"].shape), (1, 4), "initial position_ids")

    extended_input_ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
    extended_attention_mask = torch.ones_like(extended_input_ids)
    prepared_cached = model.prepare_inputs_for_generation(
        extended_input_ids,
        past_key_values=past_key_values,
        attention_mask=extended_attention_mask,
        use_cache=True,
    )
    if set(prepared_cached) != expected_keys:
        raise AssertionError(
            f"Cached prepare_inputs_for_generation keys mismatch: {sorted(prepared_cached)}"
        )
    _assert_shape(tuple(prepared_cached["input_ids"].shape), (1, 1), "cached prepared input_ids")
    _assert_shape(tuple(prepared_cached["position_ids"].shape), (1, 1), "cached position_ids")
    if prepared_cached["input_ids"].item() != 5:
        raise AssertionError("Cached generation path should keep only the last token id")
    if prepared_cached["position_ids"].item() != 4:
        raise AssertionError("Cached generation path should keep only the last computed position id")

    return {
        "config": {
            "vocab_size": config.vocab_size,
            "hidden_size": config.hidden_size,
            "intermediate_size": config.intermediate_size,
            "num_hidden_layers": config.num_hidden_layers,
            "num_attention_heads": config.num_attention_heads,
            "max_position_embeddings": config.max_position_embeddings,
            "use_cache": config.use_cache,
        },
        "forward": {
            "logits_shape": list(outputs.logits.shape),
            "loss_finite": True,
            "loss_value": float(outputs.loss.detach().cpu()),
            "past_key_values_layers": len(past_key_values),
            "first_past_key_shape": list(first_key.shape),
        },
        "prepare_inputs_for_generation": {
            "initial_keys": sorted(prepared_initial.keys()),
            "cached_keys": sorted(prepared_cached.keys()),
            "cached_input_ids_shape": list(prepared_cached["input_ids"].shape),
            "cached_position_ids": prepared_cached["position_ids"].tolist(),
        },
        "has_generate": hasattr(model, "generate"),
    }


def _check_invalid_heads(BaiChuanConfig, BaiChuanForCausalLM) -> Dict[str, Any]:
    try:
        BaiChuanForCausalLM(
            BaiChuanConfig(
                vocab_size=32,
                hidden_size=30,
                intermediate_size=64,
                num_hidden_layers=1,
                num_attention_heads=8,
                max_position_embeddings=16,
            )
        )
    except ValueError as exc:
        message = str(exc)
        if "hidden_size must be divisible by num_heads" not in message:
            raise AssertionError(f"Invalid-head check raised the wrong ValueError: {message}") from exc
        return {"passed": True, "message": message}
    raise AssertionError("Invalid-head check should have raised ValueError")


def _check_cuda(requested: bool) -> Dict[str, Any]:
    if not requested:
        return {"requested": False}

    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("--cuda was requested, but torch.cuda.is_available() is false")
    tensor = torch.ones(1, device="cuda")
    return {
        "requested": True,
        "available": True,
        "device_count": torch.cuda.device_count(),
        "current_device": int(torch.cuda.current_device()),
        "allocation_sum": float(tensor.sum().detach().cpu()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a safe Baichuan-7B local-source tiny model smoke test."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Path to a Baichuan-7B checkout containing models/configuration_baichuan.py. "
        "If omitted, the helper searches upward from the current directory and this script.",
    )
    parser.add_argument(
        "--cuda",
        action="store_true",
        help="Also require torch CUDA availability and perform a one-element CUDA allocation.",
    )
    parser.add_argument(
        "--skip-invalid-head-check",
        action="store_true",
        help="Skip the synthetic invalid hidden_size/num_attention_heads assertion.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Torch manual seed for tiny model initialization.")
    parser.add_argument("--debug", action="store_true", help="Print a traceback on failure.")
    args = parser.parse_args()

    try:
        repo_root = _discover_repo_root(args.repo_root)
        BaiChuanConfig, BaiChuanForCausalLM = _import_local_classes(repo_root)

        import torch
        import transformers

        result: Dict[str, Any] = {
            "status": "ok",
            "repo_root": str(repo_root),
            "versions": {
                "python": sys.version.split()[0],
                "torch": torch.__version__,
                "transformers": transformers.__version__,
            },
        }
        result.update(_run_forward_and_generation_prep(BaiChuanConfig, BaiChuanForCausalLM, args.seed))
        if args.skip_invalid_head_check:
            result["invalid_head_divisibility"] = {"skipped": True}
        else:
            result["invalid_head_divisibility"] = _check_invalid_heads(BaiChuanConfig, BaiChuanForCausalLM)
        result["cuda"] = _check_cuda(args.cuda)

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - command-line helper should format all failures
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
