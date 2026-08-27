#!/usr/bin/env python3
"""
Generate safe txtai RAG templates without downloading models.

This helper adapts the public RAG quickstart into a dry-run/template generator. It
prints or writes a Python template showing how to build a content-enabled
Embeddings store and RAG pipeline, then validates placeholders and config shape.
It does not import txtai, scan data directories, load models, call network
services, or execute generation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
DEFAULT_EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_LLM_MODEL = "ibm-granite/granite-4.0-350m"
DEFAULT_TEMPLATE = """\
Answer the following question using only the provided context.

Question:
{question}

Context:
{context}
"""


def build_template(
    embeddings_model: str,
    llm_model: str,
    output: str,
    context: int,
    minscore: float | None,
    gpu: bool,
) -> str:
    """Builds a standalone Python RAG template as text."""

    lines = [
        '"""',
        "txtai RAG template.",
        "",
        "Review the model paths, data source, and hardware flags before running.",
        "This file was generated as a starting point and may download models when",
        "executed in a real txtai environment.",
        '"""',
        "",
        "from txtai import Embeddings, RAG",
        "",
        "documents = [",
        '    ("doc-1", "Replace this text with content from your knowledge base."),',
        '    ("doc-2", "Use content=True so RAG and agent tools can read retrieved text."),',
        "]",
        "",
        "embeddings = Embeddings(",
        "    content=True,",
        f"    path={embeddings_model!r},",
        ")",
        "embeddings.index(documents)",
        "",
        f"template = {DEFAULT_TEMPLATE!r}",
        "",
        "rag = RAG(",
        "    embeddings,",
        f"    {llm_model!r},",
        "    template=template,",
        '    system="Answer only from the supplied context.",',
        f"    context={context!r},",
    ]

    if minscore is not None:
        lines.append(f"    minscore={minscore!r},")

    lines.append(f"    output={output!r},")

    if not gpu:
        lines.append("    gpu=False,")

    lines.extend(
        [
            ")",
            "",
            'question = "What should this RAG application answer?"',
            "answer = rag(question, maxlength=512, stripthink=True)",
            "print(answer)",
        ]
    )

    return "\n".join(lines) + "\n"


def validate_template(text: str) -> list[str]:
    """Returns validation errors for a generated RAG template."""

    errors = []
    if "{question}" not in text:
        errors.append("RAG prompt template must include {question}.")
    if "{context}" not in text:
        errors.append("RAG prompt template must include {context}.")
    if "content=True" not in text:
        errors.append("Embeddings should use content=True so retrieved rows include text.")
    if "RAG(" not in text:
        errors.append("Template should construct a txtai RAG pipeline.")
    return errors


def positive_int(value: str) -> int:
    """Parses a positive integer."""

    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return number


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Generate a safe txtai RAG Python template.")
    parser.add_argument("--embeddings-model", default=DEFAULT_EMBEDDINGS_MODEL, help="Embeddings model path for the generated template.")
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL, help="LLM model path for the generated template.")
    parser.add_argument("--output", choices=("default", "flatten", "reference"), default="flatten", help="RAG output mode.")
    parser.add_argument("--context", type=positive_int, default=3, help="Number of retrieved context rows to include.")
    parser.add_argument("--minscore", type=float, default=None, help="Optional minimum retrieval score.")
    parser.add_argument("--cpu", action="store_true", help="Add gpu=False to the generated RAG constructor.")
    parser.add_argument("--write-template", type=Path, help="Write the generated Python template to this path instead of stdout.")
    parser.add_argument("--check", action="store_true", help="Only validate the generated template and print a concise status line.")
    args = parser.parse_args(argv)

    template = build_template(
        embeddings_model=args.embeddings_model,
        llm_model=args.llm_model,
        output=args.output,
        context=args.context,
        minscore=args.minscore,
        gpu=not args.cpu,
    )

    errors = validate_template(template)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.check:
        destination = str(args.write_template) if args.write_template else "stdout"
        print(f"RAG template OK: output={args.output}, context={args.context}, destination={destination}")
        return 0

    if args.write_template:
        args.write_template.parent.mkdir(parents=True, exist_ok=True)
        args.write_template.write_text(template, encoding="utf-8")
        print(f"Wrote txtai RAG template to {args.write_template}")
    else:
        print(template, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
