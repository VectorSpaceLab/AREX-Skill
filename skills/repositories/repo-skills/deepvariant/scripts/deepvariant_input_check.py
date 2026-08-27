#!/usr/bin/env python3
"""Lightweight DeepVariant input preflight checks.

This helper checks common path, index, output, model-type, and region mistakes
for DeepVariant-style workflows. It does not parse genomics file headers, run
DeepVariant, execute containers, download data, or validate biological accuracy.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

MODEL_TYPES = {
    "germline": {"WGS", "WES", "PACBIO", "ONT_R104", "HYBRID_PACBIO_ILLUMINA", "MASSEQ", "RNASEQ"},
    "trio": {"WGS", "WES", "PACBIO", "ONT"},
    "pangenome": {"WGS", "WES"},
}

READ_INDEXES = {
    ".bam": [".bai", ".csi"],
    ".cram": [".crai"],
}


def existing_companion(path: Path, suffixes: list[str]) -> str | None:
    candidates = []
    for suffix in suffixes:
        candidates.append(Path(str(path) + suffix))
        if path.suffix:
            candidates.append(path.with_suffix(suffix))
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def read_fai_contigs(ref: Path) -> set[str]:
    candidates = [Path(str(ref) + ".fai")]
    if ref.suffix in {".gz", ".bgz"}:
        candidates.append(ref.with_suffix(""))
    contigs: set[str] = set()
    for fai in candidates:
        if not fai.exists():
            continue
        with fai.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if line.strip():
                    contigs.add(line.split("\t", 1)[0])
        if contigs:
            return contigs
    return contigs


def region_contig(region: str) -> str | None:
    if not region or region.startswith("/") or region.endswith(".bed") or "," in region:
        return None
    match = re.match(r"^([^:]+)(?::[0-9,]+-[0-9,]+)?$", region)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check common DeepVariant input and command-shape mistakes.")
    parser.add_argument("--workflow", choices=sorted(MODEL_TYPES), default="germline")
    parser.add_argument("--model-type", required=True, help="DeepVariant/DeepTrio model type for the selected workflow.")
    parser.add_argument("--ref", required=True, help="Reference FASTA path.")
    parser.add_argument("--reads", action="append", default=[], help="BAM/CRAM path. Repeat for trio child/parent reads.")
    parser.add_argument("--output-vcf", action="append", default=[], help="Planned output VCF path. Repeat for per-sample outputs.")
    parser.add_argument("--output-gvcf", action="append", default=[], help="Optional output gVCF path. Repeat for per-sample outputs.")
    parser.add_argument("--regions", action="append", default=[], help="Region literal or BED path. Repeat as needed.")
    parser.add_argument("--pangenome", help="GBZ pangenome path for pangenome-aware workflows.")
    parser.add_argument("--customized-model", help="Custom model directory or checkpoint/SavedModel path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    facts: dict[str, object] = {"workflow": args.workflow, "model_type": args.model_type}

    allowed = MODEL_TYPES[args.workflow]
    if args.model_type not in allowed:
        errors.append(f"model type {args.model_type!r} is not valid for {args.workflow}; choose one of {sorted(allowed)}")

    ref = Path(args.ref)
    if not ref.exists():
        errors.append(f"reference FASTA does not exist: {args.ref}")
    elif not Path(str(ref) + ".fai").exists():
        errors.append(f"reference FASTA index is missing: {args.ref}.fai")
    contigs = read_fai_contigs(ref) if ref.exists() else set()
    if contigs:
        facts["fai_contig_count"] = len(contigs)

    if not args.reads:
        warnings.append("no --reads paths supplied; command shape cannot be fully checked")
    for reads in args.reads:
        read_path = Path(reads)
        if not read_path.exists():
            errors.append(f"reads path does not exist: {reads}")
            continue
        suffix = read_path.suffix.lower()
        if suffix not in READ_INDEXES:
            warnings.append(f"reads path does not end in .bam or .cram: {reads}")
            continue
        if not existing_companion(read_path, READ_INDEXES[suffix]):
            errors.append(f"missing index companion for {reads}; expected one of {READ_INDEXES[suffix]}")

    for output in args.output_vcf + args.output_gvcf:
        parent = Path(output).expanduser().parent
        if str(parent) and not parent.exists():
            errors.append(f"output parent directory does not exist: {parent}")

    for region in args.regions:
        region_path = Path(region)
        if region.endswith(".bed") or region_path.exists():
            if not region_path.exists():
                errors.append(f"region BED path does not exist: {region}")
            continue
        contig = region_contig(region)
        if contig and contigs and contig not in contigs:
            errors.append(f"region contig {contig!r} is not present in the reference .fai")

    if args.workflow == "pangenome":
        if not args.pangenome:
            errors.append("pangenome workflow requires --pangenome GBZ path")
        elif not Path(args.pangenome).exists():
            errors.append(f"pangenome GBZ path does not exist: {args.pangenome}")
    elif args.pangenome:
        warnings.append("--pangenome was supplied for a non-pangenome workflow; route to pangenome-aware-calling if intentional")

    if args.customized_model:
        model_path = Path(args.customized_model)
        if not model_path.exists():
            errors.append(f"customized model path does not exist: {args.customized_model}")
        else:
            metadata_candidates = [model_path / "model.example_info.json", model_path / "example_info.json"] if model_path.is_dir() else [model_path.with_name("model.example_info.json")]
            if not any(candidate.exists() for candidate in metadata_candidates):
                warnings.append("customized model metadata was not found nearby; validate model.example_info.json before inference")

    report = {"ok": not errors, "errors": errors, "warnings": warnings, "facts": facts}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepVariant input preflight:", "PASS" if report["ok"] else "FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
