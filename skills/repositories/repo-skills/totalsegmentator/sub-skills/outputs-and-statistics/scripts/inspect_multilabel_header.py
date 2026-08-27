#!/usr/bin/env python3
"""Inspect a TotalSegmentator multilabel NIfTI label-map header."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _import_nibabel():
    try:
        import nibabel as nib  # type: ignore
    except ImportError:
        raise SystemExit("ERROR: nibabel is required to inspect NIfTI files. Install nibabel or run this in the TotalSegmentator environment.")
    return nib


def _parse_with_totalseg(path: Path) -> tuple[Any, dict[int, str]] | None:
    try:
        from totalsegmentator.nifti_ext_header import load_multilabel_nifti  # type: ignore
    except Exception:
        return None

    try:
        img, label_map = load_multilabel_nifti(path)
    except ImportError as exc:
        if "xmltodict" in str(exc):
            raise SystemExit("ERROR: xmltodict is required to parse the TotalSegmentator label-map extension. Install xmltodict or validate via run_report.json.")
        return None
    except Exception:
        return None

    return img, {int(key): str(value) for key, value in label_map.items()}


def _parse_extensions(path: Path) -> tuple[Any, dict[int, str]]:
    nib = _import_nibabel()
    try:
        import xmltodict  # type: ignore
    except ImportError:
        raise SystemExit("ERROR: xmltodict is required to parse the label-map extension. Install xmltodict or validate via run_report.json.")

    try:
        img = nib.load(str(path))
    except FileNotFoundError:
        raise SystemExit(f"ERROR: NIfTI file not found: {path}")
    except Exception as exc:
        raise SystemExit(f"ERROR: failed to load NIfTI file {path}: {exc}")

    if not img.header.extensions:
        raise SystemExit("ERROR: no NIfTI header extensions found; class names may need to come from run_report.json and task metadata.")

    errors: list[str] = []
    for extension in img.header.extensions:
        try:
            parsed = xmltodict.parse(extension.get_content())
            labels = parsed["CaretExtension"]["VolumeInformation"]["LabelTable"]["Label"]
            if isinstance(labels, dict):
                labels = [labels]
            label_map = {int(item["@Key"]): str(item["#text"]) for item in labels}
            return img, label_map
        except Exception as exc:
            errors.append(str(exc))

    raise SystemExit("ERROR: no readable TotalSegmentator label-map extension found. Extension parse errors: " + "; ".join(errors))


def _load_label_map(path: Path) -> tuple[Any, dict[int, str]]:
    parsed = _parse_with_totalseg(path)
    if parsed is not None:
        return parsed
    return _parse_extensions(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and validate a multilabel NIfTI label-map header."
    )
    parser.add_argument("image", type=Path, help="Path to a multilabel NIfTI file.")
    parser.add_argument("--require-label", action="append", default=[], help="Require a class name in the label map. Repeatable.")
    parser.add_argument("--require-id", action="append", type=int, default=[], help="Require a numeric label id. Repeatable.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    img, label_map = _load_label_map(args.image)
    label_names = set(label_map.values())
    label_ids = set(label_map)

    errors: list[str] = []
    for label in args.require_label:
        if label not in label_names:
            errors.append(f"required label not found: {label}")
    for label_id in args.require_id:
        if label_id not in label_ids:
            errors.append(f"required label id not found: {label_id}")

    payload = {
        "ok": not errors,
        "errors": errors,
        "image": str(args.image),
        "shape": list(img.shape),
        "num_labels": len(label_map),
        "label_map": {str(key): value for key, value in sorted(label_map.items())},
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Image: {args.image}")
        print(f"Shape: {img.shape}")
        print(f"Labels: {len(label_map)}")
        for key, value in sorted(label_map.items()):
            print(f"{key}: {value}")
        if errors:
            print("ERRORS:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
