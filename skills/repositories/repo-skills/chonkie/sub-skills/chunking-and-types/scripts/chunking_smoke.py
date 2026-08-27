#!/usr/bin/env python3
"""Safe deterministic Chonkie chunking smoke.

This script imports the installed ``chonkie`` package, exercises deterministic
TokenChunker/RecursiveChunker/SentenceChunker paths, and optionally checks table
and code chunkers when their dependencies are present without requiring network,
credentials, or original repository files.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any


DEFAULT_TEXT = (
    "Chonkie chunks text for retrieval. "
    "Recursive rules preserve paragraphs and sentence boundaries. "
    "Token windows are useful when a model requires a hard limit.\n\n"
    "Tables and code often need specialized chunkers. "
    "Use deterministic chunkers first, then add model-dependent chunking only when the runtime is ready."
)

TABLE_TEXT = """| item | qty |
|---|---|
| tea | 2 |
| rice | 1 |
| beans | 4 |
| oats | 3 |
"""

CODE_TEXT = """def add(a, b):
    return a + b

class Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        self.value += 1
        return self.value
"""


@dataclass
class CheckResult:
    name: str
    status: str
    details: str


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def nonnegative_int(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return value


def assert_basic_chunks(name: str, chunks: list[Any], original: str, chunk_size: int | None = None) -> None:
    assert isinstance(chunks, list), f"{name} did not return a list"
    assert chunks, f"{name} returned no chunks"
    for i, chunk in enumerate(chunks):
        assert hasattr(chunk, "text"), f"{name} chunk {i} has no text field"
        assert isinstance(chunk.text, str) and chunk.text, f"{name} chunk {i} has empty text"
        assert hasattr(chunk, "start_index") and hasattr(chunk, "end_index"), (
            f"{name} chunk {i} is missing offsets"
        )
        assert 0 <= chunk.start_index <= chunk.end_index <= len(original), (
            f"{name} chunk {i} offsets out of range: {chunk.start_index}:{chunk.end_index}"
        )
        assert hasattr(chunk, "token_count"), f"{name} chunk {i} has no token_count"
        if chunk_size is not None:
            assert chunk.token_count <= chunk_size, (
                f"{name} chunk {i} token_count={chunk.token_count} exceeds {chunk_size}"
            )


def run_core_smokes(chonkie: Any, text: str, tokenizer: str, chunk_size: int, overlap: int) -> list[CheckResult]:
    results: list[CheckResult] = []

    token_overlap = min(overlap, max(0, chunk_size - 1))
    token_chunker = chonkie.TokenChunker(
        tokenizer=tokenizer,
        chunk_size=chunk_size,
        chunk_overlap=token_overlap,
    )
    token_chunks = token_chunker.chunk(text)
    assert_basic_chunks("TokenChunker", token_chunks, text, chunk_size)
    if tokenizer == "character":
        for i, chunk in enumerate(token_chunks):
            assert text[chunk.start_index : chunk.end_index] == chunk.text, (
                f"TokenChunker chunk {i} offsets do not map to original text"
            )
    results.append(CheckResult("TokenChunker", "passed", f"{len(token_chunks)} chunks"))

    recursive_chunker = chonkie.RecursiveChunker(
        tokenizer=tokenizer,
        chunk_size=chunk_size,
        min_characters_per_chunk=max(1, min(24, chunk_size // 4)),
    )
    recursive_chunks = recursive_chunker.chunk(text)
    assert_basic_chunks("RecursiveChunker", recursive_chunks, text, None)
    if tokenizer == "character":
        reconstructed = "".join(chunk.text for chunk in recursive_chunks)
        assert reconstructed == text, "RecursiveChunker chunks do not reconstruct original text"
    results.append(CheckResult("RecursiveChunker", "passed", f"{len(recursive_chunks)} chunks"))

    sentence_chunker = chonkie.SentenceChunker(
        tokenizer=tokenizer,
        chunk_size=chunk_size,
        chunk_overlap=0,
        min_sentences_per_chunk=1,
        min_characters_per_sentence=5,
        delim=[". ", "! ", "? ", "\n"],
        include_delim="prev",
    )
    sentence_chunks = sentence_chunker.chunk(text)
    assert_basic_chunks("SentenceChunker", sentence_chunks, text, None)
    results.append(CheckResult("SentenceChunker", "passed", f"{len(sentence_chunks)} chunks"))

    return results


def run_table_smoke(chonkie: Any, row_chunk_size: int) -> CheckResult:
    table_chunker = chonkie.TableChunker(chunk_size=row_chunk_size)
    chunks = table_chunker.chunk(TABLE_TEXT)
    assert_basic_chunks("TableChunker", chunks, TABLE_TEXT, None)
    assert len(chunks) >= 2, "TableChunker should split the sample table with the selected row chunk size"
    for i, chunk in enumerate(chunks):
        assert "| item | qty |" in chunk.text, f"TableChunker chunk {i} did not preserve header"
        assert "|---|---|" in chunk.text, f"TableChunker chunk {i} did not preserve separator"
        assert chunk.token_count <= row_chunk_size, (
            f"TableChunker chunk {i} row token_count={chunk.token_count} exceeds {row_chunk_size}"
        )
    return CheckResult("TableChunker", "passed", f"{len(chunks)} chunks")


def code_cache_ready() -> tuple[bool, str]:
    try:
        pack = import_module("tree_sitter_language_pack")
    except Exception as exc:  # optional dependency may be absent
        return False, f"tree_sitter_language_pack unavailable: {exc}"

    try:
        downloaded = list(pack.downloaded_languages())
        has_python = bool(pack.has_language("python"))
    except Exception as exc:
        return False, f"could not inspect language cache: {exc}"

    # CodeChunker's constructor may call download_all() when the cache is small.
    # Treat a large existing cache plus python grammar as safe for a no-network smoke.
    if has_python and len(downloaded) > 19:
        return True, f"python grammar cached; {len(downloaded)} downloaded languages"
    return False, (
        f"python grammar cached={has_python}, downloaded_languages={len(downloaded)}; "
        "skipping to avoid implicit grammar download"
    )


def run_code_smoke(chonkie: Any, chunk_size: int, allow_code_download: bool) -> CheckResult:
    ready, reason = code_cache_ready()
    if not ready and not allow_code_download:
        return CheckResult("CodeChunker", "skipped", reason)

    chunker = chonkie.CodeChunker(language="python", chunk_size=chunk_size)
    chunks = chunker.chunk(CODE_TEXT)
    assert_basic_chunks("CodeChunker", chunks, CODE_TEXT, None)
    reconstructed = "".join(chunk.text for chunk in chunks)
    assert reconstructed == CODE_TEXT, "CodeChunker chunks do not reconstruct original code"
    return CheckResult("CodeChunker", "passed", f"{len(chunks)} chunks")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe deterministic smoke for installed Chonkie chunking APIs.",
    )
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Input text for core chunker smokes.")
    parser.add_argument(
        "--repeat",
        type=positive_int,
        default=1,
        help="Repeat --text this many times to create a longer input.",
    )
    parser.add_argument(
        "--tokenizer",
        default="character",
        help="Tokenizer string to pass to deterministic text chunkers (default: character).",
    )
    parser.add_argument(
        "--chunk-size",
        type=positive_int,
        default=96,
        help="Positive chunk size for core text chunkers.",
    )
    parser.add_argument(
        "--overlap",
        type=nonnegative_int,
        default=0,
        help="Non-negative TokenChunker overlap; clamped below chunk-size.",
    )
    parser.add_argument(
        "--table-row-size",
        type=positive_int,
        default=2,
        help="Row chunk size for the optional TableChunker smoke.",
    )
    parser.add_argument(
        "--table",
        choices=["auto", "yes", "no"],
        default="auto",
        help="Run TableChunker smoke when available (default: auto).",
    )
    parser.add_argument(
        "--code",
        choices=["auto", "yes", "no"],
        default="auto",
        help="Run CodeChunker smoke when dependencies and grammar cache are ready (default: auto).",
    )
    parser.add_argument(
        "--allow-code-download",
        action="store_true",
        help="Permit CodeChunker initialization even if it may initialize/download grammars.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON results.")
    parser.add_argument("--quiet", action="store_true", help="Suppress passed/skipped lines unless JSON is used.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results: list[CheckResult] = []

    try:
        try:
            dist_version = version("chonkie")
        except PackageNotFoundError as exc:
            raise AssertionError("installed distribution 'chonkie' was not found") from exc

        chonkie = import_module("chonkie")
        package_version = getattr(chonkie, "__version__", "unknown")
        results.append(
            CheckResult(
                "import",
                "passed",
                f"distribution={dist_version}; package_version={package_version}",
            )
        )

        text = (args.text + " ") * args.repeat
        text = text.rstrip()
        assert text.strip(), "input text must not be empty"

        results.extend(run_core_smokes(chonkie, text, args.tokenizer, args.chunk_size, args.overlap))

        if args.table != "no":
            if hasattr(chonkie, "TableChunker"):
                results.append(run_table_smoke(chonkie, args.table_row_size))
            elif args.table == "yes":
                raise AssertionError("TableChunker is not exported by installed chonkie")
            else:
                results.append(CheckResult("TableChunker", "skipped", "not exported"))

        if args.code != "no":
            if hasattr(chonkie, "CodeChunker"):
                code_result = run_code_smoke(chonkie, args.chunk_size, args.allow_code_download)
                if args.code == "yes" and code_result.status == "skipped":
                    raise AssertionError(code_result.details)
                results.append(code_result)
            elif args.code == "yes":
                raise AssertionError("CodeChunker is not exported by installed chonkie")
            else:
                results.append(CheckResult("CodeChunker", "skipped", "not exported"))

    except AssertionError as exc:
        results.append(CheckResult("assertion", "failed", str(exc)))
        if args.json:
            print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
        else:
            for result in results:
                print(f"[{result.status}] {result.name}: {result.details}", file=sys.stderr)
        return 1
    except Exception as exc:
        results.append(CheckResult(type(exc).__name__, "failed", str(exc)))
        if args.json:
            print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
        else:
            for result in results:
                print(f"[{result.status}] {result.name}: {result.details}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    elif not args.quiet:
        for result in results:
            print(f"[{result.status}] {result.name}: {result.details}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
