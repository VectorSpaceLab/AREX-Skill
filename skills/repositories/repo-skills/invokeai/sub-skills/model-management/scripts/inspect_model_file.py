#!/usr/bin/env python3
"""Safely inspect model files or directories without loading model weights."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any

MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf", ".onnx"}
PICKLE_RISK_EXTENSIONS = {".ckpt", ".pt", ".pth", ".bin"}
CONFIG_NAMES = {"model_index.json", "config.json"}
SAFETENSORS_MAX_HEADER_BYTES = 64 * 1024 * 1024


def format_bytes(byte_count: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(byte_count)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{byte_count} B"


def safe_stat(path: Path) -> dict[str, Any]:
    stat_result = path.stat()
    return {"bytes": stat_result.st_size, "human": format_bytes(stat_result.st_size)}


def inspect_safetensors_header(path: Path, max_tensors: int) -> dict[str, Any]:
    with path.open("rb") as model_file:
        header_length_bytes = model_file.read(8)
        if len(header_length_bytes) != 8:
            raise ValueError("file too small for safetensors header")
        header_length = int.from_bytes(header_length_bytes, "little")
        if header_length > SAFETENSORS_MAX_HEADER_BYTES:
            raise ValueError(f"safetensors header is unexpectedly large ({format_bytes(header_length)})")
        header_bytes = model_file.read(header_length)
        if len(header_bytes) != header_length:
            raise ValueError("truncated safetensors header")
    header = json.loads(header_bytes.decode("utf-8"))
    metadata = header.get("__metadata__", {})
    tensor_items = [(key, value) for key, value in header.items() if key != "__metadata__"]
    tensors = []
    for tensor_name, tensor_info in tensor_items[:max_tensors]:
        if isinstance(tensor_info, dict):
            tensors.append(
                {
                    "name": tensor_name,
                    "dtype": tensor_info.get("dtype"),
                    "shape": tensor_info.get("shape"),
                    "data_offsets": tensor_info.get("data_offsets"),
                }
            )
        else:
            tensors.append({"name": tensor_name, "info": tensor_info})
    return {
        "header_bytes": header_length,
        "metadata": metadata,
        "tensor_count": len(tensor_items),
        "tensors_sample": tensors,
        "truncated_tensors": max(0, len(tensor_items) - len(tensors)),
    }


def inspect_gguf_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as model_file:
        header = model_file.read(24)
    if len(header) < 8:
        raise ValueError("file too small for GGUF header")
    magic = header[:4]
    if magic != b"GGUF":
        raise ValueError("missing GGUF magic")
    version = struct.unpack("<I", header[4:8])[0]
    result: dict[str, Any] = {"magic": "GGUF", "version": version}
    if len(header) >= 24:
        tensor_count = struct.unpack("<Q", header[8:16])[0]
        metadata_kv_count = struct.unpack("<Q", header[16:24])[0]
        result.update({"tensor_count": tensor_count, "metadata_kv_count": metadata_kv_count})
    return result


def inspect_json_config(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        return {"error": str(error)}
    if not isinstance(loaded, dict):
        return {"top_level_type": type(loaded).__name__}
    keys = sorted(str(key) for key in loaded.keys())
    summary = {"top_level_keys": keys[:40], "truncated_keys": max(0, len(keys) - 40)}
    for useful_key in ("_class_name", "architectures", "model_type", "base", "type", "format", "variant"):
        if useful_key in loaded:
            summary[useful_key] = loaded[useful_key]
    return summary


def inspect_file(path: Path, warn_large_mb: float, max_tensors: int) -> dict[str, Any]:
    suffix = path.suffix.lower()
    result: dict[str, Any] = {
        "path": str(path),
        "kind": "file",
        "extension": suffix,
        "size": safe_stat(path),
        "warnings": [],
    }
    size_mb = result["size"]["bytes"] / (1024 * 1024)
    if size_mb >= warn_large_mb:
        result["warnings"].append(
            f"Large file ({size_mb:.1f} MiB); this script inspects headers only and does not load weights."
        )
    if suffix in PICKLE_RISK_EXTENSIONS:
        result["warnings"].append(
            "Pickle-style extension; do not load for diagnostics unless the user accepts malware-scan and memory risk."
        )
    if suffix == ".safetensors":
        try:
            result["safetensors"] = inspect_safetensors_header(path, max_tensors=max_tensors)
        except Exception as error:
            result["warnings"].append(f"Could not parse safetensors header: {error}")
    elif suffix == ".gguf":
        try:
            result["gguf"] = inspect_gguf_header(path)
        except Exception as error:
            result["warnings"].append(f"Could not parse GGUF header: {error}")
    elif path.name in CONFIG_NAMES or suffix == ".json":
        result["json_config"] = inspect_json_config(path)
    elif suffix not in MODEL_EXTENSIONS:
        result["warnings"].append("Extension is not one of InvokeAI's common model file extensions.")
    return result


def inspect_directory(path: Path, max_files: int) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    total_model_like = 0
    total_config_like = 0
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file() or any(part.startswith(".") for part in candidate.parts):
            continue
        suffix = candidate.suffix.lower()
        if suffix in MODEL_EXTENSIONS or candidate.name in CONFIG_NAMES:
            if suffix in MODEL_EXTENSIONS:
                total_model_like += 1
            if candidate.name in CONFIG_NAMES:
                total_config_like += 1
            if len(files) < max_files:
                try:
                    size = safe_stat(candidate)
                except OSError as error:
                    size = {"error": str(error)}
                files.append(
                    {
                        "path": str(candidate.relative_to(path)),
                        "extension": suffix,
                        "size": size,
                        "is_config": candidate.name in CONFIG_NAMES,
                    }
                )
    warnings: list[str] = []
    if total_model_like == 0 and total_config_like == 0:
        warnings.append("No common model files or config markers found under this directory.")
    if total_model_like > max_files:
        warnings.append("Directory contains more model-like files than shown; inspect the intended model root.")
    return {
        "path": str(path),
        "kind": "directory",
        "model_like_file_count": total_model_like,
        "config_marker_count": total_config_like,
        "files_sample": files,
        "truncated_files": max(0, total_model_like + total_config_like - len(files)),
        "warnings": warnings,
    }


def inspect_path(path: Path, warn_large_mb: float, max_files: int, max_tensors: int) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "error": "path does not exist", "warnings": ["Missing file or directory."]}
    if path.is_dir():
        return inspect_directory(path, max_files=max_files)
    return inspect_file(path, warn_large_mb=warn_large_mb, max_tensors=max_tensors)


def print_human(result: dict[str, Any]) -> None:
    print(f"{result.get('path')}:")
    if "error" in result:
        print(f"  error: {result['error']}")
    print(f"  kind: {result.get('kind', 'unknown')}")
    if "extension" in result:
        print(f"  extension: {result['extension'] or '(none)'}")
    if "size" in result:
        print(f"  size: {result['size'].get('human')} ({result['size'].get('bytes')} bytes)")
    if "model_like_file_count" in result:
        print(f"  model-like files: {result['model_like_file_count']}")
        print(f"  config markers: {result['config_marker_count']}")
    if "safetensors" in result:
        safetensors_info = result["safetensors"]
        print(f"  safetensors tensors: {safetensors_info.get('tensor_count')}")
        metadata = safetensors_info.get("metadata") or {}
        if metadata:
            print(f"  safetensors metadata keys: {', '.join(sorted(metadata.keys()))}")
        for tensor in safetensors_info.get("tensors_sample", []):
            print(f"  tensor: {tensor.get('name')} dtype={tensor.get('dtype')} shape={tensor.get('shape')}")
    if "gguf" in result:
        gguf_info = result["gguf"]
        print(
            "  gguf: "
            f"version={gguf_info.get('version')} tensors={gguf_info.get('tensor_count')} "
            f"metadata_kv={gguf_info.get('metadata_kv_count')}"
        )
    if "json_config" in result:
        print(f"  json config: {result['json_config']}")
    for file_info in result.get("files_sample", []):
        print(f"  file: {file_info['path']} {file_info.get('extension') or ''} {file_info.get('size')}")
    for warning in result.get("warnings", []):
        print(f"  warning: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect InvokeAI model files/directories safely without loading tensors or pickle checkpoints."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Model files, directories, or JSON config files")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--max-files", type=int, default=40, help="Maximum directory file entries to show")
    parser.add_argument("--max-tensors", type=int, default=40, help="Maximum safetensors tensor entries to show")
    parser.add_argument(
        "--warn-large-mb",
        type=float,
        default=512.0,
        help="Warn when a file is at least this many MiB; no weights are loaded regardless",
    )
    args = parser.parse_args()

    results = [
        inspect_path(
            path=target_path,
            warn_large_mb=args.warn_large_mb,
            max_files=max(args.max_files, 0),
            max_tensors=max(args.max_tensors, 0),
        )
        for target_path in args.paths
    ]
    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            print_human(result)
    return 1 if any("error" in result for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
