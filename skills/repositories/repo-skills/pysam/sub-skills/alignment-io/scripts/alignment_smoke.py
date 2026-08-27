#!/usr/bin/env python3
"""Create and inspect a tiny pysam alignment file without external fixtures."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a tiny BAM with one mapped and one unmapped read, optionally "
            "index it, read it back with pysam, and print a JSON summary."
        )
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="Directory for generated files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--prefix",
        default="alignment_smoke",
        help="Filename prefix for generated BAM output.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary directory when --outdir is not supplied.",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip the indexing attempt and prove sequential until_eof reading only.",
    )
    return parser


def make_read(
    pysam_module: Any,
    name: str,
    sequence: str,
    reference_id: int,
    reference_start: int,
    cigarstring: str | None,
    flag: int,
) -> Any:
    read = pysam_module.AlignedSegment()
    read.query_name = name
    read.query_sequence = sequence
    read.flag = flag
    read.reference_id = reference_id
    read.reference_start = reference_start
    read.mapping_quality = 60 if reference_id >= 0 else 0
    read.cigarstring = cigarstring
    read.next_reference_id = -1
    read.next_reference_start = -1
    read.template_length = 0
    read.query_qualities = pysam_module.qualitystring_to_array("F" * len(sequence))
    if reference_id >= 0:
        read.set_tag("NM", 0)
    return read


def write_bam(pysam_module: Any, path: Path) -> None:
    header = {
        "HD": {"VN": "1.6", "SO": "coordinate"},
        "SQ": [{"SN": "chr1", "LN": 200}],
    }
    mapped = make_read(pysam_module, "mapped-read", "ACGTACGTAA", 0, 10, "10M", 0)
    unmapped = make_read(pysam_module, "unmapped-read", "TTTT", -1, -1, None, 4)
    with pysam_module.AlignmentFile(os.fspath(path), "wb", header=header) as out_bam:
        out_bam.write(mapped)
        out_bam.write(unmapped)


def try_index(pysam_module: Any, path: Path, skip: bool) -> dict[str, Any]:
    if skip:
        return {"attempted": False, "ok": False, "error": None}
    try:
        pysam_module.index(os.fspath(path))
    except Exception as exc:  # pragma: no cover - environment-dependent htslib errors
        return {"attempted": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"attempted": True, "ok": True, "error": None}


def inspect_bam(pysam_module: Any, path: Path, indexed: bool) -> dict[str, Any]:
    with pysam_module.AlignmentFile(os.fspath(path), "rb") as bam:
        until_eof_reads = list(bam.fetch(until_eof=True))
        mapped_reads = []
        coverage = None
        pileup = []
        if indexed:
            mapped_reads = list(bam.fetch("chr1", 10, 20))
            coverage_arrays = bam.count_coverage("chr1", 10, 20, quality_threshold=0, read_callback="all")
            coverage = [list(values) for values in coverage_arrays]
            for column in bam.pileup("chr1", 10, 20, truncate=True, min_base_quality=0):
                pileup.append(
                    {
                        "pos": column.reference_pos,
                        "depth": column.nsegments,
                        "names": column.get_query_names(),
                        "bases": column.get_query_sequences(),
                    }
                )

        first = until_eof_reads[0]
        qualities = pysam_module.qualities_to_qualitystring(first.query_qualities)
        roundtrip = pysam_module.array_to_qualitystring(pysam_module.qualitystring_to_array(qualities))
        return {
            "references": list(bam.references),
            "lengths": list(bam.lengths),
            "has_index": bam.has_index(),
            "until_eof": [summarize_read(read) for read in until_eof_reads],
            "fetch_region": [summarize_read(read) for read in mapped_reads],
            "coverage_acgt": coverage,
            "pileup": pileup,
            "quality_roundtrip": roundtrip,
            "reverse_complement": pysam_module.reverse_complement(first.query_sequence),
        }


def summarize_read(read: Any) -> dict[str, Any]:
    return {
        "query_name": read.query_name,
        "is_unmapped": read.is_unmapped,
        "reference_name": read.reference_name,
        "reference_start": read.reference_start,
        "reference_end": read.reference_end,
        "cigarstring": read.cigarstring,
        "mapping_quality": read.mapping_quality,
        "tags": read.get_tags(),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    import pysam

    temp_dir = None
    if args.outdir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="pysam-alignment-smoke-")
        outdir = Path(temp_dir.name)
    else:
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)

    bam_path = outdir / f"{args.prefix}.bam"
    write_bam(pysam, bam_path)
    index_status = try_index(pysam, bam_path, args.no_index)
    inspection = inspect_bam(pysam, bam_path, indexed=bool(index_status["ok"]))

    result = {
        "ok": True,
        "bam": os.fspath(bam_path),
        "index": index_status,
        "inspection": inspection,
    }
    if temp_dir is not None and not args.keep:
        result["temporary_directory_removed"] = True
        temp_dir.cleanup()
    elif temp_dir is not None:
        result["temporary_directory_removed"] = False
    return result


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print(json.dumps(run(args), sort_keys=True))


if __name__ == "__main__":
    main()
