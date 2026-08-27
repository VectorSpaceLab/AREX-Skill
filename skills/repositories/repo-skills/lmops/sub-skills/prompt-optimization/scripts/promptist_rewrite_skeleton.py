#!/usr/bin/env python3
"""Offline Promptist rewrite argument validator and skeleton printer.

Default behavior is deliberately safe: no model loading, no downloads, no image
generation, and no training. The script validates arguments and prints the steps
that a future, explicitly approved Promptist rewrite run would follow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

DEFAULT_MODEL_ID = "microsoft/Promptist"
DEFAULT_TOKENIZER_ID = "gpt2"
DEFAULT_SUFFIX = " Rephrase:"


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse displays this
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def nonempty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def read_prompt_lines(path: Path, max_prompts: int) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"input path is not a file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    prompts = [line.strip() for line in lines if line.strip()]
    if not prompts:
        raise ValueError(f"input file has no nonempty prompt lines: {path}")
    if len(prompts) > max_prompts:
        raise ValueError(f"input file has {len(prompts)} prompts; increase --max-prompts if intentional")
    return prompts


def collect_prompts(args: argparse.Namespace) -> List[str]:
    if args.plain_text is not None:
        return [args.plain_text.strip()]
    return read_prompt_lines(Path(args.input_file), args.max_prompts)


def validate_generation(args: argparse.Namespace, prompts: List[str]) -> List[str]:
    warnings: List[str] = []
    if not args.model_id.strip():
        raise ValueError("--model-id must not be empty")
    if not args.tokenizer_id.strip():
        raise ValueError("--tokenizer-id must not be empty")
    if not args.suffix:
        raise ValueError("--suffix must not be empty")
    if "Rephrase:" not in args.suffix:
        warnings.append("suffix does not contain 'Rephrase:'; this diverges from the distilled Promptist demo")
    if not args.do_sample and args.num_return_sequences > args.num_beams:
        raise ValueError("with deterministic beam search, --num-return-sequences must be <= --num-beams")
    for idx, prompt in enumerate(prompts, start=1):
        if "Rephrase:" in prompt:
            warnings.append(f"prompt {idx} already contains 'Rephrase:'; the demo suffix will still be appended")
    if args.allow_downloads:
        warnings.append("--allow-downloads is only an acknowledgement; this skeleton still does not download or load models")
    return warnings


def skeleton_payload(args: argparse.Namespace, prompts: List[str], warnings: List[str]) -> dict:
    encoded_inputs = [prompt.strip() + args.suffix for prompt in prompts]
    generation_kwargs = {
        "do_sample": args.do_sample,
        "max_new_tokens": args.max_new_tokens,
        "num_beams": args.num_beams,
        "num_return_sequences": args.num_return_sequences,
        "length_penalty": args.length_penalty,
        "eos_token_id": "tokenizer.eos_token_id",
        "pad_token_id": "tokenizer.eos_token_id",
    }
    return {
        "safe": True,
        "imports_repo_code": False,
        "loads_models": False,
        "downloads_models": False,
        "generates_images": False,
        "trains_models": False,
        "model_id": args.model_id,
        "tokenizer_id": args.tokenizer_id,
        "prompt_count": len(prompts),
        "suffix": args.suffix,
        "generation_kwargs": generation_kwargs,
        "encoded_input_preview": encoded_inputs if args.show_prompts else ["<hidden>" for _ in encoded_inputs],
        "steps": [
            "After explicit approval, load tokenizer and causal language model.",
            "Set tokenizer.pad_token to tokenizer.eos_token and tokenizer.padding_side to left.",
            "Encode each stripped plain text prompt plus the configured suffix.",
            "Generate rewritten prompt candidates with the listed generation kwargs.",
            "Decode outputs, remove the original plain text plus suffix prefix, and strip whitespace.",
            "Pass rewritten text to a separate user-approved image-generation workflow if needed.",
        ],
        "real_run_requirements": [
            "PyTorch and Transformers installed",
            "Promptist model and tokenizer available in cache or network/model-registry access approved",
            "GPU recommended for responsive local use; CPU may be slow",
        ],
        "warnings": warnings,
    }


def print_text_plan(payload: dict) -> None:
    print("Promptist rewrite skeleton (offline; no model loading or downloads).")
    print(f"Model id: {payload['model_id']}")
    print(f"Tokenizer id: {payload['tokenizer_id']}")
    print(f"Prompt count: {payload['prompt_count']}")
    print(f"Suffix appended to each prompt: {payload['suffix']!r}")
    print("Generation kwargs:")
    for key, value in payload["generation_kwargs"].items():
        print(f"  - {key}: {value}")
    print("Encoded input preview:")
    for item in payload["encoded_input_preview"]:
        print(f"  - {item}")
    print("Planned steps:")
    for idx, step in enumerate(payload["steps"], start=1):
        print(f"  {idx}. {step}")
    print("Real-run requirements to confirm before loading models:")
    for item in payload["real_run_requirements"]:
        print(f"  - {item}")
    if payload["warnings"]:
        print("Warnings:", file=sys.stderr)
        for warning in payload["warnings"]:
            print(f"  - {warning}", file=sys.stderr)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Promptist rewrite arguments and print an offline execution skeleton; never load models by default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--plain-text", dest="plain_text", type=nonempty, help="One plain text prompt to rewrite")
    source.add_argument("--input-file", dest="input_file", help="UTF-8 text file with one plain prompt per nonempty line")
    parser.add_argument("--max-prompts", type=positive_int, default=20, help="Safety cap for prompts read from --input-file")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help="Promptist causal LM model identifier for a future real run")
    parser.add_argument("--tokenizer-id", default=DEFAULT_TOKENIZER_ID, help="Tokenizer identifier for a future real run")
    parser.add_argument("--suffix", default=DEFAULT_SUFFIX, help="Suffix appended before generation")
    parser.add_argument("--max-new-tokens", type=positive_int, default=75)
    parser.add_argument("--num-beams", type=positive_int, default=8)
    parser.add_argument("--num-return-sequences", type=positive_int, default=8)
    parser.add_argument("--length-penalty", type=float, default=-1.0)
    parser.add_argument("--do-sample", action="store_true", help="Plan sampling instead of deterministic beam generation")
    parser.add_argument("--allow-downloads", action="store_true", help="Acknowledgement flag only; this script still does not download or load models")
    parser.add_argument("--show-prompts", action="store_true", help="Print prompt text previews in the plan")
    parser.add_argument("--json", action="store_true", help="Print the skeleton as JSON")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        prompts = collect_prompts(args)
        warnings = validate_generation(args, prompts)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = skeleton_payload(args, prompts, warnings)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_text_plan(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
