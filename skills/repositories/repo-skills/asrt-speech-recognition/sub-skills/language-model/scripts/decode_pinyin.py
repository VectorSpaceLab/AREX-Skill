#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone ASRT pinyin-to-Chinese decoder.

This helper is adapted from ASRT's statistical language-model implementation
and bundles the minimal file parsing needed to run without the original source
checkout or ASRT utility imports.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DICT = SKILL_DIR / "dict.txt"
DEFAULT_MODEL_DIR = SKILL_DIR / "language_model"


def _load_symbol_dict(path: Path) -> dict[str, list[str]]:
    if not path.is_file():
        raise FileNotFoundError(f"pinyin dictionary not found: {path}")
    result: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            if "\t" not in line:
                raise ValueError(f"bad dictionary line {line_number}: expected pinyin<TAB>characters")
            pinyin, chars = line.split("\t", 1)
            result[pinyin] = list(chars)
    return result


def _load_language_model(path: Path) -> dict[str, int]:
    if not path.is_file():
        raise FileNotFoundError(f"language model count file not found: {path}")
    result: dict[str, int] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            if "\t" not in line:
                # ASRT count files use the first no-tab line for a corpus total;
                # the decoder does not use that value.
                if line_number == 1:
                    continue
                raise ValueError(f"bad count line {line_number} in {path.name}: expected key<TAB>count")
            key, value = line.rsplit("\t", 1)
            result[key] = int(value)
    return result


class ModelLanguage:
    """ASRT-style N-gram pinyin-to-Chinese language model."""

    def __init__(self, model_path: str, dict_path: Optional[str] = None):
        self.model_path = Path(model_path)
        self.dict_path = Path(dict_path) if dict_path is not None else Path("dict.txt")
        self.dict_pinyin: dict[str, list[str]] = {}
        self.model1: dict[str, int] = {}
        self.model2: dict[str, int] = {}

    def load_model(self):
        """Load the pinyin dictionary plus unigram and bigram count files."""
        self.dict_pinyin = _load_symbol_dict(self.dict_path)
        self.model1 = _load_language_model(self.model_path / "language_model1.txt")
        self.model2 = _load_language_model(self.model_path / "language_model2.txt")
        return self.dict_pinyin, self.model1, self.model2

    def pinyin_to_text(self, list_pinyin: list, beam_size: int = 100) -> str:
        """Decode a complete pinyin token list to Chinese text."""
        result = []
        tmp_result_last = []
        for item_pinyin in list_pinyin:
            tmp_result = self.pinyin_stream_decode(tmp_result_last, item_pinyin, beam_size)
            if len(tmp_result) == 0 and len(tmp_result_last) > 0:
                result.append(tmp_result_last[0][0])
                tmp_result = self.pinyin_stream_decode([], item_pinyin, beam_size)
                if len(tmp_result) > 0:
                    result.append(tmp_result[0][0])
                tmp_result = []
            tmp_result_last = tmp_result

        if len(tmp_result_last) > 0:
            result.append(tmp_result_last[0][0])

        return "".join(result)

    def pinyin_stream_decode(self, temple_result: list, item_pinyin: str, beam_size: int = 100) -> list:
        """Decode one pinyin token and return intermediate candidate states."""
        if item_pinyin not in self.dict_pinyin:
            return []

        cur_words = self.dict_pinyin[item_pinyin]
        if len(temple_result) == 0:
            return [[word, 1.0] for word in cur_words]

        new_result = []
        for sequence in temple_result:
            for cur_word in cur_words:
                tuple2_word = sequence[0][-1] + cur_word
                if tuple2_word not in self.model2:
                    continue
                prob_origin = sequence[1]
                count_two_word = float(self.model2[tuple2_word])
                count_one_word = float(self.model1[tuple2_word[-2]])
                cur_probability = prob_origin * count_two_word / count_one_word
                new_result.append([sequence[0] + cur_word, cur_probability])

        new_result = sorted(new_result, key=lambda x: x[1], reverse=True)
        if len(new_result) > beam_size:
            return new_result[0:beam_size]
        return new_result


def _read_pinyin_tokens(args: argparse.Namespace) -> list[str]:
    if args.pinyin and not args.stdin:
        return args.pinyin
    data = sys.stdin.read()
    tokens = data.split()
    if args.pinyin:
        tokens.extend(args.pinyin)
    return tokens


def _split_chunks(tokens: Sequence[str], separator: str) -> list[list[str]]:
    chunks: list[list[str]] = [[]]
    for token in tokens:
        if token == separator:
            chunks.append([])
        else:
            chunks[-1].append(token)
    return chunks


def _flatten_without_separator(tokens: Iterable[str], separator: str) -> list[str]:
    return [token for token in tokens if token != separator]


def _print_diagnostics(model: ModelLanguage, tokens: Sequence[str], separator: str) -> None:
    unknown = []
    for token in tokens:
        if token == separator:
            continue
        if token not in model.dict_pinyin and token not in unknown:
            unknown.append(token)
    if unknown:
        print("Unknown pinyin tokens: " + ", ".join(unknown), file=sys.stderr)
    else:
        print("All pinyin tokens are present in dict.txt", file=sys.stderr)


def _stream_events(model: ModelLanguage, chunks: Sequence[Sequence[str]], beam_size: int):
    committed: list[str] = []
    state: list = []
    for chunk_index, chunk in enumerate(chunks):
        for item_pinyin in chunk:
            next_state = model.pinyin_stream_decode(state, item_pinyin, beam_size)
            if len(next_state) == 0 and len(state) > 0:
                committed_text = state[0][0]
                committed.append(committed_text)
                yield {
                    "event": "flush",
                    "chunk": chunk_index,
                    "pinyin": item_pinyin,
                    "committed": committed_text,
                    "text": "".join(committed),
                }
                next_state = model.pinyin_stream_decode([], item_pinyin, beam_size)
            state = next_state
            if len(state) > 0:
                yield {
                    "event": "partial",
                    "chunk": chunk_index,
                    "pinyin": item_pinyin,
                    "partial": state[0][0],
                    "candidate_count": len(state),
                    "score": state[0][1],
                }
            else:
                yield {
                    "event": "empty",
                    "chunk": chunk_index,
                    "pinyin": item_pinyin,
                    "partial": "",
                    "candidate_count": 0,
                }
        yield {
            "event": "chunk_end",
            "chunk": chunk_index,
            "partial": state[0][0] if state else "",
            "candidate_count": len(state),
        }
    if len(state) > 0:
        committed_text = state[0][0]
        committed.append(committed_text)
        yield {"event": "final", "committed": committed_text, "text": "".join(committed)}
    else:
        yield {"event": "final", "committed": "", "text": "".join(committed)}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decode ASRT tone-number pinyin tokens to Chinese text using bundled unigram/bigram counts."
    )
    parser.add_argument("pinyin", nargs="*", help="pinyin tokens such as ni3 hao3 ya5; use / as a stream chunk separator")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR), help="directory containing language_model1.txt and language_model2.txt")
    parser.add_argument("--dict", dest="dict_path", default=str(DEFAULT_DICT), help="path to ASRT dict.txt pinyin dictionary")
    parser.add_argument("--beam-size", type=int, default=100, help="candidate beam size after each bigram extension (default: 100)")
    parser.add_argument("--stdin", action="store_true", help="read pinyin tokens from standard input; positional tokens are appended")
    parser.add_argument("--diagnose", action="store_true", help="print unknown-token diagnostics to stderr before decoding")
    parser.add_argument("--stream", action="store_true", help="emit JSON Lines showing streaming state across tokens and / chunk separators")
    parser.add_argument("--chunk-separator", default="/", help="token used to split stream chunks for --stream (default: /)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.beam_size < 1:
        parser.error("--beam-size must be a positive integer")

    tokens = _read_pinyin_tokens(args)
    if not tokens:
        parser.error("provide pinyin tokens as arguments or via --stdin")

    model = ModelLanguage(args.model_dir, dict_path=args.dict_path)
    model.load_model()

    if args.diagnose:
        _print_diagnostics(model, tokens, args.chunk_separator)

    if args.stream:
        chunks = _split_chunks(tokens, args.chunk_separator)
        for event in _stream_events(model, chunks, args.beam_size):
            print(json.dumps(event, ensure_ascii=False))
    else:
        sequence = _flatten_without_separator(tokens, args.chunk_separator)
        print(model.pinyin_to_text(sequence, beam_size=args.beam_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
