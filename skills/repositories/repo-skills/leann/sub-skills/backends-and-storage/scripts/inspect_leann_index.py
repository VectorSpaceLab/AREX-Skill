#!/usr/bin/env python3
"""Read-only validation for a LEANN index and its backend artifacts.

The checker intentionally uses only the Python standard library.  It validates
metadata, declared JSONL passage sources, restricted-pickle offset maps, and
backend-specific file families.  It does not import LEANN, FAISS, DiskANN,
FlashLib, Torch, an embedding model, or a network service.
"""
from __future__ import annotations

import argparse
import ast
import json
import pickle
import struct
import sys
from pathlib import Path
from typing import Any


class SafeOffsetUnpickler(pickle.Unpickler):
    """Load the primitive dict/string/int pickle emitted for passage offsets.

    The offset file is a local implementation detail, not a trusted interchange
    format.  Disallowing global class resolution prevents ordinary pickle
    imports while retaining support for the primitive map LEANN writes.
    """

    def find_class(self, module: str, name: str) -> Any:  # pragma: no cover - defensive
        raise pickle.UnpicklingError(f"global pickle objects are not allowed: {module}.{name}")


def load_offset_map(path: Path) -> dict[str, int]:
    with path.open("rb") as handle:
        value = SafeOffsetUnpickler(handle).load()
    if not isinstance(value, dict):
        raise ValueError("offset pickle must contain a dictionary")
    result: dict[str, int] = {}
    for key, offset in value.items():
        if not isinstance(key, str):
            raise ValueError("offset-map keys must be strings")
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValueError(f"offset for {key!r} must be a non-negative integer")
        result[key] = offset
    return result


def add_issue(report: dict[str, Any], severity: str, message: str) -> None:
    report["issues"].append({"severity": severity, "message": message})


def resolve_index_path(raw: str) -> tuple[Path, Path]:
    supplied = Path(raw).expanduser()
    if supplied.is_dir():
        candidates = sorted(supplied.glob("*.leann.meta.json"))
        if len(candidates) != 1:
            raise ValueError(
                f"directory input must contain exactly one *.leann.meta.json file; found {len(candidates)}"
            )
        meta_path = candidates[0]
        index_path = Path(str(meta_path)[: -len(".meta.json")])
        return index_path, meta_path
    if supplied.name.endswith(".meta.json"):
        meta_path = supplied
        index_path = Path(str(supplied)[: -len(".meta.json")])
    else:
        index_path = supplied
        meta_path = Path(f"{supplied}.meta.json")
    return index_path, meta_path


def resolve_declared_path(meta_path: Path, raw: str | None, fallback: str) -> Path:
    candidate = Path(raw) if raw else Path(fallback)
    if not candidate.is_absolute():
        candidate = meta_path.parent / candidate
    return candidate


def validate_passages(
    report: dict[str, Any], meta_path: Path, meta: dict[str, Any]
) -> set[str]:
    sources = meta.get("passage_sources")
    if sources is None:
        sources = [
            {
                "type": "jsonl",
                "path": f"{meta_path.name[:-len('.meta.json')]}.passages.jsonl",
                "index_path": f"{meta_path.name[:-len('.meta.json')]}.passages.idx",
            }
        ]
    if not isinstance(sources, list) or not sources:
        add_issue(report, "error", "metadata passage_sources must be a non-empty list")
        return set()

    all_ids: set[str] = set()
    source_reports: list[dict[str, Any]] = []
    base_name = meta_path.name[: -len(".meta.json")]
    for number, source in enumerate(sources):
        if not isinstance(source, dict):
            add_issue(report, "error", f"passage source {number} is not an object")
            continue
        if source.get("type") not in (None, "jsonl"):
            add_issue(report, "error", f"passage source {number} is not JSONL")
            continue
        passage_raw = source.get("path") or source.get("path_relative")
        offset_raw = source.get("index_path") or source.get("index_path_relative")
        passage_path = resolve_declared_path(
            meta_path, passage_raw, f"{base_name}.passages.jsonl"
        )
        offset_path = resolve_declared_path(meta_path, offset_raw, f"{base_name}.passages.idx")
        source_info: dict[str, Any] = {
            "source": number,
            "passages": str(passage_path),
            "offsets": str(offset_path),
        }
        source_reports.append(source_info)
        if not passage_path.is_file():
            add_issue(report, "error", f"passage JSONL is missing: {passage_path}")
            continue
        if not offset_path.is_file():
            add_issue(report, "error", f"passage offset file is missing: {offset_path}")
            continue

        record_offsets: dict[str, int] = {}
        try:
            with passage_path.open("rb") as handle:
                while True:
                    offset = handle.tell()
                    raw_line = handle.readline()
                    if not raw_line:
                        break
                    if not raw_line.strip():
                        add_issue(report, "warning", f"blank JSONL line at byte {offset}: {passage_path}")
                        continue
                    try:
                        record = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        add_issue(report, "error", f"invalid passage record at {passage_path}:{offset}: {exc}")
                        continue
                    if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                        add_issue(report, "error", f"passage record at {passage_path}:{offset} lacks a string id")
                        continue
                    passage_id = record["id"]
                    if passage_id in record_offsets:
                        add_issue(report, "error", f"duplicate passage id {passage_id!r} in {passage_path}")
                    record_offsets[passage_id] = offset
                    if "text" not in record or not isinstance(record.get("text"), str):
                        add_issue(report, "error", f"passage {passage_id!r} has no string text: {passage_path}:{offset}")
                    if "metadata" in record and not isinstance(record["metadata"], dict):
                        add_issue(report, "error", f"passage {passage_id!r} metadata is not an object")
        except OSError as exc:
            add_issue(report, "error", f"cannot read passage JSONL {passage_path}: {exc}")
            continue

        try:
            offset_map = load_offset_map(offset_path)
        except (OSError, EOFError, pickle.PickleError, ValueError) as exc:
            add_issue(report, "error", f"invalid passage offset file {offset_path}: {exc}")
            continue

        try:
            passage_size = passage_path.stat().st_size
            with passage_path.open("rb") as handle:
                for passage_id, offset in offset_map.items():
                    if offset >= passage_size:
                        add_issue(report, "error", f"offset for {passage_id!r} is outside {passage_path}")
                        continue
                    handle.seek(offset)
                    raw_line = handle.readline()
                    try:
                        record = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        add_issue(report, "error", f"offset for {passage_id!r} does not point to JSON: {exc}")
                        continue
                    if not isinstance(record, dict) or record.get("id") != passage_id:
                        actual = record.get("id") if isinstance(record, dict) else None
                        add_issue(
                            report,
                            "error",
                            f"offset for {passage_id!r} points to record {actual!r} in {passage_path}",
                        )
        except OSError as exc:
            add_issue(report, "error", f"cannot verify offsets in {passage_path}: {exc}")
            continue

        offset_ids = set(offset_map)
        record_ids = set(record_offsets)
        missing = sorted(offset_ids - record_ids)
        stale = sorted(record_ids - offset_ids)
        for passage_id in missing:
            add_issue(report, "error", f"offset map references missing passage record {passage_id!r}")
        if stale:
            add_issue(
                report,
                "warning",
                f"{len(stale)} JSONL record(s) are not referenced by the offset map in {passage_path}",
            )
        collisions = all_ids.intersection(offset_ids)
        for passage_id in sorted(collisions):
            add_issue(report, "error", f"passage id {passage_id!r} occurs in multiple sources")
        all_ids.update(offset_ids)
        source_info["records"] = len(record_ids)
        source_info["offsets_count"] = len(offset_map)

    report["passage_sources"] = source_reports
    report["passage_count"] = len(all_ids)
    return all_ids


def validate_id_map(
    report: dict[str, Any], path: Path, passage_ids: set[str], *, label: str
) -> list[str] | None:
    if not path.is_file():
        add_issue(report, "error", f"{label} is missing: {path}")
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        add_issue(report, "error", f"invalid {label} {path}: {exc}")
        return None
    ids = value.get("ids") if isinstance(value, dict) else None
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        add_issue(report, "error", f"{label} must contain an ids list of strings: {path}")
        return None
    if len(ids) != len(set(ids)):
        add_issue(report, "error", f"{label} contains duplicate IDs: {path}")
    if passage_ids and set(ids) != passage_ids:
        add_issue(report, "error", f"{label} IDs do not match passage offset IDs: {path}")
    return ids


def validate_npy_header(report: dict[str, Any], path: Path) -> tuple[int, ...] | None:
    try:
        with path.open("rb") as handle:
            if handle.read(6) != b"\x93NUMPY":
                raise ValueError("missing NPY magic")
            major, minor = handle.read(2)
            if (major, minor) == (1, 0):
                header_size = struct.unpack("<H", handle.read(2))[0]
            elif (major, minor) in ((2, 0), (3, 0)):
                header_size = struct.unpack("<I", handle.read(4))[0]
            else:
                raise ValueError(f"unsupported NPY version {(major, minor)}")
            header = ast.literal_eval(handle.read(header_size).decode("latin1"))
        if not isinstance(header, dict):
            raise ValueError("NPY header is not a dictionary")
        descr = header.get("descr")
        shape = header.get("shape")
        if not isinstance(descr, str) or "O" in descr or not descr.endswith("f4"):
            raise ValueError(f"expected a non-object float32 array, got descr={descr!r}")
        if not isinstance(shape, tuple) or len(shape) != 2 or not all(isinstance(x, int) and x >= 0 for x in shape):
            raise ValueError(f"expected a two-dimensional shape, got {shape!r}")
        return shape
    except (OSError, EOFError, UnicodeDecodeError, ValueError, SyntaxError, struct.error) as exc:
        add_issue(report, "error", f"invalid NPY vector file {path}: {exc}")
        return None


def require_nonempty(report: dict[str, Any], path: Path, label: str) -> bool:
    if not path.is_file():
        add_issue(report, "error", f"{label} is missing: {path}")
        return False
    try:
        if path.stat().st_size == 0:
            add_issue(report, "error", f"{label} is empty: {path}")
            return False
    except OSError as exc:
        add_issue(report, "error", f"cannot stat {label} {path}: {exc}")
        return False
    return True


def validate_backend(
    report: dict[str, Any], index_path: Path, meta: dict[str, Any], passage_ids: set[str]
) -> None:
    backend = meta.get("backend_name")
    if not isinstance(backend, str) or not backend:
        add_issue(report, "error", "metadata backend_name must be a non-empty string")
        return
    prefix = index_path.stem
    directory = index_path.parent
    report["backend"] = backend
    report["prefix"] = prefix

    if backend == "hnsw":
        require_nonempty(report, directory / f"{prefix}.index", "HNSW index")
        ids_path = directory / f"{prefix}.ids.txt"
        if ids_path.is_file():
            try:
                ids = [line.rstrip("\n") for line in ids_path.read_text(encoding="utf-8").splitlines()]
                if len(ids) != len(set(ids)):
                    add_issue(report, "error", f"HNSW ID map contains duplicates: {ids_path}")
                if passage_ids and set(ids) != passage_ids:
                    add_issue(report, "error", f"HNSW ID map does not match passage IDs: {ids_path}")
            except (OSError, UnicodeDecodeError) as exc:
                add_issue(report, "error", f"invalid HNSW ID map {ids_path}: {exc}")
        else:
            add_issue(report, "warning", f"HNSW ID map is missing: {ids_path}")

    elif backend == "ivf":
        require_nonempty(report, directory / f"{prefix}.index", "IVF index")
        map_path = directory / f"{prefix}.ivf_id_map.json"
        if not map_path.is_file():
            add_issue(report, "error", f"IVF ID map is missing: {map_path}")
        else:
            try:
                with map_path.open(encoding="utf-8") as handle:
                    value = json.load(handle)
                id_to_passage = value.get("id_to_passage") if isinstance(value, dict) else None
                passage_to_id = value.get("passage_to_id") if isinstance(value, dict) else None
                next_id = value.get("next_id") if isinstance(value, dict) else None
                if not isinstance(id_to_passage, dict) or not isinstance(passage_to_id, dict):
                    raise ValueError("expected id_to_passage and passage_to_id objects")
                if isinstance(next_id, bool) or not isinstance(next_id, int) or next_id < 0:
                    raise ValueError("next_id must be a non-negative integer")
                normalized = {str(k): v for k, v in id_to_passage.items()}
                if not all(isinstance(v, str) for v in normalized.values()):
                    raise ValueError("id_to_passage values must be strings")
                if any(passage_to_id.get(pid) != int(fid) for fid, pid in normalized.items()):
                    add_issue(report, "error", f"IVF forward/reverse ID maps disagree: {map_path}")
                if passage_ids and set(normalized.values()) != passage_ids:
                    add_issue(report, "error", f"IVF ID map does not match passage IDs: {map_path}")
            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                add_issue(report, "error", f"invalid IVF ID map {map_path}: {exc}")

    elif backend == "diskann":
        pq = [
            directory / f"{prefix}_pq_compressed.bin",
            directory / f"{prefix}_pq_pivots.bin",
        ]
        standard = [directory / f"{prefix}_disk.index", *pq]
        partitioned = [
            directory / f"{prefix}_disk_graph.index",
            directory / f"{prefix}_partition.bin",
            *pq,
            directory / f"{prefix}_disk.index_medoids.bin",
            directory / f"{prefix}_disk.index_max_base_norm.bin",
        ]
        standard_ok = all(require_nonempty(report, path, "DiskANN standard artifact") for path in standard)
        # The preceding calls report missing standard files even when a complete
        # partition layout is valid.  Remove those duplicate provisional issues.
        if not standard_ok:
            report["issues"] = [
                item
                for item in report["issues"]
                if not (
                    item["severity"] == "error"
                    and item["message"].startswith("DiskANN standard artifact is missing:")
                )
            ]
        partition_ok = all(
            require_nonempty(report, path, "DiskANN partition artifact") for path in partitioned
        )
        if not partition_ok:
            report["issues"] = [
                item
                for item in report["issues"]
                if not (
                    item["severity"] == "error"
                    and item["message"].startswith("DiskANN partition artifact is missing:")
                )
            ]
        if not standard_ok and not partition_ok:
            add_issue(report, "error", "DiskANN has neither a complete standard nor partitioned artifact family")
        report["diskann_layout"] = "both" if standard_ok and partition_ok else "standard" if standard_ok else "partitioned" if partition_ok else "invalid"

    elif backend == "flashlib":
        vectors_path = directory / f"{prefix}.flashlib.npy"
        if require_nonempty(report, vectors_path, "FlashLib vector file"):
            shape = validate_npy_header(report, vectors_path)
            if shape is not None:
                if shape[0] != len(passage_ids):
                    add_issue(report, "error", f"FlashLib vector rows ({shape[0]}) do not match passages ({len(passage_ids)})")
                if isinstance(meta.get("dimensions"), int) and shape[1] != meta["dimensions"]:
                    add_issue(report, "error", f"FlashLib vector dimension ({shape[1]}) does not match metadata ({meta['dimensions']})")
        validate_id_map(report, directory / f"{prefix}.flashlib_id_map.json", passage_ids, label="FlashLib ID map")

    elif backend == "flashlib_ivf":
        require_nonempty(report, directory / f"{prefix}.flashlib_ivf.pt", "FlashLib IVF tensor index")
        validate_id_map(report, directory / f"{prefix}.flashlib_ivf_id_map.json", passage_ids, label="FlashLib IVF ID map")
        report["native_content_check"] = "not performed: safe checker does not deserialize Torch tensors"

    else:
        add_issue(report, "error", f"unsupported or unknown backend_name: {backend!r}")


def validate(raw_path: str, strict: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "valid": False,
        "input": raw_path,
        "issues": [],
    }
    try:
        index_path, meta_path = resolve_index_path(raw_path)
    except (OSError, ValueError) as exc:
        add_issue(report, "error", str(exc))
        return report
    report["index_path"] = str(index_path)
    report["metadata_path"] = str(meta_path)
    if not meta_path.is_file():
        add_issue(report, "error", f"metadata file is missing: {meta_path}")
        return report
    try:
        with meta_path.open(encoding="utf-8") as handle:
            meta = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        add_issue(report, "error", f"invalid metadata JSON {meta_path}: {exc}")
        return report
    if not isinstance(meta, dict):
        add_issue(report, "error", "metadata JSON must contain an object")
        return report
    report["metadata"] = {
        "backend_name": meta.get("backend_name"),
        "dimensions": meta.get("dimensions"),
        "passage_sources": len(meta.get("passage_sources", [])) if isinstance(meta.get("passage_sources", []), list) else None,
    }
    dimensions = meta.get("dimensions")
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0:
        add_issue(report, "error", "metadata dimensions must be a positive integer")
    passage_ids = validate_passages(report, meta_path, meta)
    validate_backend(report, index_path, meta, passage_ids)
    if strict:
        for item in report["issues"]:
            if item["severity"] == "warning":
                item["severity"] = "error"
    report["error_count"] = sum(item["severity"] == "error" for item in report["issues"])
    report["warning_count"] = sum(item["severity"] == "warning" for item in report["issues"])
    report["valid"] = report["error_count"] == 0
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a LEANN index's metadata, passages, offsets, and backend artifacts without mutation."
    )
    parser.add_argument(
        "index_path",
        help="Path to name.leann, name.leann.meta.json, or a directory containing one metadata file",
    )
    parser.add_argument("--json", action="store_true", help="Print a machine-readable JSON report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat consistency warnings (including stale JSONL records) as validation failures",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate(args.index_path, strict=args.strict)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        state = "VALID" if report["valid"] else "INVALID"
        print(f"{state}: {report.get('index_path', args.index_path)}")
        if "backend" in report:
            print(f"backend={report['backend']} passages={report.get('passage_count', 0)}")
        for item in report["issues"]:
            print(f"{item['severity'].upper()}: {item['message']}", file=sys.stderr if item["severity"] == "error" else sys.stdout)
        print(
            f"errors={report.get('error_count', 0)} warnings={report.get('warning_count', 0)}",
            file=sys.stderr if not report["valid"] else sys.stdout,
        )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
