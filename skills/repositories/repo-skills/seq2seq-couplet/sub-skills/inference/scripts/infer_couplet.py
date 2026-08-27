#!/usr/bin/env python3
"""Run one-off couplet inference from a checkpoint.

By default this uses the self-contained runtime copy bundled with the skill.
Supply ``--repo-root`` only when intentionally comparing against a live checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import couplet_runtime  # noqa: E402


def path_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate couplet candidates from a trained checkpoint.")
    parser.add_argument("text", help="Raw input upper-line text, not space-tokenized.")
    parser.add_argument("--repo-root", default=None, help="Optional checkout to use instead of the bundled runtime copy.")
    parser.add_argument("--vocab-file", type=path_arg, required=True, help="Vocabulary file used for the checkpoint.")
    parser.add_argument("--model-dir", type=path_arg, required=True, help="Checkpoint directory containing model.ckpl files.")
    parser.add_argument("--censor-words-file", type=path_arg, help="Optional censor-word file for service-style score penalties.")
    parser.add_argument("--max-input-length", type=int, default=50)
    parser.add_argument("--num-units", type=int, default=1024)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=None, help="Optional number of ranked candidates to print.")
    parser.add_argument("--dry-run", action="store_true", help="Validate files and print config without loading TensorFlow checkpoint.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.vocab_file.exists():
        raise SystemExit("vocab file not found: %s" % args.vocab_file)
    if not args.model_dir.exists():
        raise SystemExit("model directory not found: %s" % args.model_dir)
    couplet_runtime.validate_vocab_file(args.vocab_file)
    censor_words = couplet_runtime.load_censor_words(args.censor_words_file)

    config = {
        "vocab_file": str(args.vocab_file),
        "model_dir": str(args.model_dir),
        "repo_root": str(Path(args.repo_root).expanduser().resolve()) if args.repo_root else None,
        "num_units": args.num_units,
        "layers": args.layers,
        "dropout": args.dropout,
        "max_input_length": args.max_input_length,
        "censor_words": len(censor_words),
        "text": args.text,
    }
    if args.dry_run:
        print(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    model = couplet_runtime.load_inference_model(
        args.repo_root,
        vocab_file=args.vocab_file,
        model_dir=args.model_dir,
        num_units=args.num_units,
        layers=args.layers,
        dropout=args.dropout,
    )
    outputs, scores = couplet_runtime.predict_text(
        model,
        args.text,
        censor_words=censor_words,
        max_input_length=args.max_input_length,
    )
    if args.top_k is not None:
        outputs = outputs[: args.top_k]
        scores = scores[: args.top_k]
    print(json.dumps({"output": outputs, "score": scores}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
