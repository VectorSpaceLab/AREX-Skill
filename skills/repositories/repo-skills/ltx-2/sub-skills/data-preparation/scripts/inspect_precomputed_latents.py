#!/usr/bin/env python3
"""Inspect LTX precomputed .pt directories without decoding latents or importing LTX."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_DIRS = [
    "latents",
    "conditions",
    "audio_latents",
    "reference_latents",
    "reference_audio_latents",
    "video_masks",
    "audio_masks",
]
ALIASES = {"media_path": "video", "ref_media_path": "reference_video"}
DIR_TO_ROLE = {
    "latents": "video",
    "conditions": "caption",
    "audio_latents": "audio",
    "reference_latents": "reference_video",
    "reference_audio_latents": "reference_audio",
    "video_masks": "video_mask",
    "audio_masks": "audio_mask",
}
ROLE_TO_NAMING_ROLE = {
    "caption": ("video", "audio", "caption"),
    "video": ("video",),
    "audio": ("video", "audio"),
    "reference_video": ("video",),
    "reference_audio": ("video", "audio", "reference_audio"),
    "video_mask": ("video",),
    "audio_mask": ("video", "audio"),
}


def import_torch():
    try:
        import torch  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("This inspector needs PyTorch to read .pt files. Install torch in the current environment.") from exc
    return torch


def tensor_summary(value: Any) -> dict[str, Any] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    summary: dict[str, Any] = {"shape": [int(dim) for dim in shape]}
    dtype = getattr(value, "dtype", None)
    if dtype is not None:
        summary["dtype"] = str(dtype)
    device = getattr(value, "device", None)
    if device is not None:
        summary["device"] = str(device)
    return summary


def scalar_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "item"):
        try:
            item = value.item()
            if isinstance(item, (str, int, float, bool)) or item is None:
                return item
        except Exception:
            pass
    return repr(value)


def summarize_payload(path: Path, *, torch_module: Any) -> dict[str, Any]:
    try:
        payload = torch_module.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        payload = torch_module.load(path, map_location="cpu")
    except Exception as exc:  # noqa: BLE001
        return {"path": str(path), "error": str(exc)}

    info: dict[str, Any] = {"path": str(path), "payload_type": type(payload).__name__}
    if isinstance(payload, dict):
        info["keys"] = sorted(str(key) for key in payload.keys())
        tensors: dict[str, Any] = {}
        scalars: dict[str, Any] = {}
        for key, value in payload.items():
            ts = tensor_summary(value)
            if ts is not None:
                tensors[str(key)] = ts
            else:
                scalars[str(key)] = scalar_safe(value)
        if tensors:
            info["tensors"] = tensors
        if scalars:
            info["scalars"] = scalars
    else:
        ts = tensor_summary(payload)
        if ts is not None:
            info["tensor"] = ts
        else:
            info["value"] = scalar_safe(payload)
    return info


def load_manifest(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON manifest must be a list of objects")
        rows = data
    elif suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    obj = json.loads(stripped)
                    if not isinstance(obj, dict):
                        raise ValueError("JSONL manifest lines must be objects")
                    rows.append(obj)
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    else:
        raise ValueError("Manifest must be .json, .jsonl, or .csv")
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(str(key))
    return rows, columns


def resolve_roles(columns: list[str]) -> dict[str, str]:
    roles: dict[str, str] = {}
    for col in columns:
        role = ALIASES.get(col, col)
        if role not in roles:
            roles[role] = col
    return roles


def output_relative(value: Any, data_root: Path) -> Path:
    raw = Path(str(value).strip()).expanduser()
    resolved = raw if raw.is_absolute() else data_root / raw
    try:
        rel = resolved.relative_to(data_root)
    except ValueError:
        rel = Path(*resolved.parts[1:]) if resolved.is_absolute() else resolved
    return rel.with_suffix(".pt")


def expected_paths_for_dir(manifest: Path, rows: list[dict[str, Any]], roles: dict[str, str], dir_name: str) -> set[Path]:
    role = DIR_TO_ROLE[dir_name]
    # Target audio can be explicit (`audio`) or auto-extracted from target videos;
    # in the latter case output filenames are keyed by the target video path.
    if dir_name == "audio_latents" and "audio" not in roles and "video" in roles:
        column = roles["video"]
        return {
            output_relative(row[column], manifest.parent)
            for row in rows
            if row.get(column) is not None and str(row.get(column)).strip()
        }
    if role != "caption" and role not in roles:
        return set()
    for naming_role in ROLE_TO_NAMING_ROLE[role]:
        if naming_role in roles:
            column = roles[naming_role]
            return {
                output_relative(row[column], manifest.parent)
                for row in rows
                if row.get(column) is not None and str(row.get(column)).strip()
            }
    return set()


def inspect_dir(root: Path, dir_name: str, limit: int, torch_module: Any) -> dict[str, Any]:
    directory = root / dir_name
    result: dict[str, Any] = {"exists": directory.is_dir(), "count": 0, "samples": []}
    if not directory.is_dir():
        return result
    files = sorted(path for path in directory.rglob("*.pt") if path.is_file())
    result["count"] = len(files)
    result["relative_files_preview"] = [str(path.relative_to(directory)) for path in files[:limit]]
    result["samples"] = [summarize_payload(path, torch_module=torch_module) for path in files[:limit]]
    return result


def analyze(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    torch_module = import_torch()
    root = args.precomputed_root
    output: dict[str, Any] = {"precomputed_root": str(root), "directories": {}, "warnings": [], "errors": []}

    dirs = args.dirs or EXPECTED_DIRS
    for dir_name in dirs:
        output["directories"][dir_name] = inspect_dir(root, dir_name, args.limit, torch_module)

    if args.manifest:
        try:
            rows, columns = load_manifest(args.manifest)
            roles = resolve_roles(columns)
            output["manifest"] = {"path": str(args.manifest), "rows": len(rows), "roles": roles}
            for dir_name in dirs:
                if dir_name not in DIR_TO_ROLE:
                    continue
                expected = expected_paths_for_dir(args.manifest, rows, roles, dir_name)
                if not expected:
                    continue
                directory = root / dir_name
                actual = {path.relative_to(directory) for path in directory.rglob("*.pt")} if directory.is_dir() else set()
                missing = sorted(str(path) for path in expected - actual)
                extra = sorted(str(path) for path in actual - expected)
                output["directories"][dir_name]["expected_count_from_manifest"] = len(expected)
                output["directories"][dir_name]["missing_from_manifest"] = missing[: args.limit]
                output["directories"][dir_name]["extra_vs_manifest"] = extra[: args.limit]
                explicit_role_expected = DIR_TO_ROLE[dir_name] in roles or DIR_TO_ROLE[dir_name] == "caption"
                required_dir = dir_name in (args.require_dirs or [])
                directory_present = output["directories"][dir_name].get("exists", False)
                if args.check_manifest and missing and (explicit_role_expected or required_dir or directory_present):
                    output["errors"].append(f"{dir_name}: missing {len(missing)} expected .pt files")
                if extra:
                    output["warnings"].append(f"{dir_name}: has {len(extra)} .pt files not expected from manifest")
        except Exception as exc:  # noqa: BLE001
            output["errors"].append(f"manifest inspection failed: {exc}")

    required = args.require_dirs or []
    for dir_name in required:
        info = output["directories"].get(dir_name) or inspect_dir(root, dir_name, args.limit, torch_module)
        if not info.get("exists"):
            output["errors"].append(f"required directory missing: {dir_name}")
        elif info.get("count", 0) == 0:
            output["errors"].append(f"required directory is empty: {dir_name}")

    return output, 1 if output["errors"] else 0


def print_text(output: dict[str, Any]) -> None:
    print(f"Precomputed root: {output['precomputed_root']}")
    for dir_name, info in output["directories"].items():
        status = "present" if info.get("exists") else "missing"
        print(f"\n{dir_name}: {status}, {info.get('count', 0)} .pt files")
        if "expected_count_from_manifest" in info:
            print(f"  expected from manifest: {info['expected_count_from_manifest']}")
            if info.get("missing_from_manifest"):
                print(f"  missing preview: {info['missing_from_manifest']}")
            if info.get("extra_vs_manifest"):
                print(f"  extra preview: {info['extra_vs_manifest']}")
        for sample in info.get("samples", []):
            rel = Path(sample.get("path", "")).name
            if "error" in sample:
                print(f"  sample {rel}: ERROR {sample['error']}")
                continue
            keys = sample.get("keys")
            print(f"  sample {rel}: keys={keys}")
            tensors = sample.get("tensors", {})
            for key, summary in tensors.items():
                print(f"    {key}: shape={summary.get('shape')} dtype={summary.get('dtype')}")
            scalars = sample.get("scalars", {})
            if scalars:
                print(f"    scalars={scalars}")
    if output.get("warnings"):
        print("\nWarnings:")
        for warning in output["warnings"]:
            print(f"  - {warning}")
    if output.get("errors"):
        print("\nErrors:")
        for error in output["errors"]:
            print(f"  - {error}")
    print("\nResult: " + ("FAIL" if output.get("errors") else "PASS"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize LTX precomputed .pt files and tensor shapes without decoding or loading model weights.",
    )
    parser.add_argument("--precomputed-root", type=Path, required=True, help="Directory containing latents/conditions/etc.")
    parser.add_argument("--manifest", type=Path, default=None, help="Optional manifest for expected file coverage checks")
    parser.add_argument("--check-manifest", action="store_true", help="Fail if expected manifest-derived .pt files are missing")
    parser.add_argument("--limit", type=int, default=3, help="Number of files/missing entries to preview per directory")
    parser.add_argument("--dirs", nargs="+", default=None, help="Specific subdirectories to inspect; defaults to all known dirs")
    parser.add_argument("--require-dirs", nargs="+", default=None, help="Directories that must exist and be non-empty")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output, code = analyze(args)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"errors": [str(exc)], "warnings": []}, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print_text(output)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
