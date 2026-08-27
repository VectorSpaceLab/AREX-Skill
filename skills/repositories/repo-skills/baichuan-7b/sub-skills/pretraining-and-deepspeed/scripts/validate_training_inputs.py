#!/usr/bin/env python3
"""Safe preflight checks for Baichuan-7B DeepSpeed pretraining inputs.

This helper validates local paths, corpus sharding, tokenizer placement,
DeepSpeed JSON, and hostfile syntax. It never imports Baichuan train.py,
never initializes distributed training, and never launches DeepSpeed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

HOSTFILE_RE = re.compile(r"^(?P<host>\S+)\s+(?P<rest>.*)$")
SLOTS_RE = re.compile(r"(?:^|\s)slots=(?P<slots>\d+)(?:\s|$)")


@dataclass
class Finding:
    level: str
    message: str
    detail: str = ""


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.summary: dict[str, Any] = {}

    def add(self, level: str, message: str, detail: str = "") -> None:
        self.findings.append(Finding(level, message, detail))

    def error(self, message: str, detail: str = "") -> None:
        self.add("ERROR", message, detail)

    def warn(self, message: str, detail: str = "") -> None:
        self.add("WARN", message, detail)

    def ok(self, message: str, detail: str = "") -> None:
        self.add("OK", message, detail)

    def info(self, message: str, detail: str = "") -> None:
        self.add("INFO", message, detail)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "WARN")

    def exit_code(self, strict_warnings: bool) -> int:
        if self.error_count:
            return 2
        if strict_warnings and self.warning_count:
            return 1
        return 0

    def emit(self, as_json: bool, strict_warnings: bool) -> None:
        payload = {
            "ok": self.exit_code(strict_warnings) == 0,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "summary": self.summary,
            "findings": [asdict(f) for f in self.findings],
            "note": "No training was executed; train.py was not imported.",
        }
        if as_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        print("Baichuan-7B training input validation")
        for finding in self.findings:
            line = f"[{finding.level}] {finding.message}"
            if finding.detail:
                line += f" — {finding.detail}"
            print(line)
        print(
            f"Summary: {self.error_count} error(s), {self.warning_count} warning(s). "
            "No training was executed; train.py was not imported."
        )


def path_arg(value: str) -> Path:
    return Path(value).expanduser()


def is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_tokenizer(path: Path, try_load: bool, report: Report) -> None:
    if not path.exists():
        report.error("Tokenizer model is missing", f"Expected SentencePiece model at {path}")
        return
    if not path.is_file():
        report.error("Tokenizer path is not a file", str(path))
        return
    size = path.stat().st_size
    if size <= 0:
        report.error("Tokenizer model is empty", str(path))
        return
    report.ok("Tokenizer model file exists", f"{path} ({size} bytes)")

    if not try_load:
        report.info("Tokenizer load was not attempted", "Use --try-tokenizer-load when sentencepiece is installed.")
        return
    try:
        import sentencepiece as spm  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional package
        report.error("sentencepiece is not importable", repr(exc))
        return
    try:
        sp = spm.SentencePieceProcessor()
        loaded = sp.Load(str(path))
        if loaded is False:
            report.error("SentencePiece refused to load tokenizer", str(path))
            return
        vocab_size = int(sp.GetPieceSize())
        if vocab_size <= 2:
            report.error("Tokenizer vocabulary is too small for train.py EOS id assumption", f"piece size={vocab_size}")
        else:
            report.ok("SentencePiece tokenizer loaded", f"piece size={vocab_size}; train.py appends EOS token id 2")
    except Exception as exc:  # pragma: no cover - depends on model contents
        report.error("SentencePiece tokenizer load failed", repr(exc))


def load_deepspeed_config(path: Path, report: Report) -> dict[str, Any] | None:
    if not path.exists():
        report.error("DeepSpeed config is missing", str(path))
        return None
    if not path.is_file():
        report.error("DeepSpeed config path is not a file", str(path))
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as exc:
        report.error("DeepSpeed config is not valid JSON", f"{path}: {exc}")
        return None
    except OSError as exc:
        report.error("DeepSpeed config could not be read", f"{path}: {exc}")
        return None
    if not isinstance(cfg, dict):
        report.error("DeepSpeed config root must be a JSON object", str(path))
        return None
    report.ok("DeepSpeed config JSON parsed", str(path))
    return cfg


def validate_deepspeed_config(cfg: dict[str, Any] | None, world_size: int | None, report: Report) -> tuple[int | None, int | None]:
    if cfg is None:
        return None, None

    micro = cfg.get("train_micro_batch_size_per_gpu")
    grad_accum = cfg.get("gradient_accumulation_steps")
    if is_positive_int(micro):
        report.ok("train_micro_batch_size_per_gpu is positive", str(micro))
    else:
        report.error("DeepSpeed config needs positive integer train_micro_batch_size_per_gpu", "train.py indexes this key directly.")
        micro = None

    if is_positive_int(grad_accum):
        report.ok("gradient_accumulation_steps is positive", str(grad_accum))
    else:
        report.error("DeepSpeed config needs positive integer gradient_accumulation_steps", "The demo config uses 1.")
        grad_accum = None

    optimizer = cfg.get("optimizer")
    if isinstance(optimizer, dict) and optimizer.get("type") and isinstance(optimizer.get("params"), dict):
        report.ok("DeepSpeed optimizer block is present", f"type={optimizer.get('type')}")
    else:
        report.error("DeepSpeed optimizer block is incomplete", "Expected optimizer.type and optimizer.params for deepspeed.initialize(..., optimizer=None).")

    zero = cfg.get("zero_optimization")
    if isinstance(zero, dict):
        stage = zero.get("stage")
        if isinstance(stage, int) and not isinstance(stage, bool) and 0 <= stage <= 3:
            if stage != 2:
                report.warn("ZeRO stage differs from Baichuan demo config", f"configured stage={stage}; source config used stage=2")
            else:
                report.ok("ZeRO optimization stage matches demo config", "stage=2")
        else:
            report.error("zero_optimization.stage must be an integer from 0 to 3", repr(stage))
    else:
        report.error("DeepSpeed zero_optimization block is missing", "The source config uses ZeRO stage 2.")

    bf16 = cfg.get("bf16")
    fp16 = cfg.get("fp16")
    if isinstance(bf16, dict) and bf16.get("enabled") is True:
        report.ok("bf16 training is enabled", "Requires compatible accelerator support for a real run.")
    elif isinstance(fp16, dict) and fp16.get("enabled") is True:
        report.warn("fp16 is enabled instead of the source bf16 default", "Confirm numerical and hardware expectations before launch.")
    else:
        report.warn("No enabled bf16/fp16 block found", "The source config enables bf16 for large-scale GPU training.")

    if "steps_per_print" in cfg:
        report.info("DeepSpeed steps_per_print", str(cfg["steps_per_print"]))
    if world_size and micro and grad_accum:
        effective = int(micro) * int(grad_accum) * int(world_size)
        report.info("Estimated global batch in samples", f"micro_batch({micro}) * grad_accum({grad_accum}) * ranks({world_size}) = {effective}")
        declared = cfg.get("train_batch_size")
        if declared is not None and declared != effective:
            report.warn("train_batch_size does not match derived global batch", f"declared={declared}, derived={effective}")
    return int(micro) if micro else None, int(grad_accum) if grad_accum else None


def parse_hostfile(path: Path, skip: bool, allow_placeholders: bool, report: Report) -> tuple[int | None, list[tuple[str, int]]]:
    if skip:
        report.info("Hostfile validation skipped", "Shard validation will use --world-size if provided.")
        return None, []
    if not path.exists():
        report.error("DeepSpeed hostfile is missing", str(path))
        return None, []
    if not path.is_file():
        report.error("DeepSpeed hostfile path is not a file", str(path))
        return None, []

    entries: list[tuple[str, int]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        report.error("Hostfile is not valid UTF-8", f"{path}: {exc}")
        return None, []
    except OSError as exc:
        report.error("Hostfile could not be read", f"{path}: {exc}")
        return None, []

    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "..." or line.startswith("..."):
            if not allow_placeholders:
                report.error("Hostfile still contains ellipsis placeholder", f"{path}:{line_no}: {raw}")
            continue
        if ("[" in line or "]" in line) and not allow_placeholders:
            report.error("Hostfile still contains bracketed placeholder text", f"{path}:{line_no}: {raw}")
            continue
        match = HOSTFILE_RE.match(line)
        if not match:
            report.error("Hostfile line is malformed", f"{path}:{line_no}: {raw}")
            continue
        host = match.group("host")
        slots_match = SLOTS_RE.search(match.group("rest"))
        if not slots_match:
            report.error("Hostfile line is missing slots=N", f"{path}:{line_no}: {raw}")
            continue
        slots = int(slots_match.group("slots"))
        if slots <= 0:
            report.error("Hostfile slots must be positive", f"{path}:{line_no}: {raw}")
            continue
        entries.append((host, slots))

    if not entries:
        report.error("Hostfile has no runnable host entries", str(path))
        return None, []
    total = sum(slots for _, slots in entries)
    report.ok("Hostfile parsed", f"{len(entries)} host(s), {total} total slot(s)")
    report.summary["hostfileEntries"] = [{"host": host, "slots": slots} for host, slots in entries]
    report.summary["hostfileTotalSlots"] = total
    return total, entries


def scan_text_sample(path: Path, sample_lines: int) -> tuple[bool, int, bool, str]:
    """Return (utf8_ok, sampled_line_count, saw_nonblank, detail)."""
    sampled = 0
    saw_nonblank = False
    try:
        with path.open("r", encoding="utf-8", errors="strict") as f:
            for sampled, line in enumerate(f, start=1):
                if line.strip():
                    saw_nonblank = True
                if sampled >= sample_lines:
                    break
    except UnicodeDecodeError as exc:
        return False, sampled, saw_nonblank, str(exc)
    except OSError as exc:
        return False, sampled, saw_nonblank, str(exc)
    return True, sampled, saw_nonblank, ""


def validate_corpus(data_dir: Path, world_size: int | None, allow_uneven: bool, sample_lines: int, report: Report) -> list[Path]:
    if not data_dir.exists():
        report.error("Corpus data_dir is missing", str(data_dir))
        return []
    if not data_dir.is_dir():
        report.error("Corpus data_dir is not a directory", str(data_dir))
        return []

    children = sorted(data_dir.iterdir(), key=lambda p: p.name)
    files = [p for p in children if p.is_file()]
    dirs = [p for p in children if p.is_dir()]
    others = [p for p in children if not p.is_file() and not p.is_dir()]
    for directory in dirs:
        report.error("Corpus directory contains a nested directory", f"train.py iterates os.listdir(data_dir) and may try to open {directory} as a file")
    for other in others:
        report.warn("Corpus directory contains a non-regular entry", str(other))
    if not files:
        report.error("Corpus directory has no regular shard files", str(data_dir))
        return []

    empty_files = [p for p in files if p.stat().st_size == 0]
    for path in empty_files:
        report.error("Corpus shard file is empty", str(path))

    invalid_utf8: list[str] = []
    blank_samples: list[str] = []
    sampled_lines = 0
    for path in files[: min(len(files), 64)]:
        ok, count, saw_nonblank, detail = scan_text_sample(path, sample_lines)
        sampled_lines += count
        if not ok:
            invalid_utf8.append(f"{path}: {detail}")
        elif not saw_nonblank:
            blank_samples.append(str(path))
    if invalid_utf8:
        report.error("Some sampled corpus files are not strict UTF-8", "; ".join(invalid_utf8[:4]))
    else:
        report.ok("Sampled corpus files are UTF-8 decodable", f"sampled up to {sample_lines} line(s) from {min(len(files), 64)} file(s)")
    if blank_samples:
        report.warn("Some sampled corpus files contain only blank sampled lines", "; ".join(blank_samples[:4]))

    total_bytes = sum(p.stat().st_size for p in files)
    report.ok("Corpus shard files found", f"{len(files)} file(s), {total_bytes} byte(s) total")
    report.summary["corpusFiles"] = len(files)
    report.summary["corpusBytes"] = total_bytes
    report.summary["sampledCorpusLines"] = sampled_lines

    if world_size:
        if len(files) < world_size:
            report.error("Corpus has fewer shard files than total DeepSpeed ranks", f"files={len(files)}, ranks={world_size}")
        if len(files) % world_size != 0:
            message = "Corpus shard count is not a multiple of total ranks"
            detail = f"files={len(files)}, ranks={world_size}; README recommends an even multiple of total rank count."
            if allow_uneven:
                report.warn(message, detail)
            else:
                report.error(message, detail + " Use --allow-uneven-shards only when this imbalance is intentional.")
        counts = [0 for _ in range(world_size)]
        for index, _path in enumerate(files):
            counts[index % world_size] += 1
        report.info("Deterministic shard-count projection", f"using sorted file names: min={min(counts)}, max={max(counts)} per rank")
        report.summary["projectedFilesPerRank"] = {str(i): count for i, count in enumerate(counts)}
    else:
        report.warn("Total rank count is unknown", "Provide a valid hostfile or --world-size to check even corpus sharding.")
    return files


def validate_checkpoint_path(path: Path, data_dir: Path, report: Report) -> None:
    if path.exists() and not path.is_dir():
        report.error("Checkpoint saving path exists but is not a directory", str(path))
        return
    if path.resolve() == data_dir.resolve():
        report.error("Checkpoint path must not be the corpus directory", "DeepSpeed output would be mixed with training shards.")
    else:
        try:
            path_resolved = path.resolve(strict=False)
            data_resolved = data_dir.resolve(strict=False)
            if data_resolved in path_resolved.parents:
                report.warn("Checkpoint path is inside the corpus tree", "Keep checkpoints separate from UTF-8 shard files.")
        except OSError:
            pass
    parent = path.parent if str(path.parent) else Path(".")
    if parent.exists():
        report.ok("Checkpoint parent path exists", str(parent))
    else:
        report.warn("Checkpoint parent path does not exist yet", f"Create {parent} before running if DeepSpeed cannot create it.")


def resolve_world_size(hostfile_slots: int | None, requested_world_size: int | None, report: Report) -> int | None:
    if requested_world_size is not None and requested_world_size <= 0:
        report.error("--world-size must be positive", str(requested_world_size))
        return hostfile_slots
    if hostfile_slots and requested_world_size and hostfile_slots != requested_world_size:
        report.error("--world-size disagrees with hostfile slot total", f"--world-size={requested_world_size}, hostfile slots={hostfile_slots}")
        return hostfile_slots
    return hostfile_slots or requested_world_size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Baichuan-7B DeepSpeed pretraining inputs without importing train.py or launching training."
    )
    parser.add_argument("--data-dir", type=path_arg, default=Path("data_dir"), help="Directory of UTF-8 corpus shard files (train.py default: data_dir).")
    parser.add_argument("--tokenizer-path", type=path_arg, default=Path("tokenizer.model"), help="SentencePiece tokenizer.model path.")
    parser.add_argument("--deepspeed-config", type=path_arg, default=Path("config/deepspeed.json"), help="DeepSpeed JSON config path.")
    parser.add_argument("--hostfile", type=path_arg, default=Path("config/hostfile"), help="DeepSpeed hostfile path.")
    parser.add_argument("--skip-hostfile", action="store_true", help="Skip hostfile validation and rely on --world-size if supplied.")
    parser.add_argument("--world-size", type=int, default=None, help="Expected total rank count; must match hostfile slot total when both are provided.")
    parser.add_argument("--max-length", type=int, default=4096, help="Training sequence length used by train.py (default: 4096).")
    parser.add_argument("--steps-per-epoch", type=int, default=4096, help="Checkpoint interval in steps (train.py default: 4096).")
    parser.add_argument("--checkpoint-saving-path", type=path_arg, default=Path("checkpoints"), help="DeepSpeed checkpoint output directory.")
    parser.add_argument("--allow-uneven-shards", action="store_true", help="Downgrade non-multiple shard count from error to warning.")
    parser.add_argument("--allow-placeholder-hostfile", action="store_true", help="Do not fail bracket/ellipsis placeholders in hostfile; useful only for documentation previews.")
    parser.add_argument("--try-tokenizer-load", action="store_true", help="Import sentencepiece and load tokenizer.model for a stronger check.")
    parser.add_argument("--sample-lines", type=int, default=32, help="Lines to sample from each of up to 64 corpus files for UTF-8 checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--strict-warnings", action="store_true", help="Return exit code 1 when warnings are present and no errors are present.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = Report()

    if args.max_length <= 0:
        report.error("--max-length must be positive", str(args.max_length))
    if args.steps_per_epoch <= 0:
        report.error("--steps-per-epoch must be positive", str(args.steps_per_epoch))
    if args.sample_lines <= 0:
        report.error("--sample-lines must be positive", str(args.sample_lines))

    hostfile_slots, _entries = parse_hostfile(args.hostfile, args.skip_hostfile, args.allow_placeholder_hostfile, report)
    world_size = resolve_world_size(hostfile_slots, args.world_size, report)
    report.summary["worldSize"] = world_size

    cfg = load_deepspeed_config(args.deepspeed_config, report)
    micro_batch, _grad_accum = validate_deepspeed_config(cfg, world_size, report)

    check_tokenizer(args.tokenizer_path, args.try_tokenizer_load, report)
    validate_corpus(args.data_dir, world_size, args.allow_uneven_shards, args.sample_lines, report)
    validate_checkpoint_path(args.checkpoint_saving_path, args.data_dir, report)

    if micro_batch and args.max_length and args.steps_per_epoch:
        tokens_per_rank_epoch = int(micro_batch) * int(args.steps_per_epoch) * (int(args.max_length) + 1)
        report.info(
            "Minimum complete token IDs consumed per rank before each checkpoint",
            f"micro_batch({micro_batch}) * steps_per_epoch({args.steps_per_epoch}) * (max_length+1={args.max_length + 1}) = {tokens_per_rank_epoch}; short lines under 20 token IDs are discarded by train.py.",
        )
        report.summary["minTokenIdsPerRankPerCheckpointInterval"] = tokens_per_rank_epoch

    report.emit(args.json, args.strict_warnings)
    return report.exit_code(args.strict_warnings)


if __name__ == "__main__":
    sys.exit(main())
