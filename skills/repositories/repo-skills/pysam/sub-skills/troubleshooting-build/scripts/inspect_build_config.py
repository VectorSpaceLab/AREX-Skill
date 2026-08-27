#!/usr/bin/env python3
"""Print a redacted JSON summary of the installed pysam build configuration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help=(
            "Include exact include/library paths. Use only for private diagnostics; "
            "paths can reveal machine-specific installation details."
        ),
    )
    return parser


def redact_path(value: Any, show_paths: bool) -> Any:
    if show_paths:
        return value
    if isinstance(value, (str, os.PathLike)):
        text = os.fspath(value)
        if os.sep in text:
            return {"basename": Path(text).name, "redacted": True}
        return text
    return value


def redact_list(values: Any, show_paths: bool) -> list[Any]:
    if values is None:
        return []
    if isinstance(values, (str, os.PathLike)):
        values = [values]
    return [redact_path(value, show_paths) for value in values]


def callable_result(obj: Any, name: str, show_paths: bool) -> dict[str, Any]:
    if not hasattr(obj, name):
        return {"present": False}
    func = getattr(obj, name)
    try:
        value = func()
    except Exception as exc:  # pragma: no cover - version/platform dependent
        return {"present": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"present": True, "ok": True, "value": redact_list(value, show_paths)}


def module_import(name: str) -> dict[str, Any]:
    try:
        __import__(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True}


def run(show_paths: bool) -> dict[str, Any]:
    import pysam

    modules = [
        "pysam",
        "pysam.libchtslib",
        "pysam.libcalignmentfile",
        "pysam.libcalignedsegment",
        "pysam.libcbcf",
        "pysam.libctabix",
        "pysam.libcfaidx",
        "pysam.samtools",
        "pysam.bcftools",
    ]

    result = {
        "ok": True,
        "path_policy": "exact paths shown" if show_paths else "paths redacted",
        "versions": {
            "pysam": getattr(pysam, "__version__", None),
            "samtools": getattr(pysam, "__samtools_version__", None),
            "bcftools": getattr(pysam, "__bcftools_version__", None),
            "htslib": getattr(pysam, "__htslib_version__", None),
        },
        "imports": {module: module_import(module) for module in modules},
        "helpers": {
            "get_include": callable_result(pysam, "get_include", show_paths),
            "get_libraries": callable_result(pysam, "get_libraries", show_paths),
            "get_defines": callable_result(pysam, "get_defines", show_paths),
        },
        "deprecated_aliases_present": {
            "Tabixfile": hasattr(pysam, "Tabixfile"),
            "Fastafile": hasattr(pysam, "Fastafile"),
            "FastqFile": hasattr(pysam, "FastqFile"),
        },
        "command_wrappers_present": {
            "samtools_flagstat": hasattr(getattr(pysam, "samtools", object()), "flagstat"),
            "bcftools_view": hasattr(getattr(pysam, "bcftools", object()), "view"),
            "top_level_sort": hasattr(pysam, "sort"),
        },
    }
    result["ok"] = all(item.get("ok") for item in result["imports"].values())
    return result


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(run(args.show_paths), sort_keys=True))


if __name__ == "__main__":
    main()
