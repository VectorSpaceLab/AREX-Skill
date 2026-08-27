#!/usr/bin/env python3
"""Inspect zi2zi train.obj / val.obj pickle streams from Python 3.

Each zi2zi object file is a stream of pickled (label, image_bytes) records that
was normally written by Python 2 cPickle. This helper reads records safely,
counts labels, and can optionally verify image dimensions with Pillow.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def iter_records(path: Path, max_records: int | None = None) -> Iterable[Tuple[int, bytes]]:
    count = 0
    with path.open("rb") as handle:
        while True:
            if max_records is not None and count >= max_records:
                return
            try:
                try:
                    record = pickle.load(handle, encoding="latin1")
                except TypeError:  # pragma: no cover - Python 2 fallback
                    record = pickle.load(handle)
            except EOFError:
                return
            except Exception as exc:
                raise RuntimeError(f"failed to unpickle record {count} from {path}: {exc}") from exc
            if not isinstance(record, tuple) or len(record) != 2:
                raise RuntimeError(f"record {count} from {path} is not a (label, image_bytes) tuple")
            label, payload = record
            if not isinstance(label, int):
                raise RuntimeError(f"record {count} from {path} has non-integer label {label!r}")
            if isinstance(payload, str):
                payload = payload.encode("latin1")
            if not isinstance(payload, (bytes, bytearray)):
                raise RuntimeError(f"record {count} from {path} has non-bytes image payload")
            count += 1
            yield label, bytes(payload)


def inspect_image(payload: bytes) -> Dict[str, Any]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - optional dependency
        return {"image_check": "Pillow unavailable", "error": str(exc)}
    with Image.open(io.BytesIO(payload)) as image:
        width, height = image.size
        return {
            "mode": image.mode,
            "width": width,
            "height": height,
            "paired_width_ok": width == height * 2,
        }


def inspect_obj(path: Path, max_records: int | None, image_check: bool) -> Dict[str, Any]:
    label_counts: collections.Counter[int] = collections.Counter()
    byte_sizes: List[int] = []
    first_images: List[Dict[str, Any]] = []
    for idx, (label, payload) in enumerate(iter_records(path, max_records=max_records)):
        label_counts[label] += 1
        byte_sizes.append(len(payload))
        if image_check and len(first_images) < 5:
            first_images.append(inspect_image(payload))
    result: Dict[str, Any] = {
        "path": str(path),
        "records_read": sum(label_counts.values()),
        "labels": dict(sorted(label_counts.items())),
        "min_bytes": min(byte_sizes) if byte_sizes else None,
        "max_bytes": max(byte_sizes) if byte_sizes else None,
    }
    if first_images:
        result["first_image_checks"] = first_images
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect zi2zi .obj pickle streams")
    parser.add_argument("obj", nargs="+", type=Path, help="train.obj, val.obj, or another zi2zi object file")
    parser.add_argument("--max-records", type=int, help="Read at most this many records from each file")
    parser.add_argument("--expect-label", action="append", type=int, default=[], help="Label expected to appear; repeatable")
    parser.add_argument("--expect-min", type=int, default=1, help="Minimum records expected in each inspected file")
    parser.add_argument("--image-check", action="store_true", help="Open up to five payloads with Pillow and check paired dimensions")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    reports: List[Dict[str, Any]] = []
    problems: List[str] = []
    for obj_path in args.obj:
        if not obj_path.exists():
            problems.append(f"missing file: {obj_path}")
            continue
        try:
            report = inspect_obj(obj_path, args.max_records, args.image_check)
            reports.append(report)
            if report["records_read"] < args.expect_min:
                problems.append(f"{obj_path} has {report['records_read']} records, expected at least {args.expect_min}")
            labels = set(report["labels"].keys())
            for label in args.expect_label:
                if label not in labels:
                    problems.append(f"{obj_path} does not contain expected label {label}")
        except Exception as exc:
            problems.append(str(exc))

    output = {"files": reports, "problems": problems}
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for report in reports:
            print(f"# {report['path']}")
            print(f"records_read: {report['records_read']}")
            print(f"labels: {report['labels']}")
            print(f"byte_size_range: {report['min_bytes']}..{report['max_bytes']}")
            for image in report.get("first_image_checks", []):
                print(f"image: {image}")
            print()
        if problems:
            print("Problems:")
            for problem in problems:
                print(f"- {problem}")
    return 2 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
