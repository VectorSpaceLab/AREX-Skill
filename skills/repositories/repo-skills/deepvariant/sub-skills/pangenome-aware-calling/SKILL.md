---
name: pangenome-aware-calling
description: "Use pangenome-aware DeepVariant with GBZ inputs and
  run_pangenome_aware_deepvariant for WGS and WES workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Pangenome-aware DeepVariant

Use this sub-skill when the user wants DeepVariant calling that adds pangenome haplotype evidence through `run_pangenome_aware_deepvariant`, especially with a GBZ pangenome and short-read WGS or WES reads. The pangenome-aware wrapper is a Docker/Bazel-binary workflow; a verified Python package import does not imply a console script is available.

## Route Requests

- Use this sub-skill for pangenome-aware `WGS` or `WES` runs with `--pangenome`, GBZ shared memory, BWA- or VG-mapped reads, `--ref_name_pangenome`, `--sample_name_pangenome`, pangenome-aware intermediates, runtime reports, or Roche/SBX pangenome-aware arguments.
- Route standard non-pangenome single-sample calling to `../germline-calling/SKILL.md`.
- Route low-level stage tuning for `make_examples`, `call_variants`, `postprocess_variants`, TFRecord sharding, or generic extra args to `../pipeline-stages/SKILL.md`.
- Route visualization, hap.py interpretation, runtime plots, and benchmarking summaries to `../analysis-visualization/SKILL.md`.

## Start Here

- Generate a safe Docker command with `scripts/pangenome_command_builder.py`; it validates command shape and prints a command without running Docker or opening genomics files.
- Follow `references/workflows.md` for WGS/WES BWA/VG command patterns, GBZ shared-memory planning, pangenome intermediates, runtime reporting, and benchmark handoff.
- Use `references/pangenome-flags.md` for pangenome-specific flags, defaults, reference/sample naming, WES behavior, model/data compatibility, and Roche/SBX additions.
- Use `references/troubleshooting.md` for GBZ path and mount failures, shared-memory sizing, reference-name mismatches, sample-name confusion, WES multiprocessing expectations, pangenome extra args, and Docker tag mismatches.

## Required User Inputs

Collect these before producing a final command:

- `--model_type`: `WGS` or `WES` for the pangenome-aware r1.10 workflow.
- `--ref`: container-visible FASTA path with a matching `.fai`, compatible with the read alignment.
- `--reads`: aligned, sorted, indexed BAM or CRAM for the sample being called.
- `--pangenome`: container-visible GBZ pangenome path for the documented pangenome-aware workflow.
- `--output_vcf`: mounted output VCF path; optionally collect `--output_gvcf`, `--regions`, `--num_shards`, `--intermediate_results_dir`, and `--logging_dir`.
- Pangenome identity: confirm `--ref_name_pangenome` when the reference name inside the GBZ differs from the FASTA basename or expected assembly label, and confirm `--sample_name_pangenome` when the pangenome panel name is not `hprc_v1.1`.

## Safety Notes

Docker pulls/runs, GBZ loading, GPU or Singularity variants, native DeepVariant binaries, hap.py benchmarking, and full pangenome runs are conditional. Do not run them without explicit user data, Docker privileges, image availability, sufficient shared memory, safe mounts, and runtime budget. Prefer command generation, dry-run review, and user confirmation first.

## Evidence Basis

This sub-skill distills the pangenome-aware WGS BWA, WGS VG, WES BWA, pangenome metrics, Roche/SBX workflows, and the pangenome runner/shared-memory behavior from DeepVariant r1.10 evidence into self-contained runtime guidance.
