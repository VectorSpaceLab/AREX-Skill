#!/usr/bin/env python3
"""Bundled PageIndex CLI wrapper.

This adapts the repository's public document-structure workflow into a
self-contained skill helper. It assumes the `pageindex` package is importable
from the active Python environment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from pageindex import md_to_tree, page_index
from pageindex.utils import ConfigLoader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process a PDF or Markdown document and generate a PageIndex structure")
    parser.add_argument("--pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("--md_path", type=str, help="Path to the Markdown file")
    parser.add_argument("--flash", action="store_true", help="Use PageIndex Flash with --pdf_path")
    parser.add_argument("--embedded-toc", action=argparse.BooleanOptionalAction, default=None,
                        help="Use the PDF's embedded bookmarks when trustworthy (default: on with --flash)")
    parser.add_argument("--summary", action=argparse.BooleanOptionalAction, default=None,
                        help="Generate node summaries with an LLM (default: on with --flash)")
    parser.add_argument("--optimize", nargs="?", const="full", choices=["full", "merge"], default=None,
                        help="Refine the tree for search cost; `merge` is deterministic, `full` also expands with an LLM")
    parser.add_argument("--model", type=str, default=None, help="Model to use (overrides config defaults)")
    parser.add_argument("--summary-model", type=str, default=None,
                        help="Model for Flash node summaries (defaults to --model, then config defaults)")
    parser.add_argument("--toc-check-pages", type=int, default=None,
                        help="Number of pages to check for table of contents (classic PDF only)")
    parser.add_argument("--max-pages-per-node", type=int, default=None,
                        help="Maximum pages per node before recursive splitting (classic PDF only)")
    parser.add_argument("--max-tokens-per-node", type=int, default=None,
                        help="Maximum tokens per node before recursive splitting (classic PDF only)")
    parser.add_argument("--if-add-node-id", type=str, default=None,
                        help="Whether to add node id to the output nodes")
    parser.add_argument("--if-add-node-summary", type=str, default=None,
                        help="Whether to add node summaries")
    parser.add_argument("--if-add-doc-description", type=str, default=None,
                        help="Whether to add a document description")
    parser.add_argument("--if-add-node-text", type=str, default=None,
                        help="Whether to retain source text inside nodes")
    parser.add_argument("--if-thinning", type=str, default="no",
                        help="Whether to apply tree thinning for Markdown")
    parser.add_argument("--thinning-threshold", type=int, default=5000,
                        help="Minimum token threshold for Markdown thinning")
    parser.add_argument("--summary-token-threshold", type=int, default=200,
                        help="Token threshold for Markdown summary generation")
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if not args.pdf_path and not args.md_path:
        raise ValueError("Either --pdf_path or --md_path must be specified")
    if args.pdf_path and args.md_path:
        raise ValueError("Only one of --pdf_path or --md_path can be specified")
    if args.optimize and not (args.pdf_path and args.flash):
        raise ValueError("--optimize requires --flash with --pdf_path")
    if args.embedded_toc is not None and not (args.pdf_path and args.flash):
        raise ValueError("--embedded-toc requires --flash with --pdf_path")
    if args.summary is not None and not (args.pdf_path and args.flash):
        raise ValueError("--summary requires --flash with --pdf_path")


def _write_result(name: str, suffix: str, result: dict) -> Path:
    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}{suffix}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def _run_pdf(args: argparse.Namespace) -> Path:
    pdf_path = Path(args.pdf_path)
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("PDF file must have .pdf extension")
    if not pdf_path.is_file():
        raise ValueError(f"PDF file not found: {pdf_path}")

    if args.flash:
        from pageindex.flash import page_index_flash
        if args.optimize == "full":
            from pageindex.tree_optimize import default_model
            from pageindex.utils import _is_openai_model
            expand_model = args.model or default_model()
            if _is_openai_model(expand_model) and not os.getenv("OPENAI_API_KEY"):
                raise SystemExit(f"OPENAI_API_KEY is not set (expand model: {expand_model}).")
        result = page_index_flash(
            str(pdf_path),
            optimize=args.optimize is not None,
            optimize_expand=args.optimize == "full",
            optimize_model=args.model,
            summary_model=args.summary_model or args.model,
            use_embedded_toc=args.embedded_toc if args.embedded_toc is not None else True,
            summary=args.summary if args.summary is not None else True,
        )
        if "optimize" in result:
            opt = result["optimize"]
            print(
                f"Optimize: merges={opt['merges']} expands={opt['expands']}, "
                f"worst-case search cost "
                f"{opt['before'].get('worst_case_search_complexity')} -> "
                f"{opt['after'].get('worst_case_search_complexity')} pages"
            )
        suffix = "_structure_flash"
    else:
        result = page_index(
            str(pdf_path),
            model=args.model,
            toc_check_page_num=args.toc_check_pages,
            max_page_num_each_node=args.max_pages_per_node,
            max_token_num_each_node=args.max_tokens_per_node,
            if_add_node_id=args.if_add_node_id,
            if_add_node_summary=args.if_add_node_summary,
            if_add_doc_description=args.if_add_doc_description,
            if_add_node_text=args.if_add_node_text,
        )
        suffix = "_structure"

    return _write_result(pdf_path.stem, suffix, result)


def _run_markdown(args: argparse.Namespace) -> Path:
    md_path = Path(args.md_path)
    if md_path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError("Markdown file must have .md or .markdown extension")
    if not md_path.is_file():
        raise ValueError(f"Markdown file not found: {md_path}")

    opt = ConfigLoader().load({
        key: value for key, value in {
            "model": args.model,
            "if_add_node_summary": args.if_add_node_summary,
            "if_add_doc_description": args.if_add_doc_description,
            "if_add_node_text": args.if_add_node_text,
            "if_add_node_id": args.if_add_node_id,
        }.items() if value is not None
    })

    result = asyncio.run(md_to_tree(
        md_path=str(md_path),
        if_thinning=args.if_thinning.lower() == "yes",
        min_token_threshold=args.thinning_threshold,
        if_add_node_summary=opt.if_add_node_summary,
        summary_token_threshold=args.summary_token_threshold,
        model=opt.model,
        if_add_doc_description=opt.if_add_doc_description,
        if_add_node_text=opt.if_add_node_text,
        if_add_node_id=opt.if_add_node_id,
    ))
    return _write_result(md_path.stem, "_structure", result)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _validate_args(args)
    print("Parsing document...")
    out_path = _run_pdf(args) if args.pdf_path else _run_markdown(args)
    print(f"Tree structure saved to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
