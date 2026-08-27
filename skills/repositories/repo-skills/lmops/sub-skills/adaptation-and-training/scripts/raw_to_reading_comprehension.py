#!/usr/bin/env python3
"""Tiny, self-contained corpus transformer distilled from AdaptLLM ideas.

The script is intentionally conservative:
- stdlib only
- no repository imports
- no model downloads
- safe fixture generation for offline checks

It turns plain raw text files into a small reading-comprehension style bundle.
Each output record keeps the title/context split explicit and emits a few
traceable question-answer pairs instead of trying to mimic the full paper-scale
mining pipeline.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Tuple

DOMAIN_CHOICES = ("biomedicine", "finance", "law", "general")
DEFAULT_FIXTURE = {
    "biomedicine_seed.txt": (
        "Clinical domain note\n"
        "A clinic study describes a simple treatment pattern. The report mentions follow-up care,"
        " a clear improvement, and one caution about dosage. The goal is to preserve the facts"
        " while rewriting them into a compact reading-comprehension form."
    ),
    "finance_seed.txt": (
        "Market comment\n"
        "A financial memo says the portfolio improved after risk limits were tightened. It notes"
        " that the team reduced volatility, kept the strategy simple, and documented the result"
        " for downstream review."
    ),
}


@dataclass
class DocumentResult:
    source_name: str
    domain: str
    title: str
    sentence_count: int
    qa_count: int
    output_name: str


def _clean_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def _split_title_context(text: str) -> Tuple[str, str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return "Untitled", ""

    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    if len(lines) >= 2:
        return lines[0], "\n".join(lines[1:]).strip()

    parts = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    if len(parts) == 2 and parts[0].strip():
        return parts[0].strip(), parts[1].strip()

    return "Untitled", cleaned


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    chunks = re.split(r"(?<=[.!?])\s+", _clean_text(text))
    sentences = [chunk.strip() for chunk in chunks if chunk.strip()]
    return sentences


def _truncate(sentence: str, limit: int = 220) -> str:
    sentence = sentence.strip()
    if len(sentence) <= limit:
        return sentence
    return sentence[: limit - 1].rstrip() + "…"


def _summarize(sentences: List[str]) -> str:
    if not sentences:
        return "No context was supplied."
    if len(sentences) == 1:
        return _truncate(sentences[0], 220)
    return _truncate(" ".join(sentences[:2]), 260)


def _build_qas(domain: str, title: str, sentences: List[str], max_qa: int) -> List[Tuple[str, str]]:
    qas: List[Tuple[str, str]] = []
    qas.append(("What domain does this reading material belong to?", domain))
    if title:
        qas.append(("What is the title of the passage?", title))
    if sentences:
        qas.append(("What is the main idea in one short sentence?", _summarize(sentences)))
    if len(sentences) >= 2:
        qas.append(("What is one detail from the second sentence?", _truncate(sentences[1], 180)))
    if len(sentences) >= 3:
        qas.append(("Which sentence adds an extra supporting detail?", _truncate(sentences[2], 180)))

    if not qas:
        qas.append(("What type of document is this?", "raw text"))

    return qas[:max_qa]


def _render_document(domain: str, title: str, context: str, qas: List[Tuple[str, str]]) -> str:
    lines = [
        "<READING>",
        f"Domain: {domain}",
        f"Title: {title}",
        "Context:",
        context.strip() or "[empty context]",
        "</READING>",
        "",
        "<COMPREHENSION>",
    ]
    for idx, (question, answer) in enumerate(qas, start=1):
        lines.append(f"Q{idx}: {question}")
        lines.append(f"A{idx}: {answer}")
    lines.append("</COMPREHENSION>")
    return "\n".join(lines) + "\n"


def _iter_inputs(input_dir: Path | None, input_file: Path | None) -> Iterable[Path]:
    if input_file is not None:
        yield input_file
        return
    assert input_dir is not None
    for path in sorted(input_dir.iterdir()):
        if path.is_file():
            yield path


def _load_document(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _is_placeholder_path(value: str | None) -> bool:
    if value is None:
        return True
    lowered = value.strip().lower()
    return not lowered or any(token in lowered for token in ("<", ">", "todo", "replace", "path/to", "???"))


def _make_fixture(root: Path, domain: str) -> Path:
    raw_dir = root / "input-raw-texts"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, content in DEFAULT_FIXTURE.items():
        path = raw_dir / name
        path.write_text(content, encoding="utf-8")
        manifest.append({"file": name, "domain": domain})
    (root / "fixture-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return raw_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, help="Directory containing raw text files.")
    parser.add_argument("--input-file", type=Path, help="Single raw text file to transform.")
    parser.add_argument("--output-dir", type=Path, help="Directory for rendered outputs.")
    parser.add_argument("--domain-name", type=str, default="general", choices=DOMAIN_CHOICES)
    parser.add_argument("--max-qa", type=int, default=4)
    parser.add_argument("--min-sentence-chars", type=int, default=30)
    parser.add_argument("--max-context-chars", type=int, default=2400)
    parser.add_argument("--output-jsonl", type=Path, help="Optional JSONL summary file.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    parser.add_argument("--dry-run", action="store_true", help="Show the plan without writing outputs.")
    parser.add_argument("--create-fixture", type=Path, help="Write a tiny raw-text fixture and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.create_fixture is not None:
        fixture_root = args.create_fixture
        raw_dir = _make_fixture(fixture_root, args.domain_name)
        print(json.dumps({
            "fixture_root": str(fixture_root),
            "raw_dir": str(raw_dir),
            "next_step": "run this script again with --input-dir pointing at the fixture raw directory",
        }, indent=2))
        return 0

    if args.input_dir is None and args.input_file is None:
        print("error: provide either --input-dir or --input-file, or use --create-fixture", file=sys.stderr)
        return 2
    if args.input_dir is not None and args.input_file is not None:
        print("error: use only one of --input-dir or --input-file", file=sys.stderr)
        return 2
    if _is_placeholder_path(str(args.input_dir) if args.input_dir is not None else None) and args.input_file is None:
        print("error: input path looks like a placeholder", file=sys.stderr)
        return 2
    if args.output_dir is None and not args.dry_run:
        print("error: provide --output-dir unless you are using --dry-run", file=sys.stderr)
        return 2

    inputs = list(_iter_inputs(args.input_dir, args.input_file))
    if not inputs:
        print("error: no input files were found", file=sys.stderr)
        return 2

    results: List[DocumentResult] = []
    rendered_records = []
    for source_path in inputs:
        raw = _load_document(source_path)
        title, context = _split_title_context(raw)
        context = context[: args.max_context_chars]
        sentences = [s for s in _split_sentences(context) if len(s) >= args.min_sentence_chars]
        qas = _build_qas(args.domain_name, title, sentences, args.max_qa)
        rendered = _render_document(args.domain_name, title, context, qas)
        out_name = f"{source_path.stem}.readcompre.txt"
        rendered_records.append((out_name, rendered))
        results.append(DocumentResult(
            source_name=source_path.name,
            domain=args.domain_name,
            title=title,
            sentence_count=len(sentences),
            qa_count=len(qas),
            output_name=out_name,
        ))

    if args.dry_run:
        print(json.dumps([asdict(result) for result in results], indent=2))
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.output_jsonl is not None:
        args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.output_jsonl.open("w", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")

    for output_name, rendered in rendered_records:
        output_path = args.output_dir / output_name
        if output_path.exists() and not args.overwrite:
            print(f"error: output already exists: {output_path}", file=sys.stderr)
            return 2
        output_path.write_text(rendered, encoding="utf-8")

    print(json.dumps({
        "written": [result.output_name for result in results],
        "output_dir": str(args.output_dir),
        "domain": args.domain_name,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
