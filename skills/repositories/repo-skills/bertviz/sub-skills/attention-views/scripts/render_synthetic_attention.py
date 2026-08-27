#!/usr/bin/env python3
"""Synthetic BertViz attention renderer and validator.

This helper builds deterministic, no-network attention tensors and exercises
bertviz.head_view and bertviz.model_view using html_action='return'. It is safe
for offline smoke tests, saved HTML workflows, and CWD-independent validation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple


def _fatal(message: str, exit_code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def _import_runtime():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment-specific
        _fatal("Missing dependency 'torch'. Install PyTorch before running this helper.")

    try:
        from bertviz import head_view, model_view
    except ImportError as exc:  # pragma: no cover - environment-specific
        _fatal(
            "Missing dependency 'bertviz' (or one of its notebook/display dependencies). "
            "Install bertviz and ensure IPython is available in the runtime."
        )

    return torch, head_view, model_view


def _make_attention_stack(torch, num_layers: int, num_heads: int, left_len: int, right_len: int):
    base = torch.arange(left_len * right_len, dtype=torch.float32).reshape(left_len, right_len)
    layers = []
    for layer_idx in range(num_layers):
        head_blocks = []
        for head_idx in range(num_heads):
            scores = base + (layer_idx * 0.17) + (head_idx * 0.11)
            head_blocks.append(torch.softmax(scores, dim=-1))
        layers.append(torch.stack(head_blocks, dim=0).unsqueeze(0))
    return layers


def _self_attention_case(torch):
    tokens = ["[CLS]", "ĠThe", "Ġcat", "Ġsat", "Ġon", "Ġthe", "Ġmat", "[SEP]"]
    attention = _make_attention_stack(torch, num_layers=3, num_heads=4, left_len=len(tokens), right_len=len(tokens))
    return {"tokens": tokens, "attention": attention}


def _encoder_decoder_case(torch):
    encoder_tokens = ["<s>", "▁She", "▁sees", "▁the", "▁small", "▁elephant", "</s>"]
    decoder_tokens = ["<s>", "▁Sie", "▁sieht", "▁den", "▁kleinen", "▁Elefanten", "</s>"]
    encoder_attention = _make_attention_stack(
        torch,
        num_layers=2,
        num_heads=3,
        left_len=len(encoder_tokens),
        right_len=len(encoder_tokens),
    )
    decoder_attention = _make_attention_stack(
        torch,
        num_layers=2,
        num_heads=3,
        left_len=len(decoder_tokens),
        right_len=len(decoder_tokens),
    )
    cross_attention = _make_attention_stack(
        torch,
        num_layers=2,
        num_heads=3,
        left_len=len(decoder_tokens),
        right_len=len(encoder_tokens),
    )
    return {
        "encoder_tokens": encoder_tokens,
        "decoder_tokens": decoder_tokens,
        "encoder_attention": encoder_attention,
        "decoder_attention": decoder_attention,
        "cross_attention": cross_attention,
    }


def _ensure_html(result, label: str) -> str:
    data = getattr(result, "data", None)
    if not isinstance(data, str) or not data.strip():
        _fatal(f"{label} did not return an HTML object with usable .data content.")
    if "<script" not in data or "<div" not in data:
        _fatal(f"{label} returned unexpected HTML content.")
    return data


def _render(renderer: Callable, kwargs: Dict, label: str, action: str, output_dir: Path | None) -> Path | None:
    try:
        result = renderer(html_action="return", **kwargs)
    except Exception as exc:  # pragma: no cover - BertViz validation path
        _fatal(f"{label} failed during BertViz rendering: {exc}")

    html_data = _ensure_html(result, label)

    if action == "validate":
        print(f"OK: {label} validated ({len(html_data)} HTML characters)")
        return None

    if output_dir is None:
        _fatal("An output directory is required when action is write-html.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{label}.html"
    output_path.write_text(html_data, encoding="utf-8")
    print(f"Wrote {output_path}")
    return output_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render synthetic BertViz attention views without downloading models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--view",
        choices=("head", "model", "both"),
        default="both",
        help="Which BertViz view(s) to render.",
    )
    parser.add_argument(
        "--encoder-decoder",
        action="store_true",
        help="Build encoder-attention, decoder-attention, and cross-attention tensors instead of self-attention tensors.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("attention-views-html"),
        help="Directory that receives HTML files when --action write-html is used.",
    )
    parser.add_argument(
        "--action",
        choices=("validate", "write-html"),
        default="validate",
        help="Validate returned HTML objects or write them to disk.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    torch, head_view, model_view = _import_runtime()

    output_dir = args.output_dir.expanduser()
    if args.action == "write-html":
        output_dir.mkdir(parents=True, exist_ok=True)

    selected_views = ("head", "model") if args.view == "both" else (args.view,)

    if args.encoder_decoder:
        case = _encoder_decoder_case(torch)
        kwargs = {
            "encoder_attention": case["encoder_attention"],
            "decoder_attention": case["decoder_attention"],
            "cross_attention": case["cross_attention"],
            "encoder_tokens": case["encoder_tokens"],
            "decoder_tokens": case["decoder_tokens"],
        }
        for view_name in selected_views:
            renderer = head_view if view_name == "head" else model_view
            label = f"{view_name}_encoder_decoder"
            _render(renderer, kwargs, label, args.action, output_dir if args.action == "write-html" else None)
    else:
        case = _self_attention_case(torch)
        kwargs = {"attention": case["attention"], "tokens": case["tokens"]}
        for view_name in selected_views:
            renderer = head_view if view_name == "head" else model_view
            _render(renderer, kwargs, view_name, args.action, output_dir if args.action == "write-html" else None)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
