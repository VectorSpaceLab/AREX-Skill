#!/usr/bin/env python3
"""Validate that a GPT2-Chinese checkout can be imported and smoke-tested.

Safe to run from any directory. Point --repo-root at the checkout you want to
inspect. The script checks module imports, a tiny GPT-2 config, the default
BERT tokenizer, the word-level tokenizer, the BPE helper, and a one-step
cached-past generation smoke.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List



SPECIAL_SAMPLE = "[CLS]最美的不是下雨天"
WORD_SAMPLE = "今天天气不错"
BPE_SAMPLE = "今天天气不错"


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def import_module(name: str) -> None:
    __import__(name)
    print(f"import-ok: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="GPT2-Chinese install smoke check")
    parser.add_argument("--repo-root", required=True, help="Path to the GPT2-Chinese checkout")
    parser.add_argument("--config-path", default="config/model_config_test.json", help="Relative or absolute config path")
    parser.add_argument("--char-vocab-path", default="cache/vocab_small.txt", help="Relative or absolute default vocab path")
    parser.add_argument("--word-vocab-path", default="cache/vocab_seg.txt", help="Relative or absolute word-level vocab path")
    parser.add_argument("--encoder-json", default="tokenizations/encoder.json", help="Relative or absolute BPE encoder JSON")
    parser.add_argument("--vocab-bpe", default="tokenizations/vocab.bpe", help="Relative or absolute BPE merges file")
    parser.add_argument("--sample-text", default=SPECIAL_SAMPLE, help="Sample text for the default tokenizer smoke")
    parser.add_argument("--word-sample-text", default=WORD_SAMPLE, help="Sample text for the word-level tokenizer smoke")
    parser.add_argument("--bpe-sample-text", default=BPE_SAMPLE, help="Sample text for the BPE tokenizer smoke")
    parser.add_argument("--generate-length", type=int, default=2, help="Number of new tokens to sample in the generation smoke")
    parser.add_argument("--skip-word", action="store_true", help="Skip the word-level tokenizer smoke")
    parser.add_argument("--skip-bpe", action="store_true", help="Skip the BPE tokenizer smoke")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        print(f"repo-root not found: {repo_root}", file=sys.stderr)
        return 2

    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    errors: List[str] = []

    try:
        import torch
    except Exception as exc:  # pragma: no cover - direct failure path
        print(f"torch import failed: {exc}", file=sys.stderr)
        return 1

    try:
        import_module("train")
        import_module("train_single")
        import_module("eval")
        import_module("generate")
        import_module("generate_texts")
    except Exception as exc:  # pragma: no cover - direct failure path
        errors.append(f"repo module import failed: {exc}")

    try:
        from transformers.modeling_gpt2 import GPT2Config, GPT2LMHeadModel
        from tokenizations.tokenization_bert import BertTokenizer as CharTokenizer
        from tokenizations.tokenization_bert_word_level import BertTokenizer as WordTokenizer
        from tokenizations.bpe_tokenizer import get_encoder
        import generate as generate_module
    except Exception as exc:
        errors.append(f"core API import failed: {exc}")
        print("\n".join(errors), file=sys.stderr)
        return 1

    config_path = resolve(repo_root, args.config_path)
    char_vocab_path = resolve(repo_root, args.char_vocab_path)
    word_vocab_path = resolve(repo_root, args.word_vocab_path)
    encoder_json = resolve(repo_root, args.encoder_json)
    vocab_bpe = resolve(repo_root, args.vocab_bpe)

    if not config_path.exists():
        errors.append(f"missing config file: {config_path}")
    if not char_vocab_path.exists():
        errors.append(f"missing char vocab file: {char_vocab_path}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    cfg = GPT2Config.from_json_file(str(config_path))
    print(f"config-ok: n_ctx={cfg.n_ctx} n_layer={cfg.n_layer} n_embd={cfg.n_embd} vocab_size={cfg.vocab_size}")

    model = GPT2LMHeadModel(config=cfg)
    model.eval()
    print(f"model-ok: {model.__class__.__name__}")

    char_tokenizer = CharTokenizer(vocab_file=str(char_vocab_path))
    char_tokens = char_tokenizer.tokenize(args.sample_text)
    char_ids = char_tokenizer.convert_tokens_to_ids(char_tokens)
    print(f"char-tokenizer-ok: {len(char_tokens)} tokens, first_ids={char_ids[:8]}")

    if not char_ids:
        errors.append("default tokenizer produced no ids")
    else:
        with torch.no_grad():
            inputs = torch.tensor([char_ids[: cfg.n_ctx]], dtype=torch.long)
            outputs = model(input_ids=inputs)
            logits = outputs[0]
            print(f"forward-ok: logits_shape={tuple(logits.shape)}")

        generated = generate_module.generate(
            cfg.n_ctx,
            model,
            char_ids[:],
            args.generate_length,
            char_tokenizer,
            temperature=1.0,
            top_k=2,
            top_p=0.0,
            device="cpu",
            is_fast_pattern=True,
        )
        print(f"generation-ok: generated_ids={len(generated)}")

    if not args.skip_word:
        try:
            word_tokenizer = WordTokenizer(vocab_file=str(word_vocab_path))
            word_tokens = word_tokenizer.tokenize(args.word_sample_text)
            word_ids = word_tokenizer.convert_tokens_to_ids(word_tokens)
            print(f"word-tokenizer-ok: tokens={word_tokens[:8]} ids={word_ids[:8]}")
        except Exception as exc:
            errors.append(f"word tokenizer smoke failed: {exc}")

    if not args.skip_bpe:
        try:
            if not encoder_json.exists():
                raise FileNotFoundError(encoder_json)
            if not vocab_bpe.exists():
                raise FileNotFoundError(vocab_bpe)
            encoder = get_encoder(str(encoder_json), str(vocab_bpe))
            pieces = encoder.tokenize(args.bpe_sample_text)
            print(f"bpe-tokenizer-ok: pieces={pieces[:8]}")
        except Exception as exc:
            errors.append(f"BPE tokenizer smoke failed: {exc}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("OK: GPT2-Chinese install smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
