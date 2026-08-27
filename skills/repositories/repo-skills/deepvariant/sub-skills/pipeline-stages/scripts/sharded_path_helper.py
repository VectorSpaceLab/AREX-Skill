#!/usr/bin/env python3
"""Explain DeepVariant/Nucleus sharded path specs without reading data."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

SHARD_SPEC_RE = re.compile(r"^(?P<prefix>.*)@(?P<count>\d*[1-9]\d*)(?:\.(?P<suffix>.+))?$")
SHARD_FILE_RE = re.compile(r"^(?P<prefix>.*)-(?P<index>\d+)-of-(?P<count>\d*[1-9]\d*)(?P<suffix>[^/]*)$")


@dataclass(frozen=True)
class ShardedSpec:
    original: str
    prefix: str
    num_shards: int
    suffix: str
    width: int

    @property
    def pattern(self) -> str:
        return f"{self.prefix}-{'?' * self.width}-of-{self.num_shards:0{self.width}d}{self.suffix}"

    def filename(self, task: int) -> str:
        if task < 0 or task >= self.num_shards:
            raise ValueError(
                f"task {task} is out of range for {self.original}; expected 0..{self.num_shards - 1}"
            )
        return f"{self.prefix}-{task:0{self.width}d}-of-{self.num_shards:0{self.width}d}{self.suffix}"

    def preview(self, limit: int) -> list[str]:
        if self.num_shards <= limit:
            return [self.filename(i) for i in range(self.num_shards)]
        head = max(1, limit // 2)
        tail = max(1, limit - head)
        return [self.filename(i) for i in range(head)] + ["..."] + [
            self.filename(i) for i in range(self.num_shards - tail, self.num_shards)
        ]


def parse_sharded_spec(spec: str) -> ShardedSpec:
    match = SHARD_SPEC_RE.match(spec)
    if not match:
        raise ValueError(
            f"{spec!r} is not a valid DeepVariant sharded spec. Use prefix@N.suffix, for example examples.tfrecord@32.gz."
        )
    num_shards = int(match.group("count"))
    width = max(5, int(math.floor(math.log10(num_shards)) + 1))
    suffix = f".{match.group('suffix')}" if match.group("suffix") else ""
    return ShardedSpec(
        original=spec,
        prefix=match.group("prefix"),
        num_shards=num_shards,
        suffix=suffix,
        width=width,
    )


def parse_concrete_shard(path: str) -> dict[str, object] | None:
    match = SHARD_FILE_RE.match(path)
    if not match:
        return None
    index = int(match.group("index"))
    count = int(match.group("count"))
    return {
        "prefix": match.group("prefix"),
        "index": index,
        "num_shards": count,
        "suffix": match.group("suffix") or "",
        "valid_index": 0 <= index < count,
    }


def likely_mistakes(spec: str, parsed: ShardedSpec | None) -> list[str]:
    warnings: list[str] = []
    if "@0" in spec:
        warnings.append("Shard count must be a positive integer; @0 is invalid.")
    if spec.count("@") > 1:
        warnings.append("Only one @N shard marker is allowed.")
    if re.search(r"\.gz@\d+$", spec) or re.search(r"\.tfrecords?@\d+$", spec):
        warnings.append("The @N marker belongs before the suffix, for example examples.tfrecord@32.gz.")
    if parsed and parsed.num_shards == 1:
        warnings.append("@1 is valid but often unnecessary; an unsharded path plus --task 0 may be clearer for single-process debugging.")
    if parsed and not re.search(r"\.(tfrecords?|bagz)(\.gz)?$", parsed.prefix + parsed.suffix):
        warnings.append("This path does not look like a standard DeepVariant TFRecord-style output; verify the owning stage accepts the extension.")
    return warnings


def explain(spec: str, task: int | None, preview_limit: int) -> dict[str, object]:
    try:
        parsed = parse_sharded_spec(spec)
    except ValueError as exc:
        concrete = parse_concrete_shard(spec)
        return {
            "spec": spec,
            "valid_sharded_spec": False,
            "error": str(exc),
            "concrete_shard": concrete,
            "warnings": likely_mistakes(spec, None),
        }

    result: dict[str, object] = {
        "spec": spec,
        "valid_sharded_spec": True,
        "prefix": parsed.prefix,
        "num_shards": parsed.num_shards,
        "suffix": parsed.suffix,
        "shard_width": parsed.width,
        "glob_pattern": parsed.pattern,
        "preview_filenames": parsed.preview(preview_limit),
        "warnings": likely_mistakes(spec, parsed),
    }
    if task is not None:
        try:
            result["task_filename"] = parsed.filename(task)
        except ValueError as exc:
            result.setdefault("warnings", []).append(str(exc))
    return result


def compare_pair(primary: str, secondary: str, secondary_name: str) -> dict[str, object]:
    result: dict[str, object] = {"secondary_name": secondary_name, "secondary_spec": secondary}
    try:
        left = parse_sharded_spec(primary)
        left_sharded = True
    except ValueError:
        left = None
        left_sharded = False
    try:
        right = parse_sharded_spec(secondary)
        right_sharded = True
    except ValueError as exc:
        right = None
        right_sharded = False
        result["secondary_error"] = str(exc)

    result["primary_is_sharded"] = left_sharded
    result["secondary_is_sharded"] = right_sharded
    if left_sharded != right_sharded:
        result["compatible"] = False
        result["message"] = "Paired filespecs must both be sharded or both be unsharded."
    elif left and right and left.num_shards != right.num_shards:
        result["compatible"] = False
        result["message"] = f"Shard counts differ: primary has {left.num_shards}, {secondary_name} has {right.num_shards}."
    elif left and right:
        result["compatible"] = True
        result["message"] = f"Shard counts match at {left.num_shards}."
    else:
        result["compatible"] = True
        result["message"] = "Neither path is a valid @N spec; treat them as unsharded or reader patterns."
    return result


def print_text(records: Iterable[dict[str, object]]) -> None:
    for record in records:
        print(f"spec: {record['spec']}")
        if not record.get("valid_sharded_spec"):
            print("  valid_sharded_spec: no")
            print(f"  error: {record.get('error')}")
            if record.get("concrete_shard"):
                print(f"  concrete_shard: {record['concrete_shard']}")
        else:
            print("  valid_sharded_spec: yes")
            print(f"  num_shards: {record['num_shards']}")
            print(f"  glob_pattern: {record['glob_pattern']}")
            if "task_filename" in record:
                print(f"  task_filename: {record['task_filename']}")
            print("  preview_filenames:")
            for filename in record["preview_filenames"]:
                print(f"    - {filename}")
        warnings = record.get("warnings") or []
        if warnings:
            print("  warnings:")
            for warning in warnings:
                print(f"    - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", action="append", required=True, help="Sharded spec or concrete shard to explain. May be repeated.")
    parser.add_argument("--task", type=int, help="Optional make_examples task id to resolve for every valid @N spec.")
    parser.add_argument("--paired-gvcf", help="Optional --gvcf / --nonvariant_site_tfrecord_path spec to compare with the first --spec.")
    parser.add_argument("--paired", action="append", default=[], help="Optional paired filespec to compare with the first --spec. May be repeated.")
    parser.add_argument("--preview-limit", type=int, default=8, help="Maximum concrete filenames to preview per spec.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    preview_limit = max(2, args.preview_limit)
    records = [explain(spec, args.task, preview_limit) for spec in args.spec]
    comparisons = []
    primary = args.spec[0]
    if args.paired_gvcf:
        comparisons.append(compare_pair(primary, args.paired_gvcf, "gvcf"))
    for index, paired_spec in enumerate(args.paired, start=1):
        comparisons.append(compare_pair(primary, paired_spec, f"paired_{index}"))

    if args.json:
        print(json.dumps({"records": records, "comparisons": comparisons}, indent=2, sort_keys=True))
    else:
        print_text(records)
        if comparisons:
            print("comparisons:")
            for comparison in comparisons:
                print(f"  - {comparison['secondary_name']}: {comparison['message']}")
    has_error = any(not record.get("valid_sharded_spec") for record in records)
    has_bad_pair = any(not comparison.get("compatible") for comparison in comparisons)
    return 1 if has_error or has_bad_pair else 0


if __name__ == "__main__":
    sys.exit(main())
