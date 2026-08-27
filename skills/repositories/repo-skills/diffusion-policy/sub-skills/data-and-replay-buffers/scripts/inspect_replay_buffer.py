#!/usr/bin/env python3
"""Read-only ReplayBuffer inspector.

Reports data/meta keys, episode_ends, episode count, array shapes, dtypes,
chunks, and simple length-mismatch warnings for zarr directory or zip stores.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

import numpy as np


def _load_zarr():
    try:
        import zarr  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency failure path
        raise SystemExit(
            "inspect_replay_buffer.py requires zarr to read ReplayBuffer stores. "
            "Install zarr (and its numcodecs dependency) and retry."
        ) from exc
    return zarr


@contextmanager
def _open_root(path: Path):
    zarr = _load_zarr()

    if not path.exists():
        raise SystemExit(f"ReplayBuffer path does not exist: {path}")

    if path.is_dir():
        store = zarr.DirectoryStore(str(path))
        root = zarr.open_group(store=store, mode="r") if hasattr(zarr, "open_group") else zarr.open(store=store, mode="r")
        yield zarr, root, "directory"
        return

    if path.suffix == ".zip" or path.name.endswith(".zarr.zip"):
        store = zarr.ZipStore(str(path), mode="r")
        try:
            root = zarr.open_group(store=store, mode="r") if hasattr(zarr, "open_group") else zarr.open(store=store, mode="r")
            yield zarr, root, "zip"
        finally:
            store.close()
        return

    root = zarr.open_group(str(path), mode="r") if hasattr(zarr, "open_group") else zarr.open(str(path), mode="r")
    yield zarr, root, "auto"


def _direct_array_keys(group) -> List[str]:
    if hasattr(group, "array_keys"):
        try:
            return sorted(list(group.array_keys()))
        except Exception:
            pass

    keys: List[str] = []
    for key in sorted(list(group.keys())):
        try:
            item = group[key]
        except Exception:
            continue
        if hasattr(item, "shape") and hasattr(item, "dtype") and hasattr(item, "chunks"):
            keys.append(key)
    return keys


def _array_info(arr) -> Dict[str, object]:
    info: Dict[str, object] = {
        "shape": [int(x) for x in arr.shape],
        "dtype": str(arr.dtype),
        "chunks": [int(x) for x in arr.chunks] if getattr(arr, "chunks", None) is not None else None,
    }
    compressor = getattr(arr, "compressor", None)
    if compressor is not None:
        info["compressor"] = str(compressor)
    return info


def _summarize(path: Path, max_keys: int) -> Dict[str, object]:
    with _open_root(path) as (zarr, root, store_type):
        if "data" not in root or "meta" not in root:
            raise SystemExit("ReplayBuffer root must contain both 'data' and 'meta' groups.")

        data_group = root["data"]
        meta_group = root["meta"]
        data_keys = _direct_array_keys(data_group)
        meta_keys = _direct_array_keys(meta_group)

        report: Dict[str, object] = {
            "path": str(path),
            "store_type": store_type,
            "data_key_count": len(data_keys),
            "meta_key_count": len(meta_keys),
            "data_keys": data_keys[:max_keys],
            "meta_keys": meta_keys[:max_keys],
            "arrays": {},
            "warnings": [],
            "length_mismatches": [],
        }

        episode_ends = None
        if "episode_ends" in meta_group:
            episode_ends = np.asarray(meta_group["episode_ends"][:], dtype=np.int64)
            report["episode_ends"] = episode_ends.tolist()
            report["episode_count"] = int(episode_ends.shape[0])
            report["n_steps"] = int(episode_ends[-1]) if episode_ends.size else 0
            if episode_ends.ndim != 1:
                report["warnings"].append("meta/episode_ends is not one-dimensional")
            if episode_ends.size and np.any(np.diff(episode_ends) <= 0):
                report["warnings"].append("meta/episode_ends is not strictly increasing")
            if episode_ends.size:
                episode_lengths = np.diff(np.concatenate(([0], episode_ends)))
                report["episode_lengths"] = [int(x) for x in episode_lengths.tolist()]
        else:
            report["warnings"].append("meta/episode_ends is missing")
            report["episode_ends"] = []
            report["episode_count"] = 0
            report["n_steps"] = 0
            report["episode_lengths"] = []

        for key in data_keys:
            arr = data_group[key]
            if episode_ends is not None and arr.shape and int(arr.shape[0]) != int(report["n_steps"]):
                report["length_mismatches"].append(
                    {
                        "key": key,
                        "shape0": int(arr.shape[0]),
                        "expected": int(report["n_steps"]),
                    }
                )
            if len(report["arrays"]) < max_keys:
                report["arrays"][f"data/{key}"] = _array_info(arr)

        for key in meta_keys:
            if len(report["arrays"]) >= max_keys:
                break
            arr = meta_group[key]
            report["arrays"][f"meta/{key}"] = _array_info(arr)

        if len(data_keys) > max_keys:
            report["warnings"].append(f"data key list truncated at {max_keys} entries")
        if len(meta_keys) > max_keys:
            report["warnings"].append(f"meta key list truncated at {max_keys} entries")

        return report


def _format_report(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append(f"ReplayBuffer inspection: {report['path']}")
    lines.append(f"  store type: {report['store_type']}")
    lines.append(f"  episode count: {report['episode_count']}")
    lines.append(f"  n steps: {report['n_steps']}")
    lines.append(f"  data keys ({len(report['data_keys'])}/{report['data_key_count']} shown): {', '.join(report['data_keys']) if report['data_keys'] else '(none)'}")
    lines.append(f"  meta keys ({len(report['meta_keys'])}/{report['meta_key_count']} shown): {', '.join(report['meta_keys']) if report['meta_keys'] else '(none)'}")
    lines.append(f"  episode_ends: {report['episode_ends']}")
    if report.get("episode_lengths") is not None:
        lines.append(f"  episode_lengths: {report['episode_lengths']}")

    arrays = report.get("arrays", {})
    if arrays:
        lines.append("  arrays:")
        for name in sorted(arrays):
            info = arrays[name]
            chunk_text = info["chunks"] if info["chunks"] is not None else "None"
            extra = f" compressor={info['compressor']}" if "compressor" in info else ""
            lines.append(
                f"    - {name}: shape={info['shape']} dtype={info['dtype']} chunks={chunk_text}{extra}"
            )

    mismatches = report.get("length_mismatches", [])
    if mismatches:
        lines.append("  length mismatches:")
        for mismatch in mismatches:
            lines.append(
                f"    - {mismatch['key']}: shape[0]={mismatch['shape0']} expected={mismatch['expected']}"
            )

    warnings = report.get("warnings", [])
    if warnings:
        lines.append("  warnings:")
        for warning in warnings:
            lines.append(f"    - {warning}")

    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Diffusion Policy ReplayBuffer store without modifying it.")
    parser.add_argument("--path", required=True, help="Path to a zarr directory or .zarr.zip store")
    parser.add_argument("--max-keys", type=int, default=20, help="Maximum number of keys to include in the report")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text")
    args = parser.parse_args(argv)

    if args.max_keys < 0:
        parser.error("--max-keys must be non-negative")

    report = _summarize(Path(args.path).expanduser(), max_keys=args.max_keys)
    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_report(report) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
