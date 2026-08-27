#!/usr/bin/env python3
"""Inspect local legacy BERT/UniLM vocab files without downloading models."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import unicodedata
from typing import Iterable

SPECIAL_TOKENS = ("[UNK]", "[SEP]", "[X_SEP]", "[PAD]", "[CLS]", "[MASK]")
S2S_TOKENS = ("[S2S_CLS]", "[S2S_SEP]", "[S2S_SOS]")
COMMON_MODEL_HINTS = {
    "bert-base-uncased": {"expected_case": "uncased", "max_positions": 512},
    "bert-large-uncased": {"expected_case": "uncased", "max_positions": 512},
    "bert-base-cased": {"expected_case": "cased", "max_positions": 512},
    "bert-large-cased": {"expected_case": "cased", "max_positions": 512},
    "bert-base-multilingual-uncased": {"expected_case": "uncased", "max_positions": 512},
    "bert-base-multilingual-cased": {"expected_case": "cased", "max_positions": 512},
    "bert-base-chinese": {"expected_case": "cased", "max_positions": 512},
}


def parser() -> argparse.ArgumentParser:
    argp = argparse.ArgumentParser(
        description=(
            "Inspect a local vocab.txt for legacy UniLM/BERT tokenizer compatibility. "
            "This helper never imports torch, downloads checkpoints, or loads model weights."
        )
    )
    argp.add_argument("--vocab-file", required=True, help="Local one-token-per-line vocab.txt file.")
    argp.add_argument("--bert-model", help="Optional BERT model name hint such as bert-large-cased.")
    argp.add_argument("--config-file", help="Optional bert_config.json/config.json to inspect basic size fields.")
    argp.add_argument("--sample", help="Optional sample text to tokenize with the local vocab.")
    argp.add_argument("--do-lower-case", action="store_true", help="Lowercase and strip accents like uncased legacy BERT tokenization.")
    argp.add_argument("--tokenized-input", action="store_true", help="Treat --sample as already whitespace-tokenized WordPiece input.")
    argp.add_argument("--max-len", type=int, help="Optional sequence length budget to check against tokenized sample.")
    argp.add_argument("--show-remappings", action="store_true", help="Print special UniLM token availability/remapping suggestions.")
    argp.add_argument("--json", action="store_true", help="Emit a JSON report instead of human-readable text.")
    return argp


def load_vocab(path: str) -> collections.OrderedDict[str, int]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"vocab file not found: {path}")
    vocab: collections.OrderedDict[str, int] = collections.OrderedDict()
    with open(path, "r", encoding="utf-8") as reader:
        for index, line in enumerate(reader):
            token = line.rstrip("\n")
            if token in vocab:
                raise ValueError(f"duplicate token {token!r} at line {index + 1}")
            vocab[token] = index
    if not vocab:
        raise ValueError("vocab file is empty")
    return vocab


def load_config(path: str | None) -> dict[str, object] | None:
    if not path:
        return None
    if not os.path.isfile(path):
        raise FileNotFoundError(f"config file not found: {path}")
    with open(path, "r", encoding="utf-8") as reader:
        return json.load(reader)


def whitespace_tokenize(text: str) -> list[str]:
    text = text.strip()
    return [] if not text else text.split()


def is_whitespace(char: str) -> bool:
    return char in " \t\n\r" or unicodedata.category(char) == "Zs"


def is_control(char: str) -> bool:
    if char in "\t\n\r":
        return False
    return unicodedata.category(char) in ("Cc", "Cf")


def is_punctuation(char: str) -> bool:
    cp = ord(char)
    if (33 <= cp <= 47) or (58 <= cp <= 64) or (91 <= cp <= 96) or (123 <= cp <= 126):
        return True
    return unicodedata.category(char).startswith("P")


def is_chinese_char(cp: int) -> bool:
    return (
        (0x4E00 <= cp <= 0x9FFF)
        or (0x3400 <= cp <= 0x4DBF)
        or (0x20000 <= cp <= 0x2A6DF)
        or (0x2A700 <= cp <= 0x2B73F)
        or (0x2B740 <= cp <= 0x2B81F)
        or (0x2B820 <= cp <= 0x2CEAF)
        or (0xF900 <= cp <= 0xFAFF)
        or (0x2F800 <= cp <= 0x2FA1F)
    )


def clean_text(text: str) -> str:
    output: list[str] = []
    for char in text:
        cp = ord(char)
        if cp == 0 or cp == 0xFFFD or is_control(char):
            continue
        if is_whitespace(char):
            output.append(" ")
        else:
            output.append(char)
    return "".join(output)


def tokenize_chinese_chars(text: str) -> str:
    output: list[str] = []
    for char in text:
        if is_chinese_char(ord(char)):
            output.extend([" ", char, " "])
        else:
            output.append(char)
    return "".join(output)


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def split_on_punc(token: str, never_split: set[str]) -> list[str]:
    if token in never_split:
        return [token]
    output: list[list[str]] = []
    start_new_word = True
    for char in token:
        if is_punctuation(char):
            output.append([char])
            start_new_word = True
        else:
            if start_new_word:
                output.append([])
            start_new_word = False
            output[-1].append(char)
    return ["".join(chars) for chars in output]


def basic_tokenize(text: str, do_lower_case: bool, never_split: Iterable[str]) -> list[str]:
    never = set(never_split)
    text = tokenize_chinese_chars(clean_text(text))
    split_tokens: list[str] = []
    for token in whitespace_tokenize(text):
        if do_lower_case and token not in never:
            token = strip_accents(token.lower())
        split_tokens.extend(split_on_punc(token, never))
    return whitespace_tokenize(" ".join(split_tokens))


def wordpiece_tokenize(tokens: Iterable[str], vocab: dict[str, int], unk_token: str = "[UNK]", max_chars: int = 100) -> list[str]:
    output_tokens: list[str] = []
    for token in tokens:
        chars = list(token)
        if len(chars) > max_chars:
            output_tokens.append(unk_token)
            continue
        is_bad = False
        start = 0
        sub_tokens: list[str] = []
        while start < len(chars):
            end = len(chars)
            current = None
            while start < end:
                piece = "".join(chars[start:end])
                if start > 0:
                    piece = "##" + piece
                if piece in vocab:
                    current = piece
                    break
                end -= 1
            if current is None:
                is_bad = True
                break
            sub_tokens.append(current)
            start = end
        if is_bad:
            output_tokens.append(unk_token)
        else:
            output_tokens.extend(sub_tokens)
    return output_tokens


def tokenize_sample(sample: str, vocab: dict[str, int], do_lower_case: bool, tokenized_input: bool) -> list[str]:
    if tokenized_input:
        return whitespace_tokenize(sample)
    never_split = set(SPECIAL_TOKENS + S2S_TOKENS)
    basic = basic_tokenize(sample, do_lower_case=do_lower_case, never_split=never_split)
    return wordpiece_tokenize(basic, vocab)


def detect_case(vocab: dict[str, int]) -> dict[str, object]:
    has_upper = any(any(char.isupper() for char in token if token.isalpha()) for token in vocab)
    has_common_uncased = all(token in vocab for token in ("the", "of", "and"))
    has_common_cased = any(token in vocab for token in ("The", "Of", "And"))
    likely = "uncased" if has_common_uncased and not has_common_cased else "cased-or-mixed" if has_upper or has_common_cased else "unknown"
    return {"has_uppercase_tokens": has_upper, "likely_case": likely}


def ids_for(tokens: Iterable[str], vocab: dict[str, int]) -> list[int | None]:
    return [vocab.get(token) for token in tokens]


def config_summary(config: dict[str, object] | None) -> dict[str, object] | None:
    if config is None:
        return None
    keys = (
        "vocab_size",
        "hidden_size",
        "num_hidden_layers",
        "num_attention_heads",
        "intermediate_size",
        "max_position_embeddings",
        "type_vocab_size",
        "source_type_id",
        "target_type_id",
    )
    return {key: config[key] for key in keys if key in config}


def build_report(args: argparse.Namespace) -> dict[str, object]:
    vocab = load_vocab(args.vocab_file)
    config = load_config(args.config_file)
    special = {token: vocab.get(token) for token in SPECIAL_TOKENS}
    s2s = {token: vocab.get(token) for token in S2S_TOKENS}
    missing_special = [token for token, idx in special.items() if idx is None]
    missing_s2s = [token for token, idx in s2s.items() if idx is None]
    sample_tokens: list[str] | None = None
    sample_ids: list[int | None] | None = None
    unknown_count = None
    if args.sample is not None:
        sample_tokens = tokenize_sample(args.sample, vocab, args.do_lower_case, args.tokenized_input)
        sample_ids = ids_for(sample_tokens, vocab)
        unknown_count = sample_tokens.count("[UNK]") + sum(1 for token_id in sample_ids if token_id is None)
    model_hint = COMMON_MODEL_HINTS.get(args.bert_model or "")
    warnings: list[str] = []
    if missing_special:
        warnings.append("Missing core special tokens: " + ", ".join(missing_special))
    if args.show_remappings and missing_s2s:
        warnings.append("Missing UniLM S2S special tokens: " + ", ".join(missing_s2s))
    if model_hint:
        expected = model_hint["expected_case"]
        if expected == "uncased" and not args.do_lower_case:
            warnings.append(f"{args.bert_model} is usually uncased; consider --do-lower-case.")
        if expected == "cased" and args.do_lower_case:
            warnings.append(f"{args.bert_model} is usually cased; --do-lower-case may corrupt casing.")
    if config and "vocab_size" in config and config["vocab_size"] != len(vocab):
        warnings.append(f"Config vocab_size={config['vocab_size']} does not match vocab size={len(vocab)}.")
    if args.max_len and sample_tokens is not None and len(sample_tokens) > args.max_len:
        warnings.append(f"Sample token length {len(sample_tokens)} exceeds --max-len {args.max_len}.")
    if args.tokenized_input and sample_tokens:
        missing_input_tokens = [token for token, token_id in zip(sample_tokens, sample_ids or []) if token_id is None]
        if missing_input_tokens:
            warnings.append("Tokenized input contains tokens missing from vocab: " + ", ".join(missing_input_tokens[:10]))
    return {
        "vocab_file": os.path.basename(args.vocab_file),
        "vocab_size": len(vocab),
        "case": detect_case(vocab),
        "bert_model_hint": args.bert_model,
        "model_hint": model_hint,
        "config": config_summary(config),
        "special_tokens": special,
        "s2s_tokens": s2s,
        "missing_special_tokens": missing_special,
        "missing_s2s_tokens": missing_s2s,
        "sample_tokens": sample_tokens,
        "sample_token_ids": sample_ids,
        "sample_unknown_count": unknown_count,
        "warnings": warnings,
        "remapping_notes": remapping_notes(special, s2s) if args.show_remappings else [],
    }


def remapping_notes(special: dict[str, int | None], s2s: dict[str, int | None]) -> list[str]:
    notes: list[str] = []
    if s2s.get("[S2S_CLS]") is not None and special.get("[CLS]") is not None:
        notes.append("[S2S_CLS] is available; UniLM S2S source prefix can be distinct from [CLS].")
    elif special.get("[CLS]") is not None:
        notes.append("[S2S_CLS] is absent; do not enable S2S special-token mode unless checkpoint/vocab were extended.")
    if s2s.get("[S2S_SEP]") is not None and special.get("[SEP]") is not None:
        notes.append("[S2S_SEP] is available; source/target separator can be distinct from [SEP].")
    elif special.get("[SEP]") is not None:
        notes.append("[S2S_SEP] is absent; standard [SEP] separation is the safer legacy default.")
    if s2s.get("[S2S_SOS]") is not None:
        notes.append("[S2S_SOS] is available for legacy decoder start-of-sequence mode.")
    else:
        notes.append("[S2S_SOS] is absent; legacy decoder modes requiring it will fail with a tokenizer KeyError.")
    return notes


def print_human(report: dict[str, object]) -> None:
    print("Legacy tokenizer inspection")
    print(f"vocab file: {report['vocab_file']}")
    print(f"vocab size: {report['vocab_size']}")
    case = report["case"]
    print(f"likely case: {case['likely_case']} (uppercase tokens: {case['has_uppercase_tokens']})")
    if report.get("bert_model_hint"):
        print(f"bert model hint: {report['bert_model_hint']}")
    if report.get("config"):
        print("config:")
        for key, value in report["config"].items():
            print(f"  {key}: {value}")
    print("special tokens:")
    for token, token_id in report["special_tokens"].items():
        value = "missing" if token_id is None else str(token_id)
        print(f"  {token}: {value}")
    print("s2s special tokens:")
    for token, token_id in report["s2s_tokens"].items():
        value = "missing" if token_id is None else str(token_id)
        print(f"  {token}: {value}")
    if report.get("sample_tokens") is not None:
        print("sample tokenization:")
        print("  tokens: " + " ".join(report["sample_tokens"]))
        print("  ids: " + " ".join("None" if idx is None else str(idx) for idx in report["sample_token_ids"]))
        print(f"  unknown_or_missing_count: {report['sample_unknown_count']}")
    if report.get("remapping_notes"):
        print("remapping notes:")
        for note in report["remapping_notes"]:
            print(f"  - {note}")
    if report["warnings"]:
        print("warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main(argv: list[str] | None = None) -> int:
    argp = parser()
    args = argp.parse_args(argv)
    try:
        report = build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"inspect_legacy_tokenizers.py: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
