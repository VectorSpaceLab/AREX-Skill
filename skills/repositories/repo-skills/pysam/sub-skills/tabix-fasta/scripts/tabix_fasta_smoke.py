#!/usr/bin/env python3
"""Create tiny source-free tabix, FASTA, and FASTQ fixtures and print JSON."""

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
        "--outdir",
        type=Path,
        default=None,
        help="Directory for generated fixture files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary directory when --outdir is not supplied.",
    )
    return parser


def run_tabix(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    bed_path = outdir / "tiny.bed"
    bed_path.write_text("chr1\t10\t20\tfeatureA\nchr1\t30\t40\tfeatureB\n", encoding="utf-8")
    compressed_path = outdir / "tiny.bed.gz"

    pysam_module.tabix_compress(os.fspath(bed_path), os.fspath(compressed_path), force=True)
    indexed_path = pysam_module.tabix_index(os.fspath(compressed_path), preset="bed", force=True)

    with pysam_module.TabixFile(indexed_path, parser=pysam_module.asBed()) as table:
        hits = list(table.fetch("chr1", 0, 25))
        chr1_rows = list(table.fetch("chr1"))
        tuple_hits = list(table.fetch("chr1", 0, 25, parser=pysam_module.asTuple()))
        summary = {
            "compressed_exists": compressed_path.exists(),
            "index_exists": Path(f"{indexed_path}.tbi").exists(),
            "contigs": list(table.contigs),
            "hit_names": [getattr(row, "name", None) for row in hits],
            "hit_intervals": [(row.contig, int(row.start), int(row.end)) for row in hits],
            "chr1_row_count": len(chr1_rows),
            "tuple_first": list(tuple_hits[0]) if tuple_hits else None,
        }
    return summary


def run_fasta(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    fasta_path = outdir / "tiny.fa"
    fasta_path.write_text(">chr1\nACGTACGTACGT\n>chr2\nTTTTCCCC\n", encoding="utf-8")
    pysam_module.faidx(os.fspath(fasta_path))

    with pysam_module.FastaFile(os.fspath(fasta_path)) as fasta:
        return {
            "fai_exists": fasta_path.with_suffix(".fa.fai").exists(),
            "references": list(fasta.references),
            "lengths": list(fasta.lengths),
            "chr1_2_6": fasta.fetch("chr1", 2, 6),
            "chr2_region": fasta.fetch(region="chr2:1-4"),
            "chr1_length": fasta.get_reference_length("chr1"),
        }


def run_fastx(pysam_module: Any, outdir: Path) -> dict[str, Any]:
    fastq_path = outdir / "tiny.fq"
    fastq_path.write_text("@read1 comment\nACGT\n+\nIIII\n@read2\nTGCA\n+\n####\n", encoding="utf-8")

    records = []
    with pysam_module.FastxFile(os.fspath(fastq_path), persist=True) as fastx:
        for record in fastx:
            qualities = record.get_quality_array() if record.quality is not None else None
            records.append(
                {
                    "name": record.name,
                    "comment": record.comment,
                    "sequence": record.sequence,
                    "quality": record.quality,
                    "qualities": list(qualities) if qualities is not None else None,
                }
            )
    return {"record_count": len(records), "records": records}


def run(args: argparse.Namespace) -> dict[str, Any]:
    import pysam

    temp_dir = None
    if args.outdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="pysam-tabix-fasta-smoke-")
        outdir = Path(temp_dir.name)
    else:
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        result = {
            "ok": True,
            "pysam_version": getattr(pysam, "__version__", None),
            "tabix": run_tabix(pysam, outdir),
            "fasta": run_fasta(pysam, outdir),
            "fastx": run_fastx(pysam, outdir),
        }
    finally:
        if temp_dir is not None and not args.keep:
            temp_dir.cleanup()

    if temp_dir is not None:
        result["temporary_directory_removed"] = not args.keep
    return result


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(run(args), sort_keys=True))


if __name__ == "__main__":
    main()
