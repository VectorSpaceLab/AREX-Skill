#!/usr/bin/env python3
"""Generate safe Hail dense MatrixTable recipe templates.

This utility does not import Hail and does not read or write cohort data unless
its printed template is copied into a separate analysis script and executed by a
user. It is intended as a skill-owned starting point for future agents.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RecipeConfig:
    input_format: str
    input_path: str
    output_mt: str
    reference_genome: str
    phenotype_table: Optional[str]
    phenotype_key: str
    run_qc: bool
    split_multiallelics: bool
    run_pca: bool
    run_association: bool
    association: str
    export_vcf: Optional[str]
    vep_config: Optional[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a safe Hail dense MatrixTable analysis recipe template.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--print-template",
        action="store_true",
        help="Print the generated Python template to stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved recipe configuration without generating code.",
    )
    parser.add_argument(
        "--input-format",
        choices=("vcf", "plink", "bgen", "mt"),
        default="vcf",
        help="Input format the generated template should read.",
    )
    parser.add_argument(
        "--input-path",
        default="cohort.vcf.bgz",
        help="Input path or prefix placeholder. For PLINK, use a prefix without .bed/.bim/.fam.",
    )
    parser.add_argument(
        "--output-mt",
        default="analysis.mt",
        help="Native MatrixTable checkpoint/write path used by the template.",
    )
    parser.add_argument(
        "--reference-genome",
        default="GRCh38",
        help="Reference genome name used for imports and interval parsing.",
    )
    parser.add_argument(
        "--phenotype-table",
        help="Optional sample phenotype/covariate TSV path keyed by --phenotype-key.",
    )
    parser.add_argument(
        "--phenotype-key",
        default="s",
        help="Sample ID key field in the phenotype table.",
    )
    parser.add_argument(
        "--no-qc",
        dest="run_qc",
        action="store_false",
        help="Omit variant_qc/sample_qc steps from the generated template.",
    )
    parser.set_defaults(run_qc=True)
    parser.add_argument(
        "--split-multiallelics",
        action="store_true",
        help="Include split_multi_hts recipe block.",
    )
    parser.add_argument(
        "--run-pca",
        action="store_true",
        help="Include LD pruning and HWE-normalized PCA recipe block.",
    )
    parser.add_argument(
        "--run-association",
        action="store_true",
        help="Include linear or logistic regression recipe block.",
    )
    parser.add_argument(
        "--association",
        choices=("linear", "logistic"),
        default="linear",
        help="Association test family for the generated recipe block.",
    )
    parser.add_argument(
        "--export-vcf",
        help="Optional VCF path for an export_vcf recipe block.",
    )
    parser.add_argument(
        "--vep-config",
        help="Optional VEP config path for a VEP recipe block.",
    )
    return parser


def config_from_args(args: argparse.Namespace) -> RecipeConfig:
    return RecipeConfig(
        input_format=args.input_format,
        input_path=args.input_path,
        output_mt=args.output_mt,
        reference_genome=args.reference_genome,
        phenotype_table=args.phenotype_table,
        phenotype_key=args.phenotype_key,
        run_qc=args.run_qc,
        split_multiallelics=args.split_multiallelics,
        run_pca=args.run_pca,
        run_association=args.run_association,
        association=args.association,
        export_vcf=args.export_vcf,
        vep_config=args.vep_config,
    )


def quoted(value: Optional[str]) -> str:
    return repr(value)


def import_block(config: RecipeConfig) -> str:
    if config.input_format == "vcf":
        force_bgz = repr(config.input_path.endswith(".gz") and not config.input_path.endswith(".bgz"))
        return f"""
mt = hl.import_vcf(
    {quoted(config.input_path)},
    reference_genome={quoted(config.reference_genome)},
    array_elements_required=False,
    force_bgz={force_bgz},
    # contig_recoding={{"1": "chr1"}},  # enable only for naming-convention fixes
)
"""
    if config.input_format == "plink":
        prefix = config.input_path
        return f"""
mt = hl.import_plink(
    bed={quoted(prefix + '.bed')},
    bim={quoted(prefix + '.bim')},
    fam={quoted(prefix + '.fam')},
    reference_genome={quoted(config.reference_genome)},
    missing="-9",
    quant_pheno=True,
)
"""
    if config.input_format == "bgen":
        return f"""
# Run once outside repeated analyses if the .idx2 index does not already exist:
# hl.index_bgen({quoted(config.input_path)}, reference_genome={quoted(config.reference_genome)})
mt = hl.import_bgen(
    {quoted(config.input_path)},
    entry_fields=["dosage", "GP"],
    sample_file=None,  # set a .sample path when available
)
"""
    return f"""
mt = hl.read_matrix_table({quoted(config.input_path)})
"""


def phenotype_block(config: RecipeConfig) -> str:
    if not config.phenotype_table:
        return """
# Optional: annotate samples with phenotype/covariate data.
# pheno = hl.import_table("phenotypes.tsv", impute=True, key="s")
# mt = mt.annotate_cols(pheno=pheno[mt.s])
"""
    return f"""
pheno = hl.import_table({quoted(config.phenotype_table)}, impute=True, key={quoted(config.phenotype_key)})
mt = mt.annotate_cols(pheno=pheno[mt.s])
mt = mt.filter_cols(hl.is_defined(mt.pheno))
"""


def split_block(enabled: bool) -> str:
    if not enabled:
        return """
# Optional for multiallelic VCFs before biallelic-only analyses:
# mt = hl.split_multi_hts(mt)
"""
    return """
bi = mt.filter_rows(hl.len(mt.alleles) == 2).annotate_rows(a_index=1, was_split=False)
multi = mt.filter_rows(hl.len(mt.alleles) > 2)
split = hl.split_multi_hts(multi)
mt = split.union_rows(bi)
mt = mt.checkpoint("split.mt", overwrite=True)
"""


def qc_block(enabled: bool) -> str:
    if not enabled:
        return """
# QC omitted by template option. Ensure downstream filters are still appropriate.
"""
    return """
mt = hl.variant_qc(mt)
mt = hl.sample_qc(mt)
mt = mt.filter_cols(mt.sample_qc.call_rate >= 0.98)
mt = mt.filter_rows(mt.variant_qc.call_rate >= 0.98)
"""


def pca_block(enabled: bool) -> str:
    if not enabled:
        return """
# Optional PCA block:
# pruned = hl.ld_prune(mt.GT, r2=0.2, bp_window_size=500000)
# mt_pruned = mt.filter_rows(hl.is_defined(pruned[mt.row_key]))
# eigenvalues, scores, loadings = hl.hwe_normalized_pca(mt_pruned.GT, k=10, compute_loadings=True)
# mt = mt.annotate_cols(scores=scores[mt.s].scores)
"""
    return """
mt_common = mt.filter_rows((hl.len(mt.alleles) == 2) & (mt.variant_qc.AF[1] > 0.05))
pruned = hl.ld_prune(mt_common.GT, r2=0.2, bp_window_size=500000)
mt_pruned = mt_common.filter_rows(hl.is_defined(pruned[mt_common.row_key]))
eigenvalues, scores, loadings = hl.hwe_normalized_pca(mt_pruned.GT, k=10, compute_loadings=True)
mt = mt.annotate_cols(scores=scores[mt.s].scores)
"""


def association_block(config: RecipeConfig) -> str:
    if not config.run_association:
        return """
# Optional association block requires column phenotype/covariates and entry predictor.
# gwas = hl.linear_regression_rows(
#     y=mt.pheno.trait,
#     x=mt.GT.n_alt_alleles(),
#     covariates=[1, mt.pheno.age, mt.pheno.is_female],
#     pass_through=[mt.rsid],
# )
"""
    if config.association == "linear":
        return """
gwas = hl.linear_regression_rows(
    y=mt.pheno.trait,
    x=mt.GT.n_alt_alleles(),
    covariates=[1, mt.pheno.age, mt.pheno.is_female],
    pass_through=[mt.rsid],
)
gwas.export("linear_gwas.tsv.bgz")
"""
    return """
gwas = hl.logistic_regression_rows(
    test="wald",
    y=mt.pheno.is_case,
    x=mt.GT.n_alt_alleles(),
    covariates=[1, mt.pheno.age, mt.pheno.is_female],
    pass_through=[mt.rsid],
)
gwas.export("logistic_gwas.tsv.bgz")
"""


def vep_block(config: RecipeConfig) -> str:
    if not config.vep_config:
        return """
# Optional VEP block requires a configured VEP runtime matching the reference genome.
# mt = hl.vep(mt, config="vep-config.json", name="vep")
"""
    return f"""
mt = hl.vep(mt, config={quoted(config.vep_config)}, name="vep")
mt = mt.checkpoint("vep_annotated.mt", overwrite=True)
"""


def export_block(config: RecipeConfig) -> str:
    if not config.export_vcf:
        return """
# Optional VCF export:
# mt = hl.variant_qc(mt)
# mt = mt.annotate_rows(info=mt.info.annotate(AC=mt.variant_qc.AC[1:], AF=mt.variant_qc.AF[1:], AN=mt.variant_qc.AN))
# hl.export_vcf(mt, "cohort.filtered.vcf.bgz", tabix=True)
"""
    return f"""
mt = hl.variant_qc(mt)
if "info" in mt.row:
    mt = mt.annotate_rows(info=mt.info.annotate(
        AC=mt.variant_qc.AC[1:],
        AF=mt.variant_qc.AF[1:],
        AN=mt.variant_qc.AN,
    ))
hl.export_vcf(mt, {quoted(config.export_vcf)}, tabix=True)
"""


def indent(block: str) -> str:
    text = textwrap.dedent(block).strip("\n")
    if not text:
        return ""
    return textwrap.indent(text, "    ") + "\n"


def render_template(config: RecipeConfig) -> str:
    body = f'''#!/usr/bin/env python3
"""Editable Hail dense MatrixTable analysis recipe.

Review every placeholder before running on real data. This template assumes a
configured Hail runtime and a dense MatrixTable workflow, not sparse VDS/GVCF.
"""

import hail as hl


def main():
    hl.init()
{indent(import_block(config))}    mt.describe()
    mt = mt.checkpoint({quoted(config.output_mt)}, overwrite=True)
{indent(phenotype_block(config))}{indent(split_block(config.split_multiallelics))}{indent(qc_block(config.run_qc))}    mt = mt.checkpoint("post_qc.mt", overwrite=True)
{indent(pca_block(config.run_pca))}{indent(association_block(config))}{indent(vep_block(config))}{indent(export_block(config))}    mt.write("final_dense_analysis.mt", overwrite=True)


if __name__ == "__main__":
    main()
'''
    return body


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)

    if args.dry_run:
        print(json.dumps(asdict(config), indent=2, sort_keys=True))
        return 0

    if args.print_template:
        print(render_template(config))
        return 0

    parser.print_help()
    print("\nNo data was read or written. Use --print-template or --dry-run.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
