#!/usr/bin/env python3
"""Safe input validator for OmicVerse specialist-domain workflows.

The script performs read-only checks for GWAS summary statistics, AIRR/VDJ
schemas, FASTQ pair naming, and molecular target identifiers. It never runs
external bioinformatics binaries, installs packages, or downloads data.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

GWAS_ALIASES = {
    "SNP": {"snp", "rsid", "rs_id", "markername", "marker", "variant", "variant_id", "id"},
    "CHR": {"chr", "chrom", "chromosome", "#chrom"},
    "BP": {"bp", "pos", "position", "base_pair_location"},
    "A1": {"a1", "ea", "effect_allele", "alt", "tested_allele"},
    "A2": {"a2", "nea", "other_allele", "non_effect_allele", "ref"},
    "BETA": {"beta", "effect", "effect_size", "estimate", "b"},
    "SE": {"se", "stderr", "standard_error", "beta_se"},
    "OR": {"or", "odds_ratio"},
    "Z": {"z", "zscore", "z_score", "zstat"},
    "P": {"p", "pval", "pvalue", "p_value", "p-value", "p.value"},
    "N": {"n", "samplesize", "n_total", "sample_size"},
    "EAF": {"eaf", "freq", "maf", "af", "effect_allele_frequency"},
    "INFO": {"info", "imputation_info", "rsq"},
}

GWAS_MODE_REQUIREMENTS = {
    "basic": {"SNP", "P"},
    "association": {"SNP", "BETA", "SE", "P"},
    "coloc": {"SNP", "BETA", "SE", "N"},
    "mr": {"SNP", "BETA", "SE", "A1", "A2"},
}

AIRR_CONTIG_REQUIRED_ANY = [
    {"barcode", "chain"},
    {"cell_id", "locus"},
    {"sequence_id"},
]
AIRR_RECOMMENDED = {
    "v_gene", "v_call", "j_gene", "j_call", "cdr3", "junction_aa",
    "cdr3_nt", "junction", "umis", "duplicate_count", "productive",
}
AIRR_OBS_MINIMUM_ANY = [
    {"has_ir", "receptor_type"},
    {"VJ_1_junction_aa", "VDJ_1_junction_aa"},
    {"clone_id"},
]
AIRR_CHAIN_FIELDS = ("v_gene", "d_gene", "j_gene", "c_gene", "junction", "junction_aa", "locus", "duplicate_count", "productive")
AIRR_SLOTS = ("VJ_1", "VJ_2", "VDJ_1", "VDJ_2")

FASTQ_EXTENSIONS = (
    ".fastq", ".fq", ".fastq.gz", ".fq.gz", ".fastq.bz2", ".fq.bz2"
)
R1_PATTERNS = (
    re.compile(r"(?P<prefix>.+?)(?:_S\d+)?(?:_L\d{3})?_R1(?:_\d{3})?(?P<ext>\.f(?:ast)?q(?:\.gz|\.bz2)?)$", re.I),
    re.compile(r"(?P<prefix>.+?)(?:[._-])1(?P<ext>\.f(?:ast)?q(?:\.gz|\.bz2)?)$", re.I),
)
R2_MARKERS = ("_R2", ".R2", "-R2", "_2.", ".2.", "-2.")
SAFE_SAMPLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

PDB_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")
UNIPROT_RE = re.compile(r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9](?:-[0-9]+)?)$")
GENE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{1,19}$")
AA_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYXBZUOJ*\-]+$", re.I)


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="")
    return path.open("r", newline="")


def sniff_delimiter(path: Path, default: str = "\t") -> str:
    with open_text(path) as handle:
        sample = handle.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,; ")
        return dialect.delimiter
    except csv.Error:
        if "," in sample and "\t" not in sample:
            return ","
        return default


def read_header(path: Path, delimiter: str | None = None) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    sep = delimiter or sniff_delimiter(path)
    with open_text(path) as handle:
        reader = csv.reader(handle, delimiter=sep)
        for row in reader:
            if row and any(cell.strip() for cell in row):
                return [cell.strip().lstrip("\ufeff") for cell in row]
    return []


def detect_gwas_columns(columns: Iterable[str]) -> dict[str, str]:
    lower = {col.lower().strip(): col for col in columns}
    detected: dict[str, str] = {}
    for canonical, aliases in GWAS_ALIASES.items():
        for alias in aliases:
            if alias in lower:
                detected[canonical] = lower[alias]
                break
    return detected


def warn_duplicate_columns(columns: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for col in columns:
        key = col.lower().strip()
        if key in seen:
            dupes.add(col)
        seen.add(key)
    return sorted(dupes)


def check_gwas(args: argparse.Namespace) -> tuple[int, dict]:
    path = Path(args.path)
    delimiter = args.delimiter.encode().decode("unicode_escape") if args.delimiter else None
    columns = read_header(path, delimiter)
    detected = detect_gwas_columns(columns)
    required = set(GWAS_MODE_REQUIREMENTS[args.mode])
    if args.mode in {"coloc", "mr"}:
        required |= {"A1", "A2"} if args.require_alleles else set()
    missing = sorted(required - set(detected))
    recommended = sorted(({"CHR", "BP", "EAF", "N"} - set(detected)) & set(GWAS_ALIASES))
    result = {
        "kind": "gwas",
        "path": str(path),
        "mode": args.mode,
        "columns": columns,
        "detected": detected,
        "missing_required": missing,
        "missing_recommended": recommended,
        "duplicate_columns": warn_duplicate_columns(columns),
        "notes": [],
    }
    if "OR" in detected and "BETA" not in detected:
        result["notes"].append("OR detected without BETA; effect-scale workflows may need log(OR).")
    if "A1" in detected and "A2" in detected and "EAF" not in detected:
        result["notes"].append("Alleles detected but EAF missing; palindromic SNP harmonization may be ambiguous.")
    status = 1 if missing else 0
    return status, result


def check_airr_vdj(args: argparse.Namespace) -> tuple[int, dict]:
    path = Path(args.path)
    delimiter = args.delimiter.encode().decode("unicode_escape") if args.delimiter else None
    columns = read_header(path, delimiter)
    names = {col.strip() for col in columns}
    lower = {col.lower().strip(): col for col in columns}
    lower_names = set(lower)
    matched_source_schema = [sorted(req) for req in AIRR_CONTIG_REQUIRED_ANY if req <= lower_names]
    recommended_present = sorted({lower[c] for c in lower_names if c in AIRR_RECOMMENDED})
    missing_recommended = sorted(AIRR_RECOMMENDED - lower_names)
    result = {
        "kind": "airr-vdj",
        "path": str(path),
        "columns": columns,
        "matched_source_schema": matched_source_schema,
        "recommended_present": recommended_present,
        "missing_recommended": missing_recommended,
        "duplicate_columns": warn_duplicate_columns(columns),
        "notes": [],
    }
    if not matched_source_schema:
        result["notes"].append("Expected a 10x-style barcode/chain table, an AIRR cell_id/locus table, or sequence_id for cell inference.")
    if "cell_id" not in lower_names and "barcode" not in lower_names and "sequence_id" in lower_names:
        result["notes"].append("cell_id can be inferred only when sequence_id carries cell prefixes such as *_contig*.")
    status = 0 if matched_source_schema else 1
    return status, result


def check_airr_obs(args: argparse.Namespace) -> tuple[int, dict]:
    path = Path(args.path)
    delimiter = args.delimiter.encode().decode("unicode_escape") if args.delimiter else None
    columns = read_header(path, delimiter)
    names = set(columns)
    chain_columns = sorted(col for col in columns if any(col.startswith(f"{slot}_") for slot in AIRR_SLOTS))
    expected_chain = [f"{slot}_{field}" for slot in AIRR_SLOTS for field in AIRR_CHAIN_FIELDS]
    present_chain_expected = sorted(set(expected_chain) & names)
    matched_minimum = [sorted(req) for req in AIRR_OBS_MINIMUM_ANY if req <= names]
    result = {
        "kind": "airr-obs",
        "path": str(path),
        "columns": columns,
        "matched_minimum": matched_minimum,
        "chain_columns_found": chain_columns,
        "expected_chain_columns_present": present_chain_expected,
        "missing_common": sorted({"has_ir", "receptor_type", "clone_id"} - names),
        "duplicate_columns": warn_duplicate_columns(columns),
        "notes": [],
    }
    if not chain_columns:
        result["notes"].append("No OmicVerse AIRR chain-slot columns found, such as VJ_1_junction_aa or VDJ_1_locus.")
    if "clone_id" not in names:
        result["notes"].append("clonal_expansion requires clone_id or a custom target_col.")
    status = 0 if chain_columns or matched_minimum else 1
    return status, result


def is_fastq(path: Path) -> bool:
    lowered = path.name.lower()
    return lowered.endswith(FASTQ_EXTENSIONS)


def sample_from_r1(name: str) -> tuple[str, str] | None:
    for pattern in R1_PATTERNS:
        match = pattern.match(name)
        if match:
            prefix = match.group("prefix")
            ext = match.group("ext")
            sample = re.sub(r"(?:_S\d+)?(?:_L\d{3})$", "", prefix, flags=re.I)
            return sample, ext
    return None


def candidate_r2_names(r1_name: str) -> list[str]:
    candidates = []
    replacements = [("_R1", "_R2"), (".R1", ".R2"), ("-R1", "-R2"), ("_1.", "_2."), (".1.", ".2."), ("-1.", "-2.")]
    for src, dst in replacements:
        if src.lower() in r1_name.lower():
            idx = r1_name.lower().find(src.lower())
            candidates.append(r1_name[:idx] + dst + r1_name[idx + len(src):])
    return candidates


def check_fastq(args: argparse.Namespace) -> tuple[int, dict]:
    root = Path(args.path)
    files = sorted([p for p in root.rglob("*") if p.is_file() and is_fastq(p)] if root.is_dir() else [root])
    by_name = {p.name: p for p in files}
    samples = []
    orphan_r2 = []
    unsafe = []
    for path in files:
        parsed = sample_from_r1(path.name)
        if parsed:
            sample, _ext = parsed
            r2 = next((by_name[name] for name in candidate_r2_names(path.name) if name in by_name), None)
            if not SAFE_SAMPLE.match(sample):
                unsafe.append(sample)
            samples.append({"sample": sample, "r1": str(path), "r2": str(r2) if r2 else None})
        elif any(marker.lower() in path.name.lower() for marker in R2_MARKERS):
            orphan_r2.append(str(path))
    sample_names = [s["sample"] for s in samples]
    duplicate_samples = sorted(name for name in set(sample_names) if sample_names.count(name) > 1)
    result = {
        "kind": "fastq",
        "path": str(root),
        "fastq_files": len(files),
        "samples": samples,
        "n_samples": len(samples),
        "single_end_samples": [s["sample"] for s in samples if s["r2"] is None],
        "orphan_r2_files": orphan_r2,
        "duplicate_samples": duplicate_samples,
        "unsafe_sample_names": sorted(set(unsafe)),
        "notes": [],
    }
    if not samples:
        result["notes"].append("No R1 FASTQ files detected; provide explicit samples=[(sample, r1, r2)] if naming is nonstandard.")
    if orphan_r2:
        result["notes"].append("R2-looking files were found without matching R1 files.")
    if duplicate_samples:
        result["notes"].append("Duplicate sample names may collide in amplicon or alignment output directories.")
    if unsafe:
        result["notes"].append("Unsafe sample names should be renamed before pipeline execution.")
    status = 1 if (not samples or unsafe or duplicate_samples) else 0
    return status, result


def classify_target(value: str) -> dict:
    compact = value.strip()
    no_space = re.sub(r"\s+", "", compact)
    if PDB_RE.match(compact):
        kind = "pdb_id"
        note = "Use source='pdb' for experimental PDB structures."
    elif UNIPROT_RE.match(compact):
        kind = "uniprot_accession"
        note = "Suitable for AlphaFold/UniProt-backed structure lookup."
    elif len(no_space) >= 20 and AA_RE.match(no_space):
        kind = "amino_acid_sequence"
        note = "Use predict_structure only after network/API approval."
    elif GENE_RE.match(compact):
        kind = "gene_symbol"
        note = "Gene symbols require organism-aware UniProt resolution and network approval."
    else:
        kind = "unknown"
        note = "Expected a gene symbol, UniProt accession, PDB ID, or amino-acid sequence."
    return {"value": value, "kind": kind, "note": note}


def check_mol_target(args: argparse.Namespace) -> tuple[int, dict]:
    targets = []
    for item in args.targets:
        path = Path(item)
        if path.exists() and path.is_file():
            with path.open() as handle:
                targets.extend(line.strip() for line in handle if line.strip() and not line.startswith("#"))
        else:
            targets.append(item)
    classified = [classify_target(target) for target in targets]
    unknown = [entry for entry in classified if entry["kind"] == "unknown"]
    result = {
        "kind": "mol-target",
        "targets": classified,
        "n_targets": len(classified),
        "unknown_targets": unknown,
        "notes": ["This check does not query UniProt, AlphaFold, PDB, ChEMBL, RDKit, Vina, or fpocket."],
    }
    return (1 if unknown else 0), result


def emit(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"kind: {result.get('kind')}")
    for key, value in result.items():
        if key == "kind":
            continue
        print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only validator for OmicVerse genetics, AIRR, alignment FASTQ, and molecular inputs."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    gwas = sub.add_parser("gwas", help="Validate GWAS/eQTL/coloc/MR summary-stat columns.")
    gwas.add_argument("path", help="CSV/TSV/whitespace-delimited summary-stat table; .gz is supported.")
    gwas.add_argument("--mode", choices=sorted(GWAS_MODE_REQUIREMENTS), default="basic", help="Required-column profile.")
    gwas.add_argument("--delimiter", help="Delimiter override, e.g. '\\t' or ','.")
    gwas.add_argument("--require-alleles", action="store_true", help="Require A1/A2 even when the mode does not normally require them.")
    gwas.set_defaults(func=check_gwas)

    airr_vdj = sub.add_parser("airr-vdj", help="Validate 10x/AIRR VDJ contig table columns.")
    airr_vdj.add_argument("path", help="VDJ contig CSV/TSV; .gz is supported.")
    airr_vdj.add_argument("--delimiter", help="Delimiter override, e.g. '\\t' or ','.")
    airr_vdj.set_defaults(func=check_airr_vdj)

    airr_obs = sub.add_parser("airr-obs", help="Validate exported AnnData .obs AIRR columns.")
    airr_obs.add_argument("path", help="CSV/TSV of AnnData obs columns; .gz is supported.")
    airr_obs.add_argument("--delimiter", help="Delimiter override, e.g. '\\t' or ','.")
    airr_obs.set_defaults(func=check_airr_obs)

    fastq = sub.add_parser("fastq", help="Validate FASTQ R1/R2 naming without reading sequence content.")
    fastq.add_argument("path", help="FASTQ file or directory to scan recursively.")
    fastq.set_defaults(func=check_fastq)

    mol = sub.add_parser("mol-target", help="Classify molecular target IDs without network lookup.")
    mol.add_argument("targets", nargs="+", help="Target strings or files containing one target per line.")
    mol.set_defaults(func=check_mol_target)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        status, result = args.func(args)
    except Exception as exc:  # keep CLI friendly for validators
        result = {"kind": getattr(args, "command", "unknown"), "error": str(exc)}
        emit(result, args.json)
        return 2
    emit(result, args.json)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
