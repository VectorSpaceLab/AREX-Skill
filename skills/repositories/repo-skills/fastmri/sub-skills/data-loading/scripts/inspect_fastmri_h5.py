#!/usr/bin/env python3
"""Summarize fastMRI-like HDF5 files without loading full arrays."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

import h5py

ISMRMRD_NS = "http://www.ismrm.org/ISMRMRD"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _find_text(root: ET.Element, names: Iterable[str]) -> str | None:
    node = root
    for name in names:
        child = node.find(f"ismrmrd:{name}", {"ismrmrd": ISMRMRD_NS})
        if child is None:
            child = node.find(name)
        if child is None:
            return None
        node = child
    return node.text


def _parse_ismrmrd_header(raw_header: Any) -> dict[str, Any]:
    if raw_header is None:
        return {"present": False}
    if isinstance(raw_header, bytes):
        raw_header = raw_header.decode("utf-8", errors="replace")
    elif hasattr(raw_header, "item"):
        raw_header = raw_header.item()
        if isinstance(raw_header, bytes):
            raw_header = raw_header.decode("utf-8", errors="replace")

    try:
        root = ET.fromstring(raw_header)
    except Exception as exc:  # noqa: BLE001 - report parse failure without crashing.
        return {"present": True, "parse_error": str(exc)}

    def matrix(prefix: list[str]) -> dict[str, int | None]:
        values: dict[str, int | None] = {}
        for axis in ("x", "y", "z"):
            text = _find_text(root, prefix + [axis])
            try:
                values[axis] = int(text) if text is not None else None
            except ValueError:
                values[axis] = None
        return values

    center_text = _find_text(
        root, ["encoding", "encodingLimits", "kspace_encoding_step_1", "center"]
    )
    maximum_text = _find_text(
        root, ["encoding", "encodingLimits", "kspace_encoding_step_1", "maximum"]
    )

    def parse_int(text: str | None) -> int | None:
        try:
            return int(text) if text is not None else None
        except ValueError:
            return None

    encoded = matrix(["encoding", "encodedSpace", "matrixSize"])
    recon = matrix(["encoding", "reconSpace", "matrixSize"])
    center = parse_int(center_text)
    maximum = parse_int(maximum_text)
    crop: dict[str, int | None] = {
        "encoded_y": encoded.get("y"),
        "recon_y": recon.get("y"),
        "padding_left": None,
        "padding_right": None,
    }
    if encoded.get("y") is not None and center is not None and maximum is not None:
        padding_left = int(encoded["y"]) // 2 - center
        crop["padding_left"] = padding_left
        crop["padding_right"] = padding_left + maximum + 1

    return {
        "present": True,
        "encoded_matrix": encoded,
        "recon_matrix": recon,
        "kspace_encoding_step_1": {"center": center, "maximum": maximum},
        "crop": crop,
    }


def summarize_file(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {"file": str(path), "ok": True}
    try:
        with h5py.File(path, "r") as handle:
            summary["keys"] = sorted(handle.keys())
            summary["datasets"] = {
                key: {"shape": list(handle[key].shape), "dtype": str(handle[key].dtype)}
                for key in sorted(handle.keys())
                if isinstance(handle[key], h5py.Dataset) and key != "ismrmrd_header"
            }
            summary["attrs"] = {key: _jsonable(value) for key, value in handle.attrs.items()}
            summary["kspace_shape"] = (
                list(handle["kspace"].shape) if "kspace" in handle else None
            )
            summary["target_keys"] = [
                key for key in ("reconstruction_esc", "reconstruction_rss") if key in handle
            ]
            summary["has_mask"] = "mask" in handle
            summary["mask_shape"] = list(handle["mask"].shape) if "mask" in handle else None
            header_value = handle["ismrmrd_header"][()] if "ismrmrd_header" in handle else None
            summary["ismrmrd_header"] = _parse_ismrmrd_header(header_value)
    except Exception as exc:  # noqa: BLE001 - report bad files and continue.
        summary["ok"] = False
        summary["error"] = f"{type(exc).__name__}: {exc}"
    return summary


def iter_h5_paths(path: Path, max_files: int | None) -> list[Path]:
    if path.is_file():
        return [path]
    files = sorted(path.glob("*.h5"))
    if max_files is not None:
        files = files[:max_files]
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize fastMRI-like HDF5 files without loading full arrays."
    )
    parser.add_argument("path", type=Path, help="A .h5 file or a directory of .h5 files.")
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Maximum files to inspect when path is a directory; use 0 for all files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    max_files = None if args.max_files == 0 else args.max_files
    paths = iter_h5_paths(args.path, max_files)
    if not paths:
        print(f"No .h5 files found at {args.path}", file=sys.stderr)
        return 2

    summaries = [summarize_file(path) for path in paths]
    if args.json:
        print(json.dumps(summaries, indent=2, sort_keys=True))
        return 0 if all(item.get("ok") for item in summaries) else 1

    for item in summaries:
        print(f"\n== {item['file']} ==")
        if not item.get("ok"):
            print(f"ERROR: {item['error']}")
            continue
        print(f"keys: {', '.join(item['keys'])}")
        print(f"kspace_shape: {item['kspace_shape']}")
        print(f"target_keys: {item['target_keys']}")
        print(f"has_mask: {item['has_mask']} mask_shape: {item['mask_shape']}")
        print(f"attrs: {item['attrs']}")
        header = item["ismrmrd_header"]
        if header.get("present"):
            if "parse_error" in header:
                print(f"ismrmrd_header_parse_error: {header['parse_error']}")
            else:
                print(f"encoded_matrix: {header['encoded_matrix']}")
                print(f"recon_matrix: {header['recon_matrix']}")
                print(f"crop: {header['crop']}")
        else:
            print("ismrmrd_header: missing")

    return 0 if all(item.get("ok") for item in summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
