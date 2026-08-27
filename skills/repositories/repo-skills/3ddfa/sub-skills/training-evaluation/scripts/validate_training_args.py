#!/usr/bin/env python3
"""Validate 3DDFA training command templates without launching training.

This script is intentionally safe:
- it does not import torch or CUDA bindings,
- it does not start training,
- it does not download data,
- it only parses and checks the training command template and its paths.

It can validate either a shell recipe file containing a `train.py` command or a
small direct command-line subset of the training flags.
"""

from __future__ import annotations

import argparse
import pickle
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

ARCH_CHOICES = {"mobilenet_2", "mobilenet_1", "mobilenet_075", "mobilenet_05", "mobilenet_025"}
LOSS_CHOICES = {"wpdc", "vdc", "pdc"}
OPT_CHOICES = {"resample", "all"}


@dataclass
class Issue:
    level: str
    topic: str
    message: str


@dataclass
class Summary:
    issues: list[Issue]

    def add(self, level: str, topic: str, message: str) -> None:
        self.issues.append(Issue(level=level, topic=topic, message=message))

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.level == "ERROR"]

    def render(self) -> str:
        if not self.issues:
            return "No validation issues found."
        lines = []
        for issue in self.issues:
            lines.append(f"[{issue.level}] {issue.topic}: {issue.message}")
        counts = {
            "ERROR": len(self.errors),
            "WARN": sum(1 for issue in self.issues if issue.level == "WARN"),
            "INFO": sum(1 for issue in self.issues if issue.level == "INFO"),
        }
        lines.append(
            f"Summary: {counts['ERROR']} errors, {counts['WARN']} warnings, {counts['INFO']} notes."
        )
        return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate 3DDFA training command templates and data layout.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/validate_training_args.py --template-file training/train_wpdc.sh\n"
            "  python3 scripts/validate_training_args.py --root data/train_aug_120x120 --filelists-train ... --filelists-val ...\n"
        ),
    )
    parser.add_argument("--template-file", type=str, default=None, help="Shell recipe or text file containing a train.py command.")
    parser.add_argument("--strict", action="store_true", help="Treat missing files and mismatches as hard errors.")

    parser.add_argument("--arch", type=str, default=None)
    parser.add_argument("--loss", type=str, default=None)
    parser.add_argument("--opt-style", type=str, default=None)
    parser.add_argument("--resample-num", type=int, default=None)
    parser.add_argument("--root", type=str, default=None)
    parser.add_argument("--filelists-train", type=str, default=None)
    parser.add_argument("--filelists-val", type=str, default=None)
    parser.add_argument("--param-fp-train", type=str, default=None)
    parser.add_argument("--param-fp-val", type=str, default=None)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--snapshot", type=str, default=None)
    parser.add_argument("--devices-id", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--val-batch-size", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--start-epoch", type=int, default=None)
    parser.add_argument("--milestones", type=str, default=None)
    parser.add_argument("--base-lr", type=float, default=None)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--warmup", type=int, default=None)
    parser.add_argument("--print-freq", type=int, default=None)
    return parser


def merge_template_values(args: argparse.Namespace, template_args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    fields = [
        "arch",
        "loss",
        "opt_style",
        "resample_num",
        "root",
        "filelists_train",
        "filelists_val",
        "param_fp_train",
        "param_fp_val",
        "resume",
        "snapshot",
        "devices_id",
        "batch_size",
        "val_batch_size",
        "epochs",
        "start_epoch",
        "milestones",
        "base_lr",
        "workers",
        "warmup",
        "print_freq",
    ]
    for field in fields:
        current = getattr(args, field)
        default = parser.get_default(field)
        if current is None or current == default:
            value = getattr(template_args, field, None)
            if value not in (None, ""):
                setattr(args, field, value)


def parse_template_tokens(template_file: Path) -> list[str]:
    text = template_file.read_text()
    commands: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            current.append(line[:-1].rstrip())
            continue
        current.append(line)
        commands.append(" ".join(current).strip())
        current = []
    if current:
        commands.append(" ".join(current).strip())

    for command in commands:
        if "train.py" not in command:
            continue
        tokens = shlex.split(command)
        for idx, token in enumerate(tokens):
            if Path(token).name == "train.py":
                return tokens[idx + 1 :]
    return []


def resolve_path(raw: str | None, base_dir: Path) -> Path | None:
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(strict=False)


def parse_device_ids(raw: str | None) -> tuple[list[int], list[str]]:
    if not raw:
        return [], ["--devices-id was not provided."]
    ids: list[int] = []
    problems: list[str] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            problems.append("empty device id token")
            continue
        try:
            ids.append(int(chunk))
        except ValueError:
            problems.append(f"non-integer device id {chunk!r}")
    if len(set(ids)) != len(ids):
        problems.append("duplicate device ids were supplied")
    return ids, problems


def read_nonempty_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]


def infer_sample_count(obj) -> int | None:
    if isinstance(obj, np.ndarray):
        return int(obj.shape[0]) if obj.ndim > 0 else None
    if isinstance(obj, (list, tuple)):
        return len(obj)
    if isinstance(obj, dict):
        for key in ("params", "param", "data", "arr_0", "targets"):
            value = obj.get(key)
            if value is None:
                continue
            try:
                return len(value)
            except TypeError:
                if hasattr(value, "shape") and getattr(value, "shape", ()):  # type: ignore[arg-type]
                    return int(value.shape[0])
        return None
    try:
        return len(obj)
    except TypeError:
        return None


def load_param_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".npy":
        obj = np.load(path, allow_pickle=True)
    elif suffix == ".pkl":
        with path.open("rb") as fh:
            obj = pickle.load(fh)
    else:
        return None
    return infer_sample_count(obj)


def validate_dataset_pair(summary: Summary, label: str, filelist_path: Path | None, param_path: Path | None, root_path: Path | None) -> None:
    filelist_count = None
    param_count = None

    if filelist_path is None:
        summary.add("WARN", label, "filelist path was not provided.")
    elif not filelist_path.exists():
        summary.add("WARN" if not summary.errors else "ERROR", label, f"filelist not found: {filelist_path}")
    else:
        lines = read_nonempty_lines(filelist_path)
        filelist_count = len(lines)
        summary.add("INFO", label, f"filelist entries: {filelist_count}")
        if root_path is not None and root_path.exists():
            missing = []
            for entry in lines:
                candidate = resolve_path(entry, root_path)
                if candidate is None or not candidate.exists():
                    missing.append(str(candidate))
                if len(missing) >= 5:
                    break
            if missing:
                summary.add("WARN" if not summary.errors else "ERROR", label, f"first missing sample paths: {', '.join(missing)}")
        elif root_path is not None:
            summary.add("WARN", label, f"image root not found, skipping per-sample checks: {root_path}")
        else:
            summary.add("WARN", label, "no image root supplied, skipping per-sample checks.")

    if param_path is None:
        summary.add("WARN", label, "param file path was not provided.")
    elif not param_path.exists():
        summary.add("WARN" if not summary.errors else "ERROR", label, f"param file not found: {param_path}")
    else:
        param_count = load_param_count(param_path)
        if param_count is None:
            summary.add("WARN", label, f"could not infer sample count from param file: {param_path}")
        else:
            summary.add("INFO", label, f"param entries: {param_count}")

    if filelist_count is not None and param_count is not None and filelist_count != param_count:
        summary.add(
            "ERROR" if summary.errors or False else "WARN",
            label,
            f"filelist/param length mismatch: {filelist_count} vs {param_count}",
        )


def validate(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Summary:
    summary = Summary(issues=[])

    template_base = Path.cwd()
    if args.template_file:
        template_file = Path(args.template_file).expanduser().resolve(strict=False)
        if not template_file.exists():
            summary.add("ERROR" if args.strict else "WARN", "template-file", f"not found: {template_file}")
        else:
            template_base = template_file.parent
            tokens = parse_template_tokens(template_file)
            if not tokens:
                summary.add("WARN", "template-file", f"no train.py command found in {template_file}")
            else:
                template_parser = build_parser()
                template_args, _ = template_parser.parse_known_args(tokens)
                merge_template_values(args, template_args, parser)
                summary.add("INFO", "template-file", f"parsed training command from {template_file.name}")

    if args.arch and args.arch not in ARCH_CHOICES:
        summary.add("WARN" if not args.strict else "ERROR", "arch", f"unknown architecture choice: {args.arch}")

    if args.loss and args.loss not in LOSS_CHOICES:
        summary.add("WARN" if not args.strict else "ERROR", "loss", f"unknown loss choice: {args.loss}")
    elif args.loss == "wpdc" and args.opt_style not in (None, "", "resample"):
        summary.add("WARN", "loss", "WPDC currently only implements the resample path.")
    elif args.loss == "vdc" and args.opt_style not in (None, "", "resample", "all"):
        summary.add("WARN", "loss", f"unexpected VDC opt-style: {args.opt_style}")
    elif args.loss == "pdc" and args.opt_style not in (None, ""):
        summary.add("INFO", "loss", "PDC uses MSELoss; opt-style is ignored by the current training code.")

    if args.template_file:
        template_stem = Path(args.template_file).stem.lower()
        if "wpdc" in template_stem and args.loss and args.loss != "wpdc":
            summary.add("WARN", "template-loss", f"template name suggests WPDC, but the parsed loss is {args.loss!r}.")
        elif "vdc" in template_stem and args.loss and args.loss != "vdc":
            summary.add("WARN", "template-loss", f"template name suggests VDC, but the parsed loss is {args.loss!r}.")
        elif "pdc" in template_stem and "wpdc" not in template_stem and args.loss and args.loss != "pdc":
            summary.add("WARN", "template-loss", f"template name suggests PDC, but the parsed loss is {args.loss!r}.")

    if args.resample_num is not None and args.loss in {"wpdc", "vdc"}:
        summary.add("INFO", "resample-num", "the current train.py does not forward this flag into the loss constructors.")

    device_ids, device_problems = parse_device_ids(args.devices_id)
    for problem in device_problems:
        summary.add("WARN" if not args.strict else "ERROR", "devices-id", problem)
    if device_ids:
        if len(device_ids) > 1:
            summary.add("WARN", "devices-id", f"multi-GPU DataParallel requested across ids: {device_ids}")
        else:
            summary.add("INFO", "devices-id", f"single-GPU run on device id {device_ids[0]}")

    root_path = resolve_path(args.root, template_base) if args.root else None
    if args.root and root_path is not None and not root_path.exists():
        summary.add("WARN" if not args.strict else "ERROR", "root", f"image root not found: {root_path}")

    filelist_train = resolve_path(args.filelists_train, template_base)
    filelist_val = resolve_path(args.filelists_val, template_base)
    param_train = resolve_path(args.param_fp_train, template_base)
    param_val = resolve_path(args.param_fp_val, template_base)
    resume = resolve_path(args.resume, template_base)
    snapshot = resolve_path(args.snapshot, template_base)

    validate_dataset_pair(summary, "train", filelist_train, param_train, root_path)
    validate_dataset_pair(summary, "val", filelist_val, param_val, root_path)

    if resume is not None and not resume.exists():
        summary.add("WARN" if not args.strict else "ERROR", "resume", f"checkpoint not found: {resume}")
    elif resume is not None:
        summary.add("INFO", "resume", f"checkpoint found: {resume}")

    if snapshot is not None:
        summary.add("INFO", "snapshot", f"checkpoint prefix: {snapshot}")

    return summary


def main() -> int:
    parser = build_parser()
    args, _ = parser.parse_known_args()
    summary = validate(args, parser)
    print(summary.render())
    if args.strict and summary.errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
