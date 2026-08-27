#!/usr/bin/env python3
"""Read-only checker for a Walk These Ways run/checkpoint layout.

The checker never unpickles parameters.pkl, writes files, imports the source
repository, starts a simulator, or contacts a logger. TorchScript inspection is
opt-in and should only be used for artifacts the caller trusts.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED = (
    "parameters.pkl",
    "checkpoints/body_latest.jit",
    "checkpoints/adaptation_module_latest.jit",
    "checkpoints/ac_weights_last.pt",
)


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def file_record(root: Path, relative: str) -> Dict[str, Any]:
    raw = root / relative
    record: Dict[str, Any] = {"path": relative, "present": False}
    try:
        resolved = raw.resolve(strict=False)
    except OSError as exc:
        record["error"] = f"cannot resolve path: {exc}"
        return record
    if not inside(root, resolved):
        record["error"] = "resolved path escapes selected run directory"
        return record
    try:
        info = raw.lstat()
    except FileNotFoundError:
        return record
    except OSError as exc:
        record["error"] = f"cannot stat: {exc}"
        return record
    if stat.S_ISLNK(info.st_mode):
        record["error"] = "symlinks are rejected by the safe checker"
        return record
    if not stat.S_ISREG(info.st_mode):
        record["error"] = "path is not a regular file"
        return record
    record.update({"present": True, "bytes": info.st_size, "mode": stat.filemode(info.st_mode)})
    if info.st_size <= 0:
        record["error"] = "file is empty"
    return record


def torchscript_metadata(path: Path) -> Dict[str, Any]:
    """Load a trusted JIT artifact and report serialization metadata only."""
    try:
        import torch  # optional dependency; not a source-repo import
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"available": False, "error": f"torch unavailable: {exc}"}
    try:
        module = torch.jit.load(str(path), map_location="cpu")
        result: Dict[str, Any] = {"available": True, "type": type(module).__name__}
        try:
            result["training"] = bool(module.training)
        except Exception:
            pass
        try:
            code = module.code
            result["code_lines"] = len(str(code).splitlines())
            result["code_preview"] = "\n".join(str(code).splitlines()[:8])
        except Exception as exc:
            result["code_error"] = str(exc)
        try:
            graph = str(module.inlined_graph)
            result["graph_lines"] = len(graph.splitlines())
            result["graph_preview"] = "\n".join(graph.splitlines()[:12])
        except Exception as exc:
            result["graph_error"] = str(exc)
        return result
    except Exception as exc:
        return {"available": False, "error": f"TorchScript load failed: {exc}"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check required Walk These Ways checkpoint files without unpickling, writing, networking, or simulator imports."
    )
    parser.add_argument("run_dir", type=Path, help="explicit run directory containing parameters.pkl and checkpoints/")
    parser.add_argument("--torchscript", action="store_true", help="load the two JIT files and report read-only metadata (trust artifacts first)")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument("--allow-missing", action="store_true", help="report missing files but exit zero (default is non-zero for incomplete layout)")
    args = parser.parse_args(argv)

    try:
        root = args.run_dir.expanduser().resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        print(f"ERROR: run directory is unavailable: {exc}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"ERROR: run directory is not a directory: {root}", file=sys.stderr)
        return 2

    files = {relative: file_record(root, relative) for relative in REQUIRED}
    problems = [relative for relative, record in files.items() if not record.get("present") or record.get("error")]
    report: Dict[str, Any] = {
        "ok": not problems,
        "run_dir": str(root),
        "files": files,
        "iteration_files": [],
        "torchscript": {},
        "notes": [
            "parameters.pkl presence was checked without unpickling it",
            "no files were written and no source-repository imports were performed",
        ],
    }

    checkpoints = root / "checkpoints"
    if checkpoints.is_dir():
        try:
            for item in sorted(checkpoints.iterdir()):
                if item.is_file() and item.name.startswith("ac_weights_") and item.name.endswith(".pt"):
                    report["iteration_files"].append(item.name)
        except OSError as exc:
            report["notes"].append(f"could not enumerate optional iteration files: {exc}")

    if args.torchscript:
        for relative in ("checkpoints/adaptation_module_latest.jit", "checkpoints/body_latest.jit"):
            record = files[relative]
            if record.get("present") and not record.get("error"):
                report["torchscript"][relative] = torchscript_metadata(root / relative)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "INCOMPLETE"
        print(f"{status}: {root}")
        for relative, record in files.items():
            if record.get("present") and not record.get("error"):
                print(f"  present {relative} ({record['bytes']} bytes)")
            else:
                print(f"  missing/invalid {relative}: {record.get('error', 'not found')}")
        if report["iteration_files"]:
            print("  iteration state dicts: " + ", ".join(report["iteration_files"]))
        for relative, metadata in report["torchscript"].items():
            if metadata.get("available"):
                print(f"  TorchScript metadata: {relative} ({metadata.get('type', 'unknown')})")
            else:
                print(f"  TorchScript metadata failed: {relative}: {metadata.get('error')}")
        for note in report["notes"]:
            print(f"  note: {note}")

    if problems and not args.allow_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
