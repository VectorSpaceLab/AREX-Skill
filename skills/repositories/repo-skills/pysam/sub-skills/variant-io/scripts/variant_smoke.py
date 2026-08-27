#!/usr/bin/env python3
"""Create, read, and summarize a tiny source-free pysam VCF round trip."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional


def _avoid_checkout_shadowing() -> None:
    script_path = Path(__file__).resolve()
    filtered = []
    for entry in sys.path:
        candidate = Path(entry or os.getcwd()).resolve()
        if candidate == script_path.parent:
            continue
        shadow = candidate / "pysam" / "__init__.py"
        pyproject = candidate / "pyproject.toml"
        if shadow.exists() and pyproject.exists():
            try:
                if 'name = "pysam"' in pyproject.read_text(encoding="utf-8", errors="ignore"):
                    continue
            except OSError:
                pass
        filtered.append(entry)
    sys.path[:] = filtered


def build_header(pysam_module):
    header = pysam_module.VariantHeader()
    header.add_meta("fileformat", value="VCFv4.2")
    header.contigs.add("chr1", length=1000)
    header.info.add("DP", 1, "Integer", "Total read depth")
    header.info.add("AF", ".", "Float", "Alternate allele frequency")
    header.formats.add("GT", 1, "String", "Genotype")
    header.formats.add("DP", 1, "Integer", "Sample read depth")
    header.add_sample("SAMPLE1")
    return header


def create_record(header):
    record = header.new_record(
        contig="chr1",
        start=9,
        stop=10,
        alleles=("A", "G"),
        id="var1",
        qual=50,
        filter="PASS",
        info={"DP": 12, "AF": (0.25,)},
        samples=[{"GT": (0, 1), "DP": 8}],
    )
    return record


def round_trip(output_path: Optional[Path] = None):
    _avoid_checkout_shadowing()
    import pysam

    header = build_header(pysam)
    record = create_record(header)

    with tempfile.TemporaryDirectory() as temp_dir:
        vcf_path = output_path or Path(temp_dir) / "tiny.vcf"
        with pysam.VariantFile(str(vcf_path), "w", header=header) as out_vcf:
            out_vcf.write(record)

        with pysam.VariantFile(str(vcf_path)) as in_vcf:
            observed = next(in_vcf.fetch())
            sample = observed.samples["SAMPLE1"]
            summary = {
                "ok": True,
                "pysam_version": getattr(pysam, "__version__", None),
                "path": str(vcf_path),
                "contigs": list(in_vcf.header.contigs),
                "samples": list(in_vcf.header.samples),
                "record": {
                    "contig": observed.contig,
                    "pos": observed.pos,
                    "start": observed.start,
                    "stop": observed.stop,
                    "id": observed.id,
                    "ref": observed.ref,
                    "alts": list(observed.alts or []),
                    "filters": list(observed.filter.keys()),
                    "info_dp": observed.info["DP"],
                    "info_af": list(observed.info["AF"]),
                    "sample_gt": list(sample["GT"]),
                    "sample_dp": sample["DP"],
                    "sample_alleles": list(sample.alleles),
                },
            }

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-vcf", type=Path, help="Optional destination for the tiny VCF")
    args = parser.parse_args()

    summary = round_trip(args.output_vcf)
    expected = {
        "contig": "chr1",
        "pos": 10,
        "start": 9,
        "stop": 10,
        "ref": "A",
        "alts": ["G"],
        "info_dp": 12,
        "sample_gt": [0, 1],
        "sample_dp": 8,
        "sample_alleles": ["A", "G"],
    }
    for key, value in expected.items():
        if summary["record"][key] != value:
            raise AssertionError(f"{key}: expected {value!r}, observed {summary['record'][key]!r}")

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
