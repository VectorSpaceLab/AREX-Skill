---
name: germline-calling
description: "Plan, validate, and adapt standard DeepVariant germline
  run_deepvariant workflows for WGS, WES, long-read, hybrid, MAS-Seq, and
  RNA-seq data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepVariant Germline Calling

Use this sub-skill when the user needs a safe plan, command, or preflight review for single-sample DeepVariant germline calling through `run_deepvariant`. It covers `WGS`, `WES`, `PACBIO`, `ONT_R104`, `HYBRID_PACBIO_ILLUMINA`, `MASSEQ`, and `RNASEQ` model types in DeepVariant `1.10.0`.

Do not use this sub-skill for trio or duo family calling, pangenome GBZ workflows, stage-by-stage tuning, custom model training, or report interpretation. Route those requests to `../trio-calling/SKILL.md`, `../pangenome-aware-calling/SKILL.md`, `../pipeline-stages/SKILL.md`, `../training-custom-models/SKILL.md`, or `../analysis-visualization/SKILL.md`.

## Trigger Phrases

- "Run DeepVariant on a BAM/CRAM", "make a germline VCF", "DeepVariant WGS/WES command", "PacBio/ONT DeepVariant", "hybrid PacBio Illumina calling", "MAS-Seq/RNA-seq DeepVariant".
- "Add gVCF", "restrict to chr20 or a BED", "use Docker/Singularity", "GPU DeepVariant", "dry run the wrapper", "haploid chrX/chrY", "disable small model", "customized model for inference".

## Workflow Outline

1. Confirm assay, sample context, reference build, read technology, and whether a standard released model or a customized model is intended.
2. Select exactly one `--model_type` and validate compatibility with `--ref`, `--reads`, `--regions`, custom-model metadata, haploid/PAR settings, and desired outputs.
3. Choose Docker or Singularity command shape and ensure every host input, output, index, region BED, PAR BED, log directory, intermediate directory, and model path is mounted under the same container paths used in flags.
4. Prefer `--dry_run=true` for planning or stage inspection; do not run full variant calling, image pulls, downloads, GPU setup, or host runtime changes without user confirmation.
5. Use `scripts/deepvariant_command_builder.py` for local static validation and command preview when the user has host paths.
6. For lower-level flags discovered through dry run or extra args, keep the top-level command here and route detailed stage customization to `../pipeline-stages/SKILL.md`.

## Read/Run Links

- `references/workflows.md` gives Docker/Singularity command recipes, per-assay templates, CRAM/bgzip reference planning, dry-run behavior, outputs, and validation order.
- `references/model-types-and-flags.md` explains model types, required flags, gVCF, VCF stats, runtime logging, haploid/PAR flags, small model controls, custom model metadata, and extra-args formatting.
- `references/troubleshooting.md` maps common failures to recovery steps for missing indexes, contig mismatches, wrong mounts, GPU confusion, wrong model type, haploid/PAR misuse, gVCF surprises, custom models, and `make_examples_extra_args` formatting.
- `scripts/deepvariant_command_builder.py` prints a Docker or Singularity `run_deepvariant` command without executing DeepVariant.

## Safe Helper

Run the helper locally to validate obvious path/index issues and print a command preview:

```bash
python scripts/deepvariant_command_builder.py --help
```

The helper never runs Docker, Singularity, `run_deepvariant`, or genomics tools. It validates required inputs, model type, common index companions, output parents, custom model metadata, region literals against a readable `.fai`, and risky flag combinations; header-level BAM/CRAM and reference compatibility still require user-side checks.

## Decision Rules

- Use `--output_gvcf` only when downstream cohort merging, joint genotyping, or reference-block output is needed; expect larger outputs and heavier postprocessing.
- Use `--vcf_stats_report=true` for an HTML VCF summary, and use `--logging_dir` plus `--runtime_report=true` for make-examples runtime diagnostics.
- Use `--haploid_contigs` only for samples/regions that should be re-genotyped as haploid; pair it with a reference-matched `--par_regions_bed` when PAR regions must remain diploid.
- Use `--disable_small_model=true` when the assay recipe calls for it, when custom model metadata is uncertain, or when every candidate should pass through the CNN.
- Use `--customized_model` only with compatible `model.example_info.json` metadata or `--customized_model_json`; otherwise model-specific example-generation flags can be wrong.

## Safety Notes

Official production execution depends on Docker/Bazel binaries or released containers, TensorFlow/compiled modules, and user genomics data. The lightweight Python import environment is useful for inspection only and is not sufficient for production variant calling.
