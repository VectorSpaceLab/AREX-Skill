#!/usr/bin/env python3
"""Compile AlpaSim-style protobufs from explicit source and output roots.

This helper is intentionally independent of the original checkout. It writes
only to the caller-selected output root and does not clean files unless
``--clean`` is explicitly supplied.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _proto_files(proto_root: Path) -> list[Path]:
    return sorted(path for path in proto_root.rglob("*.proto") if path.is_file())


def _clean_generated(proto_root: Path, output_root: Path) -> None:
    """Remove generated files corresponding to the selected proto files."""
    for proto in _proto_files(proto_root):
        relative = proto.relative_to(proto_root)
        generated_base = output_root / relative.parent / relative.stem
        for suffix in ("_pb2.py", "_pb2_grpc.py", "_pb2.pyi"):
            candidate = generated_base.with_name(generated_base.name + suffix)
            if candidate.is_file():
                print(f"Removing {candidate}")
                candidate.unlink()


def compile_protos(proto_root: Path, output_root: Path, clean: bool = False) -> int:
    proto_root = proto_root.expanduser().resolve()
    output_root = output_root.expanduser().resolve()
    if not proto_root.is_dir():
        raise ValueError(f"proto root is not a directory: {proto_root}")
    proto_files = _proto_files(proto_root)
    if not proto_files:
        raise ValueError(f"no .proto files found below: {proto_root}")

    try:
        from grpc_tools import protoc
    except ImportError as exc:  # pragma: no cover - depends on caller env
        raise RuntimeError("grpcio-tools is required to compile protobufs") from exc

    output_root.mkdir(parents=True, exist_ok=True)
    if clean:
        _clean_generated(proto_root, output_root)

    arguments = [
        "grpc_tools.protoc",
        f"--proto_path={proto_root}",
        f"--python_out={output_root}",
        f"--grpc_python_out={output_root}",
        f"--pyi_out={output_root}",
        *(str(path.relative_to(proto_root)) for path in proto_files),
    ]
    print(f"Compiling {len(proto_files)} proto file(s) into {output_root}")
    status = protoc.main(arguments)
    if status:
        raise RuntimeError(f"protoc failed with exit status {status}")
    print("Proto compilation completed successfully")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--proto-root",
        type=Path,
        required=True,
        help="directory containing .proto files; imports are resolved below it",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="directory receiving generated Python modules",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove matching generated files in output-root before compiling",
    )
    args = parser.parse_args()
    try:
        return compile_protos(args.proto_root, args.output_root, args.clean)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"compile-protos: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
