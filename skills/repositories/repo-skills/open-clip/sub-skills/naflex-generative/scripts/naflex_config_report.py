#!/usr/bin/env python3
"""Validate and report NaFlex data-config settings without importing open_clip/timm/torch.

This is a safe planning helper for open_clip NaFlex runs. It mirrors the public
validation behavior of NaFlexDataConfig closely enough to catch common CLI
mistakes before launching data loading or model construction.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Iterable, Optional


PatchSize = tuple[int, int]


@dataclass(frozen=True)
class ReportConfig:
    train_patch_sizes: tuple[PatchSize, ...]
    train_patch_size_probs: Optional[tuple[float, ...]]
    train_seq_lens: tuple[int, ...]
    train_seq_len_probs: Optional[tuple[float, ...]]
    train_num_image_tokens: Optional[int]
    max_tokens_per_batch: int
    batch_divisor: int
    eval_patch_size: PatchSize
    eval_seq_len: int
    loss_scale: str


class ConfigError(ValueError):
    """User-facing validation failure."""


def parse_patch_size(value: str) -> PatchSize:
    text = value.lower().replace("*", "x").replace(",", "x")
    if "x" in text:
        parts = [part for part in text.split("x") if part]
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(f"patch size {value!r} must be N or HxW")
        try:
            height, width = (int(parts[0]), int(parts[1]))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"patch size {value!r} must contain integers") from exc
        return height, width
    try:
        size = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"patch size {value!r} must be an integer or HxW") from exc
    return size, size


def normalize_probs(values: Optional[Iterable[float]], expected_len: int, label: str) -> Optional[tuple[float, ...]]:
    if values is None:
        return None
    probs = tuple(float(value) for value in values)
    if len(probs) != expected_len:
        raise ConfigError(f"NaFlex {label} probabilities must match {label}s length.")
    if any(value < 0 for value in probs):
        raise ConfigError(f"NaFlex {label} probabilities must be non-negative.")
    total = float(sum(probs))
    if total <= 0:
        raise ConfigError(f"NaFlex {label} probabilities must sum to a positive value.")
    return tuple(value / total for value in probs)


def positive_int(value: Optional[int], message: str) -> Optional[int]:
    if value is None:
        return None
    value = int(value)
    if value <= 0:
        raise ConfigError(message)
    return value


def resolve_config(args: argparse.Namespace) -> ReportConfig:
    patch_sizes = tuple(args.patch_sizes or [(16, 16)])
    if not patch_sizes:
        raise ConfigError("NaFlex patch sizes must contain at least one value.")
    if any(height <= 0 or width <= 0 for height, width in patch_sizes):
        raise ConfigError("NaFlex patch sizes must be positive.")

    seq_lens = tuple(int(value) for value in (args.seq_lens or (128, 256, 576, 784, 1024)))
    if not seq_lens:
        raise ConfigError("NaFlex sequence lengths must contain at least one value.")
    if any(value <= 0 for value in seq_lens):
        raise ConfigError("NaFlex sequence lengths must be positive.")

    train_num_image_tokens = positive_int(
        args.train_num_image_tokens,
        "NaFlex train image token count must be positive.",
    )
    max_tokens_per_batch = positive_int(
        args.max_tokens_per_batch,
        "NaFlex max image tokens per batch must be positive.",
    )
    batch_divisor = positive_int(args.batch_divisor, "NaFlex batch divisor must be positive.")

    eval_patch_size = args.eval_patch_size or patch_sizes[0]
    if eval_patch_size[0] <= 0 or eval_patch_size[1] <= 0:
        raise ConfigError("NaFlex eval patch size must be positive.")

    eval_seq_len = int(args.eval_seq_len) if args.eval_seq_len is not None else max(seq_lens)
    if eval_seq_len <= 0:
        raise ConfigError("NaFlex eval sequence length must be positive.")

    return ReportConfig(
        train_patch_sizes=patch_sizes,
        train_patch_size_probs=normalize_probs(args.patch_size_probs, len(patch_sizes), "patch size"),
        train_seq_lens=seq_lens,
        train_seq_len_probs=normalize_probs(args.seq_len_probs, len(seq_lens), "seq-len"),
        train_num_image_tokens=train_num_image_tokens,
        max_tokens_per_batch=max_tokens_per_batch,
        batch_divisor=batch_divisor,
        eval_patch_size=eval_patch_size,
        eval_seq_len=eval_seq_len,
        loss_scale=args.loss_scale,
    )


def adjusted_rows(raw_rows: int, divisor: int) -> int:
    if raw_rows <= 0:
        return 0
    return max(divisor, (raw_rows // divisor) * divisor) if raw_rows >= divisor else raw_rows


def estimate_rows(config: ReportConfig, text_tokens: int = 0) -> list[dict[str, int]]:
    rows = []
    for seq_len in sorted(set(config.train_seq_lens)):
        row_cost = seq_len + max(0, int(text_tokens))
        raw = max(1, config.max_tokens_per_batch // row_cost)
        rows.append(
            {
                "seq_len": seq_len,
                "row_cost_tokens": row_cost,
                "raw_rows_per_batch": raw,
                "divisor_adjusted_rows": adjusted_rows(raw, config.batch_divisor),
            }
        )
    return rows


def loss_scale_examples(config: ReportConfig, rows: list[dict[str, int]], nominal_batch_size: int) -> list[dict[str, float]]:
    out = []
    if nominal_batch_size <= 0:
        return out
    for row in rows:
        actual = row["divisor_adjusted_rows"]
        ratio = actual / nominal_batch_size
        if config.loss_scale == "linear":
            scale = ratio
        elif config.loss_scale == "sqrt":
            scale = math.sqrt(ratio)
        else:
            scale = 1.0
        out.append({"seq_len": row["seq_len"], "actual_rows": actual, "loss_scale": scale})
    return out


def config_as_jsonable(config: ReportConfig) -> dict[str, object]:
    data = asdict(config)
    for key in ("train_patch_sizes",):
        data[key] = [list(value) for value in data[key]]
    if data["eval_patch_size"] is not None:
        data["eval_patch_size"] = list(data["eval_patch_size"])
    return data


def print_text_report(config: ReportConfig, args: argparse.Namespace) -> None:
    text_tokens = args.text_tokens or 0
    rows = estimate_rows(config, text_tokens=text_tokens)
    print("NaFlex config: OK")
    print(f"  train patch sizes: {', '.join(f'{h}x{w}' for h, w in config.train_patch_sizes)}")
    print(f"  train seq lens: {', '.join(str(value) for value in config.train_seq_lens)}")
    print(f"  eval: patch_size={config.eval_patch_size[0]}x{config.eval_patch_size[1]} seq_len={config.eval_seq_len}")
    print(f"  max tokens/batch: {config.max_tokens_per_batch:,}  batch divisor: {config.batch_divisor}")
    if config.train_patch_size_probs is not None:
        print(f"  patch-size probs normalized: {tuple(round(value, 6) for value in config.train_patch_size_probs)}")
    if config.train_seq_len_probs is not None:
        print(f"  seq-len probs normalized: {tuple(round(value, 6) for value in config.train_seq_len_probs)}")
        print("  note: seq-len weights are per batch; shorter buckets fit more rows per sample.")
    if config.train_num_image_tokens is not None:
        print(f"  train image-token target: {config.train_num_image_tokens:,}")
    if text_tokens:
        print(f"  GenLIP text-token row cost included: {text_tokens}")
    print(f"  loss scale mode: {config.loss_scale}")

    print("\nEstimated local rows per scheduled batch:")
    print("  seq_len  row_cost  raw_rows  divisor_adjusted")
    for row in rows:
        print(
            f"  {row['seq_len']:>7}  {row['row_cost_tokens']:>8}  "
            f"{row['raw_rows_per_batch']:>8}  {row['divisor_adjusted_rows']:>16}"
        )

    examples = loss_scale_examples(config, rows, args.nominal_batch_size)
    if examples:
        print(f"\nLoss-scale examples relative to nominal --batch-size {args.nominal_batch_size}:")
        for item in examples:
            print(f"  seq_len {item['seq_len']}: rows={item['actual_rows']} scale={item['loss_scale']:.4g}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-sizes", nargs="+", type=parse_patch_size, default=None, help="Patch sizes as N or HxW.")
    parser.add_argument("--patch-size-probs", nargs="+", type=float, default=None, help="Sampling probabilities for patch sizes.")
    parser.add_argument("--seq-lens", nargs="+", type=int, default=None, help="NaFlex sequence-length buckets.")
    parser.add_argument("--seq-len-probs", nargs="+", type=float, default=None, help="Sampling probabilities for sequence lengths.")
    parser.add_argument("--max-tokens-per-batch", type=int, default=4096 * 4, help="Local NaFlex token budget.")
    parser.add_argument("--batch-divisor", type=int, default=8, help="Scheduled batch-size divisor.")
    parser.add_argument("--loss-scale", choices=("none", "linear", "sqrt"), default="none", help="NaFlex loss-scale mode.")
    parser.add_argument("--train-num-image-tokens", type=int, default=None, help="Optional train image-token schedule target.")
    parser.add_argument("--eval-patch-size", type=parse_patch_size, default=None, help="Optional eval patch size as N or HxW.")
    parser.add_argument("--eval-seq-len", type=int, default=None, help="Optional eval sequence length.")
    parser.add_argument("--text-tokens", type=int, default=0, help="Optional GenLIP caption-token row-cost cap.")
    parser.add_argument("--nominal-batch-size", type=int, default=64, help="Nominal --batch-size for loss-scale examples.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = resolve_config(args)
        rows = estimate_rows(config, text_tokens=args.text_tokens or 0)
    except ConfigError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")

    if args.json:
        payload = {
            "ok": True,
            "config": config_as_jsonable(config),
            "estimated_rows": rows,
            "loss_scale_examples": loss_scale_examples(config, rows, args.nominal_batch_size),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text_report(config, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
