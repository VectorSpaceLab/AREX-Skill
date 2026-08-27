#!/usr/bin/env python3
"""Check an installed pysam environment with source-free imports and tiny operations."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-operations",
        action="store_true",
        help="Only run import/version checks; skip tiny source-free operations.",
    )
    return parser


def import_checks() -> dict[str, Any]:
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
    result = {}
    for module in modules:
        try:
            __import__(module)
        except Exception as exc:
            result[module] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        else:
            result[module] = {"ok": True}
    return result


def tiny_alignment(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    bam_path = outdir / "root-check.bam"
    header = {"HD": {"VN": "1.6"}, "SQ": [{"SN": "chr1", "LN": 100}]}
    read = pysam_module.AlignedSegment()
    read.query_name = "read1"
    read.query_sequence = "ACGT"
    read.flag = 0
    read.reference_id = 0
    read.reference_start = 5
    read.mapping_quality = 20
    read.cigarstring = "4M"
    read.query_qualities = pysam_module.qualitystring_to_array("IIII")
    with pysam_module.AlignmentFile(os.fspath(bam_path), "wb", header=header) as out_bam:
        out_bam.write(read)
    with pysam_module.AlignmentFile(os.fspath(bam_path), "rb") as in_bam:
        reads = list(in_bam.fetch(until_eof=True))
    return {"ok": len(reads) == 1, "read_names": [item.query_name for item in reads]}


def tiny_variant(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    vcf_path = outdir / "root-check.vcf"
    header = pysam_module.VariantHeader()
    header.add_meta("fileformat", value="VCFv4.2")
    header.contigs.add("chr1", length=100)
    header.info.add("DP", 1, "Integer", "Depth")
    record = header.new_record(contig="chr1", start=9, stop=10, alleles=("A", "C"), info={"DP": 3})
    with pysam_module.VariantFile(os.fspath(vcf_path), "w", header=header) as out_vcf:
        out_vcf.write(record)
    with pysam_module.VariantFile(os.fspath(vcf_path)) as in_vcf:
        observed = next(in_vcf.fetch())
    return {"ok": observed.contig == "chr1" and observed.info["DP"] == 3, "pos": observed.pos}


def tiny_tabix_fasta(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    bed_path = outdir / "root-check.bed"
    bed_path.write_text("chr1\t0\t5\ta\n", encoding="utf-8")
    gz_path = outdir / "root-check.bed.gz"
    pysam_module.tabix_compress(os.fspath(bed_path), os.fspath(gz_path), force=True)
    indexed = pysam_module.tabix_index(os.fspath(gz_path), preset="bed", force=True)
    with pysam_module.TabixFile(indexed, parser=pysam_module.asBed()) as table:
        rows = list(table.fetch("chr1", 0, 5))

    fasta_path = outdir / "root-check.fa"
    fasta_path.write_text(">chr1\nACGTAC\n", encoding="utf-8")
    pysam_module.faidx(os.fspath(fasta_path))
    with pysam_module.FastaFile(os.fspath(fasta_path)) as fasta:
        sequence = fasta.fetch("chr1", 1, 4)
    return {"ok": len(rows) == 1 and sequence == "CGT", "tabix_rows": len(rows), "fasta_slice": sequence}


def run(skip_operations: bool) -> dict[str, Any]:
    imports = import_checks()
    result: dict[str, Any] = {"imports": imports, "ok": all(item["ok"] for item in imports.values())}
    if not result["ok"]:
        return result

    import pysam

    result["versions"] = {
        "pysam": getattr(pysam, "__version__", None),
        "samtools": getattr(pysam, "__samtools_version__", None),
        "bcftools": getattr(pysam, "__bcftools_version__", None),
        "htslib": getattr(pysam, "__htslib_version__", None),
    }
    result["command_wrappers"] = {
        "samtools_flagstat": hasattr(pysam.samtools, "flagstat"),
        "bcftools_view": hasattr(pysam.bcftools, "view"),
        "top_level_sort": hasattr(pysam, "sort"),
    }
    if skip_operations:
        result["operations_skipped"] = True
        return result

    with tempfile.TemporaryDirectory(prefix="pysam-root-check-") as temp_dir:
        outdir = Path(temp_dir)
        result["operations"] = {
            "alignment": tiny_alignment(pysam, outdir),
            "variant": tiny_variant(pysam, outdir),
            "tabix_fasta": tiny_tabix_fasta(pysam, outdir),
        }
    result["ok"] = result["ok"] and all(item.get("ok") for item in result["operations"].values())
    return result


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(run(args.skip_operations), sort_keys=True))


if __name__ == "__main__":
    main()
