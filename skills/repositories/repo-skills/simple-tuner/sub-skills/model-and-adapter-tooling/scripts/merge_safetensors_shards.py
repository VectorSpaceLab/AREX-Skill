#!/usr/bin/env python3
"""Preflight and merge sharded safetensors files safely."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_PATTERN = "diffusion_pytorch_model-*.safetensors"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight and merge sharded .safetensors files into one file. The command is dry-run by "
            "default; pass --no-dry-run to write the merged output."
        )
    )
    parser.add_argument("--src-dir", type=Path, required=True, help="Directory containing shard files.")
    parser.add_argument("--dst-file", type=Path, required=True, help="Output .safetensors file.")
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help=f"Glob pattern for shard files inside --src-dir. Default: {DEFAULT_PATTERN!r}.",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Only inspect shards and report what would happen. Default: true; use --no-dry-run to write.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file. Never allows using an input shard as output.",
    )
    return parser


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def discover_shards(src_dir: Path, pattern: str, dst_file: Path) -> list[Path]:
    src_dir = src_dir.expanduser()
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Shard directory not found: {src_dir}")
    shards = sorted(path for path in src_dir.glob(pattern) if path.is_file())
    if not shards:
        raise FileNotFoundError(f"No safetensors shards matching {pattern!r} in {src_dir}")
    dst_resolved = _resolved(dst_file)
    for shard in shards:
        if _resolved(shard) == dst_resolved:
            raise ValueError("Output file must not be one of the input shards.")
    return shards


def inspect_shards(shards: list[Path]) -> tuple[list[dict[str, Any]], dict[str, list[str]], int]:
    try:
        from safetensors import safe_open
    except ImportError as exc:
        raise ImportError("safetensors is required to inspect shard files.") from exc

    owners: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}
    shard_reports: list[dict[str, Any]] = []
    total_tensors = 0

    for shard in shards:
        tensor_count = 0
        dtypes: dict[str, int] = {}
        with safe_open(str(shard), framework="pt", device="cpu") as handle:
            for key in handle.keys():
                tensor_count += 1
                total_tensors += 1
                try:
                    dtype = str(handle.get_slice(key).get_dtype())
                except Exception:
                    dtype = "unknown"
                dtypes[dtype] = dtypes.get(dtype, 0) + 1
                previous = owners.get(key)
                if previous is None:
                    owners[key] = shard.name
                else:
                    duplicates.setdefault(key, [previous]).append(shard.name)
        shard_reports.append(
            {
                "file": shard.name,
                "bytes": shard.stat().st_size,
                "tensor_count": tensor_count,
                "dtypes": dict(sorted(dtypes.items())),
            }
        )
    return shard_reports, dict(sorted(duplicates.items())), total_tensors


def build_report(args: argparse.Namespace, shards: list[Path]) -> dict[str, Any]:
    shard_reports, duplicates, total_tensors = inspect_shards(shards)
    dst_file = args.dst_file.expanduser()
    output_exists = dst_file.exists()
    write_allowed = not args.dry_run and (args.overwrite or not output_exists)
    return {
        "ok": not duplicates,
        "dry_run": bool(args.dry_run),
        "overwrite": bool(args.overwrite),
        "src_dir": str(args.src_dir),
        "pattern": args.pattern,
        "dst_file": str(args.dst_file),
        "output_exists": output_exists,
        "write_allowed": write_allowed,
        "shard_count": len(shards),
        "tensor_count": total_tensors,
        "shards": shard_reports,
        "duplicate_key_count": len(duplicates),
        "duplicate_keys": [
            {"key": key, "files": files} for key, files in list(duplicates.items())[:50]
        ],
    }


def print_human_report(report: dict[str, Any]) -> None:
    print(f"Found {report['shard_count']} shard(s) matching {report['pattern']!r}.")
    for shard in report["shards"]:
        mib = shard["bytes"] / (1024 * 1024)
        dtype_text = ", ".join(f"{dtype}:{count}" for dtype, count in shard["dtypes"].items()) or "unknown"
        print(f"- {shard['file']}: {shard['tensor_count']} tensors, {mib:.2f} MiB, dtypes {dtype_text}")
    print(f"Total tensors: {report['tensor_count']}")
    if report["duplicate_key_count"]:
        print(f"Duplicate tensor keys: {report['duplicate_key_count']}")
        for duplicate in report["duplicate_keys"][:20]:
            print(f"- {duplicate['key']} in {', '.join(duplicate['files'])}")
    if report["dry_run"]:
        print("Dry run: no files written.")
        if report["output_exists"] and not report["overwrite"]:
            print("Actual write would be blocked because the output file exists and --overwrite was not provided.")
    else:
        print("Write requested.")


def emit_report(report: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)


def merge_shards(shards: list[Path], dst_file: Path, *, overwrite: bool) -> dict[str, Any]:
    try:
        from safetensors.torch import load_file, save_file
    except ImportError as exc:
        raise ImportError("safetensors[torch] and torch are required to merge shard files.") from exc

    dst_file = dst_file.expanduser()
    if dst_file.exists() and not overwrite:
        raise FileExistsError("Output file exists; pass --overwrite only after user approval.")

    merged: dict[str, Any] = {}
    for shard in shards:
        shard_state = load_file(str(shard), device="cpu")
        overlap = sorted(set(merged).intersection(shard_state))
        if overlap:
            preview = ", ".join(overlap[:5])
            raise ValueError(f"Duplicate tensor keys across shards: {preview}")
        merged.update(shard_state)

    dst_file.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{dst_file.name}.",
            suffix=".tmp",
            dir=str(dst_file.parent),
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
        save_file(merged, str(temp_path))
        os.replace(temp_path, dst_file)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

    return {"written": True, "output_bytes": dst_file.stat().st_size, "output_tensor_count": len(merged)}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        shards = discover_shards(args.src_dir, args.pattern, args.dst_file)
        report = build_report(args, shards)
        if report["duplicate_key_count"]:
            emit_report(report, as_json=args.json)
            return 1
        if args.dry_run:
            emit_report(report, as_json=args.json)
            return 0
        if report["output_exists"] and not args.overwrite:
            report["ok"] = False
            report["error"] = "Output file exists; pass --overwrite only after user approval."
            emit_report(report, as_json=args.json)
            return 1
        write_report = merge_shards(shards, args.dst_file, overwrite=args.overwrite)
        report.update(write_report)
        report["write_allowed"] = True
        emit_report(report, as_json=args.json)
        return 0
    except Exception as exc:
        if "args" in locals() and getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
