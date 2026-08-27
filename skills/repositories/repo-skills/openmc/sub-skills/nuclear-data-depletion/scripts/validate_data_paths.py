#!/usr/bin/env python3
"""Validate an OpenMC cross-section index without downloading or running transport.

The command checks XML syntax, resolves ``<directory>`` and referenced paths,
reports missing files, validates referenced HDF5 roots when h5py is available,
and checks the referenced depletion-chain XML when it exists. It is deliberately
not a physics-coverage checker: a present HDF5 file may still lack a model
nuclide, temperature, or reaction.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from typing import Any


@dataclass(frozen=True)
class Reference:
    """A file reference extracted from the index."""

    kind: str
    raw_path: str
    resolved_path: Path
    declared_type: str | None = None
    materials: tuple[str, ...] = ()


def _path_from_text(value: str, *, index_path: Path, base: Path) -> Path:
    """Resolve an XML path without depending on the invoking cwd."""
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base / candidate).resolve()


def _decode(value: Any) -> str:
    """Make an HDF5 attribute printable across h5py/numpy versions."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "tolist"):
        value = value.tolist()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
    return str(value)


def _parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    """Return a root element or a human-readable parse error."""
    try:
        return ET.parse(path).getroot(), None
    except (ET.ParseError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _hdf5_status(
    path: Path, declared_type: str, materials: tuple[str, ...] = ()
) -> tuple[str, bool]:
    """Inspect a referenced HDF5 root and return (message, is_valid)."""
    try:
        import h5py  # type: ignore
    except ImportError:
        return "SKIPPED_HDF5_CHECK h5py is not installed", True

    try:
        with h5py.File(path, "r") as handle:
            filetype = _decode(handle.attrs.get("filetype", "<missing>"))
            raw_version = handle.attrs.get("version")
            version = _decode(raw_version if raw_version is not None else "<missing>")
            expected = f"data_{declared_type}"
            if filetype != expected:
                return (
                    f"INVALID_HDF5_TYPE declared={declared_type!r} "
                    f"filetype={filetype!r} version={version}",
                    False,
                )
            try:
                version_length = len(raw_version)
            except TypeError:
                version_length = 0
            if version_length != 2:
                return (
                    f"INVALID_HDF5_SCHEMA filetype={filetype!r} "
                    f"version={version!r} expected_two_values",
                    False,
                )
            if not list(handle.keys()):
                return (
                    f"INVALID_HDF5_SCHEMA filetype={filetype!r} has_no_top_level_groups",
                    False,
                )
            missing = [name for name in materials if name not in handle]
            if missing:
                return (
                    f"INVALID_HDF5_COVERAGE filetype={filetype!r} "
                    f"missing_top_level_groups={missing!r}",
                    False,
                )
            return f"HDF5_OK filetype={filetype} version={version}", True
    except (OSError, ValueError, RuntimeError) as exc:
        return f"INVALID_HDF5 {type(exc).__name__}: {exc}", False


def _collect_references(root: ET.Element, index_path: Path) -> tuple[list[Reference], list[str]]:
    """Collect index references and structural errors."""
    errors: list[str] = []
    directory_node = root.find("directory")
    if directory_node is None or not (directory_node.text or "").strip():
        base = index_path.parent
    else:
        directory = Path((directory_node.text or "").strip()).expanduser()
        base = directory if directory.is_absolute() else index_path.parent / directory
        base = base.resolve()

    references: list[Reference] = []
    for node in root.findall("library"):
        raw_path = (node.get("path") or "").strip()
        declared_type = (node.get("type") or "").strip()
        materials = tuple((node.get("materials") or "").split())
        if not raw_path:
            errors.append("MALFORMED_REFERENCE library is missing path")
            continue
        if declared_type not in {"neutron", "thermal", "photon", "wmp"}:
            errors.append(
                f"MALFORMED_REFERENCE path={raw_path!r} has unsupported type="
                f"{declared_type!r}"
            )
            continue
        references.append(
            Reference(
                "library",
                raw_path,
                _path_from_text(raw_path, index_path=index_path, base=base),
                declared_type,
                materials,
            )
        )

    for node in root.findall("depletion_chain"):
        raw_path = (node.get("path") or "").strip()
        if not raw_path:
            errors.append("MALFORMED_REFERENCE depletion_chain is missing path")
            continue
        references.append(
            Reference(
                "depletion_chain",
                raw_path,
                _path_from_text(raw_path, index_path=index_path, base=base),
            )
        )

    return references, errors


def validate(index: Path) -> int:
    """Validate one cross-section index and return a process exit code."""
    index = index.expanduser().resolve()
    if not index.is_file():
        print(f"MISSING_INDEX {index}")
        return 1

    root, error = _parse_xml(index)
    if error is not None or root is None:
        print(f"MALFORMED_XML {index}: {error}")
        return 2
    if root.tag != "cross_sections":
        print(f"INVALID_ROOT expected='cross_sections' actual={root.tag!r}")
        return 2

    print(f"INDEX_OK {index}")
    references, structural_errors = _collect_references(root, index)
    for message in structural_errors:
        print(message)

    failed = bool(structural_errors)
    hdf5_schema_skipped = False
    if not references:
        print("NO_REFERENCES found no library or depletion_chain entries")

    for reference in references:
        path = reference.resolved_path
        print(
            f"REFERENCE kind={reference.kind} raw={reference.raw_path!r} "
            f"resolved={path}"
        )
        if not path.is_file():
            print(f"MISSING_DATA_PATH {path}")
            failed = True
            continue

        if reference.kind == "library":
            message, valid = _hdf5_status(
                path, reference.declared_type or "", reference.materials
            )
            print(f"{message} path={path}")
            hdf5_schema_skipped = hdf5_schema_skipped or message.startswith(
                "SKIPPED_HDF5_CHECK"
            )
            failed = failed or not valid
        else:
            chain_root, chain_error = _parse_xml(path)
            if chain_error is not None or chain_root is None:
                print(f"MALFORMED_CHAIN_XML {path}: {chain_error}")
                failed = True
            elif chain_root.tag != "depletion_chain":
                print(
                    f"INVALID_CHAIN_ROOT path={path} "
                    f"actual={chain_root.tag!r}"
                )
                failed = True
            else:
                print(f"CHAIN_XML_OK path={path}")

    if failed:
        print("RESULT FAIL")
        return 1
    if hdf5_schema_skipped:
        print(
            "RESULT PASS (path checks only; HDF5 schema inspection was skipped; "
            "model coverage and transport not tested)"
        )
    else:
        print("RESULT PASS (path/schema checks only; model coverage and transport not tested)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Parse an OpenMC cross_sections.xml index, report missing "
            "references, and perform non-network HDF5/XML checks."
        )
    )
    parser.add_argument(
        "--cross-sections",
        required=True,
        type=Path,
        help="explicit path to the cross_sections.xml index",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run validation for command-line arguments."""
    args = build_parser().parse_args(argv)
    return validate(args.cross_sections)


if __name__ == "__main__":
    sys.exit(main())
