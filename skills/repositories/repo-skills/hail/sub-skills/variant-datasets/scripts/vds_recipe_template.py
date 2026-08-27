#!/usr/bin/env python3
"""Safe starter template for Hail VariantDataset workflows.

Default mode is dry-run and does not import Hail. Use --print-template to print
an editable Hail script. Use --execute only after reviewing paths, backend
configuration, and workflow cost for the target environment.
"""

from __future__ import annotations

import argparse
import sys
from textwrap import dedent


WORKFLOWS = ["sample-qc", "interval-coverage", "variant-data", "dense", "merged-sparse", "combiner"]

TEMPLATE = r'''
import hail as hl


def main(args):
    hl.init()

    if args.workflow == "combiner":
        if not args.gvcf:
            raise ValueError("--gvcf is required for combiner")
        if not args.output or not args.temp_path:
            raise ValueError("--output and --temp-path are required for combiner")
        combiner_kwargs = {
            "output_path": args.output,
            "temp_path": args.temp_path,
            "gvcf_paths": args.gvcf,
            "reference_genome": args.reference_genome,
        }
        if args.save_path:
            combiner_kwargs["save_path"] = args.save_path
        if args.use_genome_default_intervals:
            combiner_kwargs["use_genome_default_intervals"] = True
        elif args.use_exome_default_intervals:
            combiner_kwargs["use_exome_default_intervals"] = True
        elif args.interval:
            combiner_kwargs["intervals"] = [
                hl.parse_locus_interval(interval, reference_genome=args.reference_genome)
                for interval in args.interval
            ]
        else:
            raise ValueError("choose one combiner partitioning mode before execution")
        hl.vds.new_combiner(**combiner_kwargs).run()
        return

    if not args.vds or not args.output:
        raise ValueError("--vds and --output are required for read/filter/convert workflows")

    vds = hl.vds.read_vds(args.vds)
    if args.validate:
        vds.validate(check_data=True)

    if args.samples_tsv:
        samples = hl.import_table(args.samples_tsv, key=args.sample_key)
        vds = hl.vds.filter_samples(
            vds,
            samples,
            keep=not args.remove_samples,
            remove_dead_alleles=args.remove_dead_alleles,
        )

    if args.interval:
        intervals = [hl.parse_locus_interval(x, reference_genome=args.reference_genome) for x in args.interval]
        vds = hl.vds.filter_intervals(
            vds,
            hl.literal(intervals),
            keep=True,
            split_reference_blocks=args.split_reference_blocks,
        )

    if args.workflow == "sample-qc":
        result = hl.vds.sample_qc(vds)
        result.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "interval-coverage":
        if not args.intervals_table:
            raise ValueError("--intervals-table is required for interval-coverage")
        intervals_ht = hl.read_table(args.intervals_table)
        result = hl.vds.interval_coverage(vds, intervals_ht)
        result.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "variant-data":
        mt = vds.variant_data
        if "LGT" in mt.entry and "LA" in mt.entry:
            mt = mt.annotate_entries(GT=hl.vds.lgt_to_gt(mt.LGT, mt.LA))
        mt.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "dense":
        mt = hl.vds.to_dense_mt(vds)
        if "LGT" in mt.entry and "LA" in mt.entry:
            mt = mt.annotate_entries(GT=hl.vds.lgt_to_gt(mt.LGT, mt.LA))
        mt.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "merged-sparse":
        mt = hl.vds.to_merged_sparse_mt(vds, ref_allele_function=lambda row: hl.missing("str"))
        mt.write(args.output, overwrite=args.overwrite)
    else:
        raise ValueError(f"unknown workflow: {args.workflow}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--workflow", choices=["sample-qc", "interval-coverage", "variant-data", "dense", "merged-sparse", "combiner"], default="sample-qc")
    parser.add_argument("--vds")
    parser.add_argument("--output", required=True)
    parser.add_argument("--reference-genome", default="GRCh38")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--samples-tsv")
    parser.add_argument("--sample-key", default="s")
    parser.add_argument("--remove-samples", action="store_true")
    parser.add_argument("--remove-dead-alleles", action="store_true")
    parser.add_argument("--interval", action="append")
    parser.add_argument("--intervals-table")
    parser.add_argument("--split-reference-blocks", action="store_true")
    parser.add_argument("--gvcf", action="append")
    parser.add_argument("--temp-path")
    parser.add_argument("--save-path")
    parser.add_argument("--use-genome-default-intervals", action="store_true")
    parser.add_argument("--use-exome-default-intervals", action="store_true")
    main(parser.parse_args())
'''.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print or dry-run a Hail VariantDataset workflow template.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workflow", choices=WORKFLOWS, default="sample-qc", help="Workflow shape to describe or execute.")
    parser.add_argument("--vds", help="Input VDS path for read/filter/convert workflows.")
    parser.add_argument("--output", help="Output path for the selected workflow.")
    parser.add_argument("--reference-genome", default="GRCh38", help="Reference genome name for interval parsing.")
    parser.add_argument("--interval", action="append", help="Locus interval to keep; may be repeated.")
    parser.add_argument("--samples-tsv", help="Sample table to keep/remove; key defaults to --sample-key.")
    parser.add_argument("--sample-key", default="s", help="Sample key field in --samples-tsv.")
    parser.add_argument("--remove-samples", action="store_true", help="Remove samples instead of keeping them.")
    parser.add_argument("--remove-dead-alleles", action="store_true", help="Compact alleles and LA after sample filtering.")
    parser.add_argument("--split-reference-blocks", action="store_true", help="Trim reference blocks to kept intervals.")
    parser.add_argument("--intervals-table", help="Interval table path for interval-coverage workflow.")
    parser.add_argument("--gvcf", action="append", help="GVCF path for combiner dry-run or execution; may be repeated.")
    parser.add_argument("--temp-path", help="Combiner temporary path.")
    parser.add_argument("--save-path", help="Combiner plan JSON path.")
    parser.add_argument("--use-genome-default-intervals", action="store_true", help="Combiner genome default partitioning.")
    parser.add_argument("--use-exome-default-intervals", action="store_true", help="Combiner exome default partitioning.")
    parser.add_argument("--print-template", action="store_true", help="Print an editable Hail script and exit.")
    parser.add_argument("--execute", action="store_true", help="Execute a minimal adapted workflow. Imports Hail and may run backend jobs.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite outputs in --execute mode.")
    parser.add_argument("--validate", action="store_true", help="Run vds.validate(check_data=True) in --execute mode.")
    return parser


def selected_partition_modes(args: argparse.Namespace) -> list[str]:
    modes = []
    if args.use_genome_default_intervals:
        modes.append("use_genome_default_intervals")
    if args.use_exome_default_intervals:
        modes.append("use_exome_default_intervals")
    if args.interval:
        modes.append("custom_intervals")
    return modes


def print_dry_run(args: argparse.Namespace) -> None:
    print("VDS recipe dry-run")
    print(f"  workflow: {args.workflow}")
    if args.workflow == "combiner":
        print(f"  gvcfs: {len(args.gvcf or [])} path(s)")
        print(f"  output: {args.output or '<required>'}")
        print(f"  temp_path: {args.temp_path or '<required>'}")
        print(f"  save_path: {args.save_path or '<auto or provided>'}")
        print(f"  reference_genome: {args.reference_genome}")
        print(f"  partition_modes: {selected_partition_modes(args) or ['<required for GVCFs>']}")
        print("  next: validate schema/reference choices before running hl.vds.new_combiner(...).run()")
        return

    print(f"  input VDS: {args.vds or '<required>'}")
    print(f"  output: {args.output or '<required>'}")
    print(f"  reference_genome: {args.reference_genome}")
    if args.samples_tsv:
        action = "remove" if args.remove_samples else "keep"
        print(f"  sample filter: {action} samples from {args.samples_tsv!r} keyed by {args.sample_key!r}")
        print(f"  remove_dead_alleles: {args.remove_dead_alleles}")
    if args.interval:
        print(f"  intervals: {', '.join(args.interval)}")
        print(f"  split_reference_blocks: {args.split_reference_blocks}")
    if args.workflow == "interval-coverage":
        print(f"  intervals_table: {args.intervals_table or '<required>'}")
    if args.workflow == "dense":
        print("  warning: dense conversion can be expensive; filter samples, variants, and intervals first")
    if args.workflow == "merged-sparse":
        print("  note: provide a reference allele strategy if missing reference alleles are not acceptable")
    print("  next: run with --print-template to copy an editable script, or --execute after review")


def validate_execute_args(args: argparse.Namespace) -> None:
    if args.workflow == "combiner":
        if not args.gvcf:
            raise ValueError("--gvcf is required for combiner execution")
        if not args.output or not args.temp_path:
            raise ValueError("--output and --temp-path are required for combiner execution")
        modes = selected_partition_modes(args)
        if len(modes) != 1:
            raise ValueError("choose exactly one combiner partitioning mode before execution")
        return
    if not args.vds or not args.output:
        raise ValueError("--vds and --output are required for execution")
    if args.workflow == "interval-coverage" and not args.intervals_table:
        raise ValueError("--intervals-table is required for interval-coverage execution")


def execute(args: argparse.Namespace) -> None:
    validate_execute_args(args)
    import hail as hl

    hl.init()

    if args.workflow == "combiner":
        combiner_kwargs = {
            "output_path": args.output,
            "temp_path": args.temp_path,
            "gvcf_paths": args.gvcf,
            "reference_genome": args.reference_genome,
        }
        if args.save_path:
            combiner_kwargs["save_path"] = args.save_path
        if args.use_genome_default_intervals:
            combiner_kwargs["use_genome_default_intervals"] = True
        elif args.use_exome_default_intervals:
            combiner_kwargs["use_exome_default_intervals"] = True
        else:
            combiner_kwargs["intervals"] = [
                hl.parse_locus_interval(interval, reference_genome=args.reference_genome) for interval in args.interval
            ]
        hl.vds.new_combiner(**combiner_kwargs).run()
        return

    vds = hl.vds.read_vds(args.vds)
    if args.validate:
        vds.validate(check_data=True)
    if args.samples_tsv:
        samples = hl.import_table(args.samples_tsv, key=args.sample_key)
        vds = hl.vds.filter_samples(
            vds,
            samples,
            keep=not args.remove_samples,
            remove_dead_alleles=args.remove_dead_alleles,
        )
    if args.interval:
        intervals = [hl.parse_locus_interval(interval, reference_genome=args.reference_genome) for interval in args.interval]
        vds = hl.vds.filter_intervals(vds, hl.literal(intervals), split_reference_blocks=args.split_reference_blocks)

    if args.workflow == "sample-qc":
        result = hl.vds.sample_qc(vds)
        result.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "interval-coverage":
        intervals_ht = hl.read_table(args.intervals_table)
        result = hl.vds.interval_coverage(vds, intervals_ht)
        result.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "variant-data":
        mt = vds.variant_data
        if "LGT" in mt.entry and "LA" in mt.entry:
            mt = mt.annotate_entries(GT=hl.vds.lgt_to_gt(mt.LGT, mt.LA))
        mt.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "dense":
        mt = hl.vds.to_dense_mt(vds)
        if "LGT" in mt.entry and "LA" in mt.entry:
            mt = mt.annotate_entries(GT=hl.vds.lgt_to_gt(mt.LGT, mt.LA))
        mt.write(args.output, overwrite=args.overwrite)
    elif args.workflow == "merged-sparse":
        mt = hl.vds.to_merged_sparse_mt(vds, ref_allele_function=lambda row: hl.missing("str"))
        mt.write(args.output, overwrite=args.overwrite)
    else:
        raise ValueError(f"unsupported workflow for execution: {args.workflow}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.print_template:
        print(dedent(TEMPLATE))
        return 0
    if args.execute:
        execute(args)
        return 0
    print_dry_run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
