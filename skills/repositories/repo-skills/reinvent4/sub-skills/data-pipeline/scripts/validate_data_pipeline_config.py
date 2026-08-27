#!/usr/bin/env python3
"""Static validation for REINVENT4 data-pipeline configs.

The script parses a TOML ``data_pipeline.toml`` file, checks required fields,
filter structure, input/output paths, transform-file naming, and a small sample
of the selected SMILES column. It intentionally does not import REINVENT4,
RDKit, or Polars, and it does not run preprocessing or write output files.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    tomllib = None  # type: ignore[assignment]


BASE_ELEMENTS = {"C", "O", "N", "S", "F", "Cl", "Br", "I"}
BUILTIN_TRANSFORMS = {"standard", "four_valent_nitrogen"}
ALLOWED_TOP_LEVEL = {
    "input_csv_file",
    "smiles_column",
    "separator",
    "output_smiles_file",
    "num_procs",
    "chunk_size",
    "filter",
    "transform_file",
}
ALLOWED_FILTER_KEYS = {
    "elements",
    "transforms",
    "min_heavy_atoms",
    "max_heavy_atoms",
    "max_mol_weight",
    "min_carbons",
    "max_num_rings",
    "max_ring_size",
    "keep_stereo",
    "keep_isotope_molecules",
    "uncharge",
    "canonical_tautomer",
    "kekulize",
    "randomize_smiles",
    "report_errors",
    "inchi_key_deduplicate",
}
COMMON_ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
    "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
    "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
}
TOKEN_PATTERN = re.compile(
    r"(\[[^]]+]|Br?|Cl?|N|O|S|P|F|I|b|c|n|o|s|p|-|=|#|\$|:|\\|/|\(|\)|%\d{2}|\d|\.|\*)"
)
BRACKET_ELEMENT_PATTERN = re.compile(r"\[\d*([A-Za-z]{1,3})")
PLAIN_ELEMENT_PATTERN = re.compile(r"Br|Cl|B|C|N|O|S|P|F|I|b|c|n|o|s|p")
UNWANTED_HALOGEN_PATTERN = re.compile(r"\[\d*(F|Cl|Br|I)(H|[+-]|\d|@)?.*]")


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def as_dict(self) -> dict[str, list[str]]:
        return {"errors": self.errors, "warnings": self.warnings, "notes": self.notes}

    def print_text(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARN: {message}")
        for message in self.notes:
            print(f"OK: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a REINVENT4 reinvent_datapre TOML config without running preprocessing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("config", type=Path, help="Path to data_pipeline.toml")
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Resolve relative input, output, and transform paths against this directory; defaults to config parent.",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=10,
        help="Number of input rows to sample-check from the selected SMILES column; use 0 to skip.",
    )
    parser.add_argument(
        "--allow-output-overwrite",
        action="store_true",
        help="Suppress warning when output_smiles_file already exists.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are present.")
    return parser.parse_args()


def load_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:
        raise RuntimeError("TOML parsing requires Python 3.11+ tomllib")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise RuntimeError("Config root must be a table/object")
    return data


def resolve_path(base_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(os.path.expanduser(value))
    if not path.is_absolute():
        path = base_dir / path
    return path


def is_smi_path(path: Path) -> bool:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    return suffixes == [".smi"] or suffixes == [".smi", ".gz"]


def display_separator(separator: str) -> str:
    if separator == "\t":
        return "tab"
    if separator == " ":
        return "space"
    return repr(separator)


def check_int(reporter: Reporter, label: str, value: Any, *, minimum: int = 1) -> None:
    if not isinstance(value, int) or value < minimum:
        reporter.error(f"{label} must be an integer >= {minimum}")


def check_number(reporter: Reporter, label: str, value: Any, *, minimum: float = 1.0) -> None:
    if not isinstance(value, (int, float)) or float(value) < minimum:
        reporter.error(f"{label} must be a number >= {minimum:g}")


def check_bool(reporter: Reporter, label: str, value: Any) -> None:
    if not isinstance(value, bool):
        reporter.error(f"{label} must be true or false")


def get_transform_file_name(path: Path, reporter: Reporter) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
    except OSError as exc:
        reporter.error(f"transform_file cannot be read: {exc}")
        return "from_file"
    if first_line.startswith("// TRANSFORM_NAME:"):
        name = first_line.replace("// TRANSFORM_NAME:", "", 1).strip()
        if name:
            reporter.note(f"transform_file declares transform name {name!r}")
            return name
        reporter.warn("transform_file has an empty // TRANSFORM_NAME declaration; runtime will not get a useful custom name")
    return "from_file"


def validate_schema(
    config: dict[str, Any], reporter: Reporter, base_dir: Path, allow_output_overwrite: bool
) -> tuple[Path | None, str, str, set[str]]:
    unknown_top = sorted(set(config) - ALLOWED_TOP_LEVEL)
    if unknown_top:
        reporter.error(f"unknown top-level keys rejected by runtime schema: {', '.join(unknown_top)}")

    for key in ("input_csv_file", "output_smiles_file"):
        if not isinstance(config.get(key), str) or not config.get(key):
            reporter.error(f"{key} is required and must be a non-empty string")

    smiles_column = config.get("smiles_column", "SMILES")
    if not isinstance(smiles_column, str) or not smiles_column:
        reporter.error("smiles_column must be a non-empty string")
        smiles_column = "SMILES"

    separator = config.get("separator", "\t")
    if not isinstance(separator, str) or len(separator) != 1:
        reporter.error("separator must be exactly one character, for example '\\t' or ','")
        separator = "\t"
    else:
        reporter.note(f"separator is {display_separator(separator)}")

    check_int(reporter, "num_procs", config.get("num_procs", 1))
    check_int(reporter, "chunk_size", config.get("chunk_size", 500))

    input_path = resolve_path(base_dir, config.get("input_csv_file"))
    if input_path is not None:
        if input_path.exists():
            reporter.note(f"input_csv_file exists: {config.get('input_csv_file')}")
        else:
            reporter.error(f"input_csv_file does not exist: {config.get('input_csv_file')}")

    output_path = resolve_path(base_dir, config.get("output_smiles_file"))
    if output_path is not None:
        if output_path.parent.exists():
            reporter.note(f"output parent exists: {output_path.parent}")
        else:
            reporter.error(f"output parent does not exist: {output_path.parent}")
        if output_path.exists() and not allow_output_overwrite:
            reporter.warn(f"output_smiles_file already exists and will be overwritten: {config.get('output_smiles_file')}")
        if output_path.suffix.lower() != ".smi":
            reporter.warn("output_smiles_file usually ends with .smi and contains one SMILES per line")

    filter_config = config.get("filter")
    if not isinstance(filter_config, dict):
        reporter.error("[filter] table is required for practical reinvent_datapre runs")
        filter_config = {}

    unknown_filter = sorted(set(filter_config) - ALLOWED_FILTER_KEYS)
    if unknown_filter:
        reporter.error(f"unknown [filter] keys rejected by runtime schema: {', '.join(unknown_filter)}")

    elements = filter_config.get("elements", [])
    configured_elements: set[str] = set()
    if not isinstance(elements, list) or not all(isinstance(item, str) and item for item in elements):
        reporter.error("filter.elements must be a list of element-symbol strings")
    else:
        configured_elements = set(elements)
        invalid = sorted(element for element in configured_elements if element not in COMMON_ELEMENTS)
        if invalid:
            reporter.error(f"filter.elements contains invalid periodic-table symbols: {', '.join(invalid)}")
        allowed = sorted(BASE_ELEMENTS | configured_elements)
        reporter.note("runtime allowed elements include: " + ", ".join(allowed))

    transforms = filter_config.get("transforms", ["standard"])
    if not isinstance(transforms, list) or not all(isinstance(item, str) and item for item in transforms):
        reporter.error("filter.transforms must be a list of transform-name strings")
        transforms = []

    transform_file_path = resolve_path(base_dir, config.get("transform_file"))
    transform_file_name = None
    if transform_file_path is not None:
        if transform_file_path.exists():
            transform_file_name = get_transform_file_name(transform_file_path, reporter)
        else:
            reporter.error(f"transform_file does not exist: {config.get('transform_file')}")
            transform_file_name = "from_file"

    for transform in transforms:
        if transform in BUILTIN_TRANSFORMS:
            continue
        if transform_file_name and transform in {"from_file", transform_file_name}:
            continue
        reporter.error(
            f"filter.transforms contains unknown transform {transform!r}; expected built-ins {sorted(BUILTIN_TRANSFORMS)}"
            + (" or the transform_file name" if transform_file_name else " or configure transform_file")
        )

    int_defaults = {
        "min_heavy_atoms": 2,
        "max_heavy_atoms": 90,
        "min_carbons": 2,
        "max_num_rings": 12,
        "max_ring_size": 7,
    }
    for key, default in int_defaults.items():
        check_int(reporter, f"filter.{key}", filter_config.get(key, default))
    check_number(reporter, "filter.max_mol_weight", filter_config.get("max_mol_weight", 1200.0))

    if isinstance(filter_config.get("min_heavy_atoms", 2), int) and isinstance(filter_config.get("max_heavy_atoms", 90), int):
        if filter_config.get("min_heavy_atoms", 2) > filter_config.get("max_heavy_atoms", 90):
            reporter.error("filter.min_heavy_atoms is greater than filter.max_heavy_atoms")

    for key in (
        "keep_stereo",
        "keep_isotope_molecules",
        "uncharge",
        "canonical_tautomer",
        "kekulize",
        "randomize_smiles",
        "report_errors",
        "inchi_key_deduplicate",
    ):
        if key in filter_config:
            check_bool(reporter, f"filter.{key}", filter_config[key])

    if filter_config.get("randomize_smiles"):
        reporter.warn("filter.randomize_smiles makes output non-deterministic; keep false for validation runs")
    if filter_config.get("canonical_tautomer"):
        reporter.warn("filter.canonical_tautomer can be slow; benchmark on a subset before scaling")
    if config.get("num_procs", 1) != 1:
        reporter.warn("start with num_procs = 1 for clearer discarded-token logging before scaling")

    return input_path, smiles_column, separator, BASE_ELEMENTS | configured_elements


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def token_sample_warnings(smiles: str, allowed_elements: set[str]) -> list[str]:
    warnings: list[str] = []
    stripped = smiles.strip()
    if not stripped:
        return ["empty SMILES"]
    if any(char.isspace() for char in stripped):
        warnings.append("contains whitespace inside selected field")
    if UNWANTED_HALOGEN_PATTERN.search(stripped):
        warnings.append("contains charged/high-valent halogen token rejected by regex filter")
    tokens = TOKEN_PATTERN.findall(stripped)
    if not tokens:
        warnings.append("no recognizable SMILES tokens")
        return warnings
    joined = "".join(tokens)
    if joined != stripped:
        warnings.append("contains characters outside REINVENT4 data-pipeline token regex")
    found_elements: set[str] = set()
    for token in tokens:
        bracket_match = BRACKET_ELEMENT_PATTERN.match(token)
        if bracket_match:
            raw = bracket_match.group(1)
            element = raw.rstrip("H").title()
            if element:
                found_elements.add(element)
            continue
        plain_match = PLAIN_ELEMENT_PATTERN.fullmatch(token)
        if plain_match:
            raw = plain_match.group(0)
            found_elements.add(raw.title())
    unexpected = sorted(element for element in found_elements if element not in allowed_elements and element != "H")
    if unexpected:
        warnings.append("contains elements outside configured runtime set: " + ", ".join(unexpected))
    if len(tokens) < 2:
        warnings.append("very few tokens; may fail min_heavy_atoms/min_carbons")
    return warnings


def sample_input(
    reporter: Reporter,
    input_path: Path | None,
    smiles_column: str,
    separator: str,
    sample_rows: int,
    allowed_elements: set[str],
) -> None:
    if sample_rows <= 0 or input_path is None or not input_path.exists():
        return

    sampled = 0
    suspicious = 0
    try:
        with open_text(input_path) as handle:
            if is_smi_path(input_path):
                reader = csv.reader(handle, delimiter=separator)
                for row_number, row in enumerate(reader, start=1):
                    if sampled >= sample_rows:
                        break
                    if not row:
                        continue
                    sampled += 1
                    for warning in token_sample_warnings(row[0], allowed_elements):
                        suspicious += 1
                        reporter.warn(f"row {row_number}: {warning}: {row[0]!r}")
            else:
                reader = csv.DictReader(handle, delimiter=separator)
                if reader.fieldnames is None:
                    reporter.error("input file has no header row")
                    return
                if smiles_column not in reader.fieldnames:
                    reporter.error(
                        f"smiles_column {smiles_column!r} not found in header {reader.fieldnames}; check separator/header"
                    )
                    return
                reporter.note(f"smiles_column {smiles_column!r} found in header")
                for row_number, row in enumerate(reader, start=2):
                    if sampled >= sample_rows:
                        break
                    value = row.get(smiles_column, "")
                    sampled += 1
                    for warning in token_sample_warnings(value, allowed_elements):
                        suspicious += 1
                        reporter.warn(f"row {row_number}: {warning}: {value!r}")
    except UnicodeDecodeError as exc:
        reporter.error(f"input file is not UTF-8 text: {exc}")
        return
    except csv.Error as exc:
        reporter.error(f"input file could not be parsed with separator {display_separator(separator)}: {exc}")
        return
    except OSError as exc:
        reporter.error(f"input file could not be read: {exc}")
        return

    if sampled == 0:
        reporter.warn("sample check found no data rows")
    elif suspicious == 0:
        reporter.note(f"sample check inspected {sampled} row(s) with no obvious token/element warnings")
    else:
        reporter.warn(f"sample check inspected {sampled} row(s) and found {suspicious} warning(s)")


def main() -> int:
    args = parse_args()
    reporter = Reporter()
    config_path = args.config.expanduser()
    if not config_path.exists():
        reporter.error(f"config does not exist: {args.config}")
        if args.json:
            print(json.dumps(reporter.as_dict(), indent=2))
        else:
            reporter.print_text()
        return 2

    try:
        config = load_toml(config_path)
    except Exception as exc:
        reporter.error(f"failed to parse TOML config: {exc}")
        if args.json:
            print(json.dumps(reporter.as_dict(), indent=2))
        else:
            reporter.print_text()
        return 2

    base_dir = (args.base_dir or config_path.parent).expanduser().resolve()
    if not base_dir.exists():
        reporter.error(f"base directory does not exist: {base_dir}")
    input_path, smiles_column, separator, allowed_elements = validate_schema(
        config, reporter, base_dir, args.allow_output_overwrite
    )
    sample_input(reporter, input_path, smiles_column, separator, args.sample_rows, allowed_elements)

    if args.json:
        print(json.dumps(reporter.as_dict(), indent=2))
    else:
        reporter.print_text()

    if reporter.has_errors:
        return 2
    if args.strict and reporter.has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
