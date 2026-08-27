---
name: analysis-visualization
description: "Plan and interpret DeepVariant VCF stats, runtime-by-region,
  show_examples, and benchmark-analysis reports safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepVariant Analysis Visualization

Use this sub-skill when a user already has DeepVariant outputs or intermediates and needs command previews, report interpretation, pileup-image review, runtime bottleneck analysis, hap.py summary interpretation, or checkpoint-metric summaries.

Do not use this sub-skill to run variant calling, trio calling, pangenome-aware calling, stage orchestration, or model training. Route those workflows to the appropriate calling, pipeline-stage, or training sub-skills. Use this sub-skill after a run has produced a VCF, runtime TSVs/logs, examples TFRecords, hap.py outputs, or training/eval `.metrics` files.

## Start Here

1. Identify the artifact type: final VCF, `make_examples` runtime TSV, examples TFRecord, hap.py summary/output VCF, runtime log, or training `.metrics` files.
2. Confirm whether the user wants a non-executing command preview, interpretation of an existing report, or a benchmark/review handoff.
3. Use `scripts/report_command_builder.py` for safe previews of `vcf_stats_report`, `runtime_by_region_vis`, and `show_examples`; it validates common path and flag mistakes but never executes DeepVariant, Docker, Singularity, hap.py, or native report tools.
4. Keep report generation bounded: use explicit output locations, small `--num_records` values for pileup review, and `--max_examples_to_scan` for broad TFRecord scans.
5. If missing inputs require a new DeepVariant run, hand off run planning to the calling or pipeline-stage sub-skills instead of trying to create those inputs here.

## Bundled References

- `references/reports-and-visualization.md` covers VCF stats reports, runtime-by-region reports, `show_examples`, notebook-to-script translation, command shapes, outputs, and validation checks.
- `references/benchmarking.md` covers release metrics context, hap.py summaries, PASS-only interpretation, pangenome-aware metrics, false-positive/false-negative review, and `print_f1`-style checkpoint summaries.
- `references/troubleshooting.md` maps common report, visualization, benchmark, and notebook-translation symptoms to checks and recoveries.

## Decision Rules

- Use `--vcf_stats_report=true` during a new wrapper run when the user wants a VCF HTML summary produced automatically; use `vcf_stats_report` afterward when the user already has a compatible single-sample VCF.
- Use `--runtime_report=true` together with `--logging_dir` during a wrapper run to create runtime TSVs and an HTML report; use `runtime_by_region_vis` afterward when the user already has runtime TSVs.
- Use `--intermediate_results_dir` during calling when the user later wants `show_examples`; otherwise examples TFRecords may be temporary or hidden inside the runtime environment.
- Use `show_examples --vcf` with hap.py false-positive or false-negative VCF slices, plus strict `--num_records`, `--regions`, or `--max_examples_to_scan` guardrails for visual inspection.
- Interpret hap.py and release metrics only after recording version, model type, sample, truth set, confident regions, reference build, assay/coverage, hardware, shard count, and optional reporting flags.

## Safe Helper

Run the helper from this sub-skill directory to preview commands only:

```bash
python scripts/report_command_builder.py --help
```

Useful modes:

- `vcf-stats`: previews `/opt/deepvariant/bin/vcf_stats_report --input_vcf ... --outfile_base ...`.
- `runtime`: previews `/opt/deepvariant/bin/runtime_by_region_vis --input ... --output ...`.
- `show-examples`: previews `/opt/deepvariant/bin/show_examples --examples ... --output ...`.

## Safety Notes

This sub-skill provides post-run analysis guidance and command previews. It must not silently pull containers, run Docker/Singularity/Bazel binaries, execute hap.py, download benchmark datasets, generate thousands of pileup images, mutate runtime configuration, or assume a lightweight Python environment is sufficient for native DeepVariant visualization modules that require TensorFlow and compiled genomics dependencies.
