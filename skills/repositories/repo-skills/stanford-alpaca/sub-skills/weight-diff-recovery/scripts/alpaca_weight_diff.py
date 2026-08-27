#!/usr/bin/env python3
"""Self-contained Stanford Alpaca weight-diff runner.

Use --dry-run for planning and path-role validation without importing torch,
transformers, or loading checkpoint tensors. Live execution expects local
Hugging Face checkpoint directories and mirrors the source diff arithmetic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

EXPECTED_NAIVE_CHECKSUM = 50637.1836
DEFAULT_SMOKE_PROMPT = (
    "Below is an instruction that describes a task. "
    "Write a response that appropriately completes the request.\r\n\r\n"
    "### Instruction:\r\nList three technologies that make life easier.\r\n\r\n### Response:"
)


def smart_tokenizer_and_embedding_resize(special_tokens_dict: dict[str, str], tokenizer: Any, model: Any) -> None:
    """Source-aligned tokenizer/embedding resize helper.

    This local copy avoids importing Stanford Alpaca's train.py while preserving
    the behavior used by weight_diff.py: add special tokens, resize embeddings,
    and initialize new token rows with the average of existing embeddings.
    """

    num_new_tokens = tokenizer.add_special_tokens(special_tokens_dict)
    model.resize_token_embeddings(len(tokenizer))

    if num_new_tokens > 0:
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg


def _canonical(path: str) -> str:
    return str(Path(path).expanduser().resolve(strict=False))


def _validate_distinct_roles(mode: str, roles: dict[str, Optional[str]]) -> None:
    seen: dict[str, str] = {}
    for role, value in roles.items():
        if not value:
            continue
        normalized = _canonical(value)
        if normalized in seen:
            raise ValueError(f"path-role collision in {mode}: {role} and {seen[normalized]} both use {value!r}")
        seen[normalized] = role


def _require_local_dir(path: str, role: str) -> None:
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"{role} does not exist locally: {path}. Pre-download/convert checkpoints before live execution."
        )
    if not p.is_dir():
        raise NotADirectoryError(f"{role} must be a Hugging Face checkpoint directory, not a file: {path}")


def _load_runtime():
    try:
        import torch  # type: ignore
        import transformers  # type: ignore
    except (ImportError, ModuleNotFoundError) as exc:
        missing = getattr(exc, "name", None) or str(exc)
        raise RuntimeError(
            "Live weight-diff execution requires torch and transformers. "
            f"Missing import: {missing}. Use --dry-run for planning, or install the runtime dependencies."
        ) from exc
    return torch, transformers


def _torch_device(device: str, torch: Any):
    try:
        device_obj = torch.device(device)
    except Exception as exc:  # pragma: no cover - depends on torch internals
        raise ValueError(f"invalid torch device {device!r}: {exc}") from exc
    if device_obj.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("device='cuda' was requested, but torch.cuda.is_available() is false")
    return device_obj


def _load_model_and_tokenizer(path: str, role: str, device_obj: Any, torch: Any, transformers: Any):
    _require_local_dir(path, role)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        path,
        device_map={"": device_obj},
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    tokenizer = transformers.AutoTokenizer.from_pretrained(path, local_files_only=True)
    return model, tokenizer


def _maybe_resize_raw_tokenizer(tokenizer_raw: Any, model_raw: Any) -> None:
    if tokenizer_raw.pad_token is None:
        print("raw tokenizer has no pad token; adding [PAD] and resizing embeddings")
        smart_tokenizer_and_embedding_resize(
            special_tokens_dict={"pad_token": "[PAD]"},
            tokenizer=tokenizer_raw,
            model=model_raw,
        )


def _progress(keys, label: str):
    try:
        from tqdm.auto import tqdm  # type: ignore

        return tqdm(keys, desc=label)
    except Exception:
        return keys


def _assert_state_dict_compatible(left: dict[str, Any], right: dict[str, Any], left_name: str, right_name: str) -> None:
    left_keys = set(left)
    right_keys = set(right)
    if left_keys != right_keys:
        missing_left = sorted(right_keys - left_keys)[:10]
        missing_right = sorted(left_keys - right_keys)[:10]
        raise ValueError(
            f"state dict key mismatch between {left_name} and {right_name}; "
            f"missing from {left_name}: {missing_left}; missing from {right_name}: {missing_right}"
        )
    for key in left:
        if left[key].shape != right[key].shape:
            raise ValueError(
                f"state dict shape mismatch for {key!r}: {left_name} has {tuple(left[key].shape)}, "
                f"{right_name} has {tuple(right[key].shape)}"
            )


def _check_integrity_naively(state_dict_recovered: dict[str, Any], torch: Any) -> None:
    allsum = sum(tensor.sum() for tensor in state_dict_recovered.values())
    target = torch.full_like(allsum, fill_value=EXPECTED_NAIVE_CHECKSUM)
    if not torch.allclose(allsum, target, atol=1e-2, rtol=0):
        observed = float(allsum.detach().cpu())
        raise AssertionError(
            "Naive integrity check failed. "
            f"Expected approximately {EXPECTED_NAIVE_CHECKSUM}, observed {observed:.4f}."
        )
    print(f"naive integrity checksum passed: {float(allsum.detach().cpu()):.4f}")


def _run_inference_smoke(model: Any, tokenizer: Any) -> None:
    print("running qualitative inference smoke test; this is not a correctness proof")
    inputs = tokenizer(DEFAULT_SMOKE_PROMPT, return_tensors="pt")
    try:
        model_device = next(iter(model.parameters())).device
        inputs = {key: value.to(model_device) for key, value in inputs.items()}
    except Exception:
        pass
    out = model.generate(**inputs, max_new_tokens=100)
    output_text = tokenizer.batch_decode(out, skip_special_tokens=True)[0]
    completion = output_text[len(DEFAULT_SMOKE_PROMPT) :]
    print(f"Input: {DEFAULT_SMOKE_PROMPT}\nCompletion: {completion}")


def _print_plan(
    mode: str,
    path_raw: str,
    path_diff: str,
    path_tuned: Optional[str],
    device: str,
    test_inference: Optional[bool] = None,
    check_integrity_naively: Optional[bool] = None,
) -> None:
    print(f"Weight-diff plan ({mode}, dry-run):")
    print(f"- path_raw: {path_raw}")
    print(f"- path_diff: {path_diff}")
    if mode == "recover":
        if path_tuned:
            print(f"- path_tuned: {path_tuned} (save recovered model/tokenizer here)")
        else:
            print("- path_tuned: omitted (recover would keep the model in memory only)")
        print("- arithmetic: diff-plus-raw")
        print(f"- naive checksum: {'enabled' if check_integrity_naively else 'disabled'}")
        print(f"- inference smoke: {'enabled' if test_inference else 'disabled'}")
    else:
        print(f"- path_tuned: {path_tuned} (input tuned checkpoint)")
        print("- arithmetic: diff-minus-raw")
        print("- save target: path_diff")
    print(f"- device: {device}")
    print("- no checkpoint tensors are loaded in dry-run mode")


def make_diff(path_raw: str, path_tuned: str, path_diff: str, device: str = "cpu", dry_run: bool = False) -> None:
    """Make `path_diff` by subtracting raw weights from tuned weights."""

    _validate_distinct_roles(
        "make_diff",
        {"path_raw": path_raw, "path_tuned": path_tuned, "path_diff": path_diff},
    )
    if dry_run:
        _print_plan("make_diff", path_raw=path_raw, path_diff=path_diff, path_tuned=path_tuned, device=device)
        return

    torch, transformers = _load_runtime()
    device_obj = _torch_device(device, torch)
    model_tuned, tokenizer_tuned = _load_model_and_tokenizer(path_tuned, "path_tuned", device_obj, torch, transformers)
    model_raw, tokenizer_raw = _load_model_and_tokenizer(path_raw, "path_raw", device_obj, torch, transformers)
    _maybe_resize_raw_tokenizer(tokenizer_raw, model_raw)

    state_dict_tuned = model_tuned.state_dict()
    state_dict_raw = model_raw.state_dict()
    _assert_state_dict_compatible(state_dict_tuned, state_dict_raw, "path_tuned", "path_raw")
    for key in _progress(state_dict_tuned.keys(), "diff-minus-raw"):
        state_dict_tuned[key].add_(-state_dict_raw[key])

    Path(path_diff).expanduser().mkdir(parents=True, exist_ok=True)
    model_tuned.save_pretrained(path_diff)
    tokenizer_tuned.save_pretrained(path_diff)
    print(f"saved weight diff to {path_diff}")


def recover(
    path_raw: str,
    path_diff: str,
    path_tuned: Optional[str] = None,
    device: str = "cpu",
    test_inference: bool = True,
    check_integrity_naively: bool = True,
    dry_run: bool = False,
):
    """Recover tuned weights by adding raw weights to a diff checkpoint."""

    _validate_distinct_roles(
        "recover",
        {"path_raw": path_raw, "path_diff": path_diff, "path_tuned": path_tuned},
    )
    if dry_run:
        _print_plan(
            "recover",
            path_raw=path_raw,
            path_diff=path_diff,
            path_tuned=path_tuned,
            device=device,
            test_inference=test_inference,
            check_integrity_naively=check_integrity_naively,
        )
        return None

    torch, transformers = _load_runtime()
    device_obj = _torch_device(device, torch)
    model_raw, tokenizer_raw = _load_model_and_tokenizer(path_raw, "path_raw", device_obj, torch, transformers)
    model_recovered, tokenizer_recovered = _load_model_and_tokenizer(path_diff, "path_diff", device_obj, torch, transformers)
    _maybe_resize_raw_tokenizer(tokenizer_raw, model_raw)

    state_dict_recovered = model_recovered.state_dict()
    state_dict_raw = model_raw.state_dict()
    _assert_state_dict_compatible(state_dict_recovered, state_dict_raw, "path_diff", "path_raw")
    for key in _progress(state_dict_recovered.keys(), "diff-plus-raw"):
        state_dict_recovered[key].add_(state_dict_raw[key])

    if check_integrity_naively:
        _check_integrity_naively(state_dict_recovered, torch)

    if path_tuned is not None:
        Path(path_tuned).expanduser().mkdir(parents=True, exist_ok=True)
        model_recovered.save_pretrained(path_tuned)
        tokenizer_recovered.save_pretrained(path_tuned)
        print(f"saved recovered model/tokenizer to {path_tuned}")
    else:
        print("path_tuned omitted; recovered model/tokenizer were not saved")

    if test_inference:
        _run_inference_smoke(model_recovered, tokenizer_recovered)

    return model_recovered, tokenizer_recovered


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    recover_parser = subparsers.add_parser("recover", help="Recover tuned weights from raw + diff.")
    recover_parser.add_argument("--path-raw", required=True, help="HF-converted raw LLaMA checkpoint directory.")
    recover_parser.add_argument("--path-diff", required=True, help="Released Alpaca weight-diff checkpoint directory.")
    recover_parser.add_argument("--path-tuned", help="Optional output directory for recovered weights.")
    recover_parser.add_argument("--device", default="cpu", help="Torch device string, e.g. cpu, cuda, or cuda:0.")
    recover_parser.add_argument("--test-inference", action=argparse.BooleanOptionalAction, default=True)
    recover_parser.add_argument("--check-integrity-naively", action=argparse.BooleanOptionalAction, default=True)
    recover_parser.add_argument("--dry-run", action="store_true", help="Plan without importing torch/transformers or loading weights.")

    make_parser = subparsers.add_parser("make_diff", help="Create a diff from raw and tuned checkpoints.")
    make_parser.add_argument("--path-raw", required=True, help="HF-converted raw LLaMA checkpoint directory.")
    make_parser.add_argument("--path-tuned", required=True, help="Tuned checkpoint directory to subtract raw weights from.")
    make_parser.add_argument("--path-diff", required=True, help="Output directory for the resulting diff.")
    make_parser.add_argument("--device", default="cpu", help="Torch device string, e.g. cpu, cuda, or cuda:0.")
    make_parser.add_argument("--dry-run", action="store_true", help="Plan without importing torch/transformers or loading weights.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "recover":
            recover(
                path_raw=args.path_raw,
                path_diff=args.path_diff,
                path_tuned=args.path_tuned,
                device=args.device,
                test_inference=args.test_inference,
                check_integrity_naively=args.check_integrity_naively,
                dry_run=args.dry_run,
            )
        elif args.command == "make_diff":
            make_diff(
                path_raw=args.path_raw,
                path_tuned=args.path_tuned,
                path_diff=args.path_diff,
                device=args.device,
                dry_run=args.dry_run,
            )
        else:  # pragma: no cover
            parser.error(f"unknown command: {args.command}")
    except (AssertionError, FileNotFoundError, NotADirectoryError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
