#!/usr/bin/env python3
"""Summarize XTuner V1 training logs.

The parser is intentionally small and self-contained. It accepts a single log
file or a directory containing node_*.txt, rank*.log, *.log, or *.txt files and
prints step, loss, throughput, memory, and warning summaries.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

_STEP_RE = re.compile(r"(?:Epoch\s+(?P<epoch>\d+)\s+)?Step\s+(?P<step>\d+)\s*/\s*(?P<total>\d+)")
_RANK_RE = re.compile(r"\[RANK\s+(?P<rank>\d+)\]")
_RANK_FILE_RE = re.compile(r"rank[_-]?(?P<rank>\d+)|node[_-]?(?P<node>\d+)", re.IGNORECASE)
_METRIC_RE = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_./-]*)\s*:\s*"
    r"(?P<value>[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
)

LOSS_KEYS = ("total_loss", "local_loss", "reduced_llm_loss", "llm_loss", "loss")
WARNING_PATTERNS = {
    "config_direct_conflict": re.compile(r"Cannot specify both `?config`? and `?arguments`?", re.I),
    "missing_launch_mode": re.compile(r"Must specify either `?config`? or `?arguments`?", re.I),
    "hf_model_path": re.compile(r"valid HuggingFace model path|AutoConfig|config\.json", re.I),
    "dataset_path": re.compile(r"Dataset file .* does not exist|Dataset file must be a JSONL", re.I),
    "oom": re.compile(r"out of memory|OutOfMemoryError|CUBLAS_STATUS_ALLOC_FAILED|CUDA error: out of memory", re.I),
    "flash_attn_fallback": re.compile(r"flash-attn is not installed|Import FlashAttention 2 failed|using `flex_attention`", re.I),
    "bitsandbytes_cuda": re.compile(r"bitsandbytes.*GPU support|bitsandbytes CUDA binary|libbitsandbytes_cuda", re.I),
    "truncation": re.compile(r"input_ids length .* exceeds model_max_length|truncated", re.I),
    "checkpoint": re.compile(r"Checkpoint path .* does not exist|has no 'weights/'|Scheduler path .* does not exist", re.I),
    "distributed": re.compile(
        r"NCCL|ProcessGroup|ChildFailedError|Rendezvous|TCPStore|rank\s+\d+\s+failed|distributed.*timeout",
        re.I,
    ),
    "generic_warning": re.compile(r"\bWARNING\b|\bWARN\b", re.I),
    "generic_error": re.compile(r"\bERROR\b|Traceback \(most recent call last\)|Exception|ValueError|FileNotFoundError", re.I),
}


@dataclass(slots=True)
class StepRecord:
    file: str
    line_no: int
    step: int
    total: int
    epoch: int | None
    rank: int | None
    metrics: dict[str, float]


@dataclass(slots=True)
class StepSummary:
    step: int
    total: int
    records: int
    ranks: list[int]
    loss_med: float | None
    loss_min: float | None
    loss_max: float | None
    lr_med: float | None
    data_time_med: float | None
    step_time_med: float | None
    tgs_med: float | None
    seqlen_tgs_med: float | None
    exp_tgs_med: float | None
    max_memory_max: float | None
    reserved_memory_max: float | None
    grad_norm_max: float | None
    text_tokens_sum: float | None
    img_tokens_sum: float | None


def finite(values: Iterable[float | None]) -> list[float]:
    out: list[float] = []
    for value in values:
        if value is None:
            continue
        if math.isfinite(value):
            out.append(float(value))
    return out


def med(values: Iterable[float | None]) -> float | None:
    vals = finite(values)
    return statistics.median(vals) if vals else None


def max_or_none(values: Iterable[float | None]) -> float | None:
    vals = finite(values)
    return max(vals) if vals else None


def min_or_none(values: Iterable[float | None]) -> float | None:
    vals = finite(values)
    return min(vals) if vals else None


def sum_or_none(values: Iterable[float | None]) -> float | None:
    vals = finite(values)
    return sum(vals) if vals else None


def fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1000:
        return f"{value:.1f}"
    return f"{value:.{digits}f}"


def discover_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise ValueError(f"not a file or directory: {path}")

    patterns = ["node_*.txt", "rank*.log", "*.log", "*.txt"]
    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in patterns:
        for item in sorted(path.rglob(pattern)):
            if item.is_file() and item not in seen:
                files.append(item)
                seen.add(item)
    return files


def rank_from_filename(path: Path) -> int | None:
    match = _RANK_FILE_RE.search(path.name)
    if not match:
        return None
    value = match.group("rank") or match.group("node")
    return int(value) if value is not None else None


def parse_metric_line(path: Path, line_no: int, line: str, fallback_rank: int | None) -> StepRecord | None:
    step_match = _STEP_RE.search(line)
    if not step_match:
        return None
    metrics = {m.group("key"): float(m.group("value")) for m in _METRIC_RE.finditer(line)}
    if "time" in metrics and "step_time" not in metrics:
        metrics["step_time"] = metrics["time"]
    rank_match = _RANK_RE.search(line)
    rank = int(rank_match.group("rank")) if rank_match else fallback_rank
    epoch = step_match.group("epoch")
    return StepRecord(
        file=str(path),
        line_no=line_no,
        step=int(step_match.group("step")),
        total=int(step_match.group("total")),
        epoch=int(epoch) if epoch is not None else None,
        rank=rank,
        metrics=metrics,
    )


def scan_logs(files: list[Path]) -> tuple[list[StepRecord], Counter[str], list[str]]:
    records: list[StepRecord] = []
    warnings: Counter[str] = Counter()
    samples: list[str] = []
    for path in files:
        fallback_rank = rank_from_filename(path)
        try:
            fh = path.open("r", encoding="utf-8", errors="replace")
        except OSError as exc:
            warnings["unreadable_file"] += 1
            samples.append(f"{path}: {exc}")
            continue
        with fh:
            for line_no, line in enumerate(fh, 1):
                rec = parse_metric_line(path, line_no, line, fallback_rank)
                if rec is not None:
                    records.append(rec)
                for name, pattern in WARNING_PATTERNS.items():
                    if pattern.search(line):
                        warnings[name] += 1
                        if len(samples) < 12 and name not in {"generic_warning", "generic_error"}:
                            samples.append(f"{name}: {line.strip()[:220]}")
    return records, warnings, samples


def loss_for_record(record: StepRecord) -> float | None:
    for key in LOSS_KEYS:
        if key in record.metrics:
            return record.metrics[key]
    for key, value in record.metrics.items():
        if key.endswith("loss"):
            return value
    return None


def summarize_steps(records: list[StepRecord]) -> list[StepSummary]:
    by_step: dict[int, list[StepRecord]] = defaultdict(list)
    for record in records:
        by_step[record.step].append(record)

    summaries: list[StepSummary] = []
    for step in sorted(by_step):
        recs = by_step[step]
        ranks = sorted({r.rank for r in recs if r.rank is not None})
        summaries.append(
            StepSummary(
                step=step,
                total=max(r.total for r in recs),
                records=len(recs),
                ranks=ranks,
                loss_med=med(loss_for_record(r) for r in recs),
                loss_min=min_or_none(loss_for_record(r) for r in recs),
                loss_max=max_or_none(loss_for_record(r) for r in recs),
                lr_med=med(r.metrics.get("lr") for r in recs),
                data_time_med=med(r.metrics.get("data_time") for r in recs),
                step_time_med=med(r.metrics.get("step_time") for r in recs),
                tgs_med=med(r.metrics.get("tgs") for r in recs),
                seqlen_tgs_med=med(r.metrics.get("seqlen_tgs") for r in recs),
                exp_tgs_med=med(r.metrics.get("exp_tgs") or r.metrics.get("e2e_tgs") for r in recs),
                max_memory_max=max_or_none(r.metrics.get("max_memory") for r in recs),
                reserved_memory_max=max_or_none(r.metrics.get("reserved_memory") for r in recs),
                grad_norm_max=max_or_none(r.metrics.get("grad_norm") for r in recs),
                text_tokens_sum=sum_or_none(r.metrics.get("text_tokens") for r in recs),
                img_tokens_sum=sum_or_none(r.metrics.get("img_tokens") for r in recs),
            )
        )
    return summaries


def trend(first: float | None, last: float | None) -> str:
    if first is None or last is None:
        return "unknown"
    delta = last - first
    pct = (delta / first * 100.0) if first else 0.0
    direction = "down" if delta < 0 else "up" if delta > 0 else "flat"
    return f"{direction} ({fmt(first)} -> {fmt(last)}, {pct:+.1f}%)"


def warning_advice(warnings: Counter[str]) -> list[str]:
    advice: list[str] = []
    if warnings["config_direct_conflict"]:
        advice.append("config/direct conflict: remove --config or move direct flags into the Python config")
    if warnings["hf_model_path"]:
        advice.append("model path issue: local HF snapshots should contain config.json; avoid cache parent directories")
    if warnings["dataset_path"]:
        advice.append("dataset path issue: check JSONL file/dir/glob visibility on every node")
    if warnings["oom"]:
        advice.append("OOM: reduce batch/length, use chunk loss/recompute, consider CPU offload or allocator config")
    if warnings["flash_attn_fallback"]:
        advice.append("flash-attn fallback: performance may drop; install compatible flash-attn only if required")
    if warnings["bitsandbytes_cuda"]:
        advice.append("bitsandbytes CUDA warning: harmless unless 8-bit optimizer/quantization is required")
    if warnings["checkpoint"]:
        advice.append("checkpoint issue: resume path must be a complete XTuner DCP checkpoint")
    if warnings["truncation"]:
        advice.append("truncation: samples exceed max length; adjust/filter data or max_length/pack length")
    return advice


def print_text_report(files: list[Path], summaries: list[StepSummary], warnings: Counter[str], samples: list[str], tail: int) -> None:
    print(f"Files scanned: {len(files)}")
    if not summaries:
        print("Parsed step lines: 0")
        if warnings:
            print("Warnings/errors detected before training step loop:")
            for name, count in warnings.most_common():
                print(f"  {name}: {count}")
        for item in warning_advice(warnings):
            print(f"Advice: {item}")
        if samples:
            print("Samples:")
            for sample in samples:
                print(f"  {sample}")
        return

    first = summaries[0]
    last = summaries[-1]
    all_tgs = [s.tgs_med for s in summaries if s.tgs_med is not None]
    all_data = [s.data_time_med for s in summaries if s.data_time_med is not None]
    all_step_time = [s.step_time_med for s in summaries if s.step_time_med is not None]
    print(f"Parsed step lines: {sum(s.records for s in summaries)}")
    print(f"Steps observed: {first.step}..{last.step} of {last.total} ({len(summaries)} distinct step(s))")
    print(f"Ranks observed in last step: {last.ranks if last.ranks else 'unknown'}")
    print(f"Loss trend: {trend(first.loss_med, last.loss_med)}")
    print(f"Latest lr: {fmt(last.lr_med, 6)}")
    print(f"Median tgs over run: {fmt(statistics.median(all_tgs), 1) if all_tgs else '-'}")
    print(f"Median data_time over run: {fmt(statistics.median(all_data), 4) if all_data else '-'} s")
    print(f"Median step time over run: {fmt(statistics.median(all_step_time), 4) if all_step_time else '-'} s")
    print(f"Peak max_memory: {fmt(max_or_none(s.max_memory_max for s in summaries), 2)} GB")
    print(f"Peak reserved_memory: {fmt(max_or_none(s.reserved_memory_max for s in summaries), 2)} GB")
    print(f"Max grad_norm: {fmt(max_or_none(s.grad_norm_max for s in summaries), 3)}")

    if warnings:
        print("\nWarnings/errors:")
        for name, count in warnings.most_common():
            print(f"  {name}: {count}")
    advice = warning_advice(warnings)
    if advice:
        print("\nAdvice:")
        for item in advice:
            print(f"  - {item}")

    print(f"\nLast {min(tail, len(summaries))} step summaries:")
    header = (
        f"{'step':>6} {'rec':>4} {'loss':>10} {'lr':>11} {'data_s':>9} "
        f"{'step_s':>9} {'tgs':>10} {'maxGB':>8} {'grad':>10}"
    )
    print(header)
    print("-" * len(header))
    for s in summaries[-tail:]:
        print(
            f"{s.step:>6} {s.records:>4} {fmt(s.loss_med):>10} {fmt(s.lr_med, 6):>11} "
            f"{fmt(s.data_time_med, 4):>9} {fmt(s.step_time_med, 4):>9} "
            f"{fmt(s.tgs_med, 1):>10} {fmt(s.max_memory_max, 2):>8} {fmt(s.grad_norm_max):>10}"
        )

    if samples:
        print("\nSelected warning samples:")
        for sample in samples:
            print(f"  {sample}")


def write_json_report(path: Path | None, files: list[Path], summaries: list[StepSummary], warnings: Counter[str], samples: list[str]) -> None:
    payload = {
        "files": [str(p) for p in files],
        "steps": [asdict(s) for s in summaries],
        "warnings": dict(warnings),
        "warning_samples": samples,
        "advice": warning_advice(warnings),
    }
    text = json.dumps(payload, indent=2)
    if path is None:
        print(text)
    else:
        path.write_text(text + "\n", encoding="utf-8")
        print(f"JSON written to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize XTuner V1 training logs.")
    parser.add_argument("path", type=Path, help="log file or directory containing XTuner torchrun logs")
    parser.add_argument("--tail", type=int, default=12, help="number of recent step summaries to print")
    parser.add_argument("--warnings", action="store_true", help="kept for readability; warnings are always scanned")
    parser.add_argument("--json", action="store_true", help="print JSON report instead of text")
    parser.add_argument("--json-out", type=Path, help="write JSON report to this path as well/instead")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    files = discover_files(args.path)
    if not files:
        raise SystemExit(f"No log files found under {args.path}")
    records, warnings, samples = scan_logs(files)
    summaries = summarize_steps(records)

    if args.json:
        write_json_report(None, files, summaries, warnings, samples)
    else:
        print_text_report(files, summaries, warnings, samples, max(1, args.tail))
    if args.json_out is not None:
        write_json_report(args.json_out, files, summaries, warnings, samples)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
