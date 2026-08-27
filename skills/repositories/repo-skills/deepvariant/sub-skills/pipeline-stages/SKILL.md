---
name: pipeline-stages
description: "Understand and adapt DeepVariant make_examples, call_variants,
  postprocess_variants, sharded TFRecords, and gVCF stage contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepVariant Pipeline Stages

Use this sub-skill when a user needs to inspect, adapt, or troubleshoot DeepVariant below the high-level wrappers: `make_examples`, `call_variants`, `postprocess_variants`, sharded TFRecords, gVCF non-variant records, candidate positions, channel lists, or wrapper `*_extra_args` routing.

Route complete single-sample command recipes to `../germline-calling/SKILL.md`, family workflows to `../trio-calling/SKILL.md`, pangenome GBZ workflows to `../pangenome-aware-calling/SKILL.md`, training dataset/model work to `../training-custom-models/SKILL.md`, and report generation to `../analysis-visualization/SKILL.md`.

## Start Here

1. Identify whether the user is starting from a wrapper `--dry_run`, a failed low-level command, or a custom stage-by-stage plan.
2. Map each intermediate path through `references/stage-contracts.md`: `make_examples` writes examples and optional non-variant TFRecords; `call_variants` writes CallVariantsOutput TFRecords; `postprocess_variants` writes final VCF and optional gVCF.
3. Validate sharded specs before discussing execution with `scripts/sharded_path_helper.py`; do not run Docker, Bazel binaries, TensorFlow inference, or genomics IO unless the user confirms the environment and data.
4. Check data and metadata assumptions in `references/data-formats.md`, including `.example_info.json`, channel lists, Nucleus sharding conventions, sorted/indexed inputs, and gVCF dataflow.
5. Use `references/troubleshooting.md` for invalid `@N` paths, missing `--task`, mode confusion, gVCF pairing errors, contig mismatches, resource pressure, or compiled-extension imports.

## Bundled References

- `references/stage-contracts.md` explains stage boundaries, required flags, wrapper dry-run mapping, `--mode`, `--task`, `--examples`, `--checkpoint`, dynamic CallVariantsOutput sharding, `--postprocess_cpus`, candidate-sweep mode, and extra args.
- `references/data-formats.md` explains sharded files, TFRecord payloads, `.example_info.json`, channel lists, candidate positions, gVCF non-variant records, VCF/gVCF outputs, and Nucleus IO assumptions.
- `references/troubleshooting.md` maps common stage-level symptoms to checks and recovery steps.
- `../../references/install-and-runtime.md` covers official Docker/Bazel runtime constraints and why lightweight package imports are not production execution.
- `../../references/model-and-data-compatibility.md` covers model, reference, reads, index, assay, and contig compatibility.
- `../../references/troubleshooting.md` covers cross-cutting installation, container, and data failures.

## Safe Helper

Run the bundled helper to explain or expand sharded path specs without reading genomics data:

```bash
python scripts/sharded_path_helper.py --spec examples.tfrecord@32.gz --task 7 --paired-gvcf gvcf.tfrecord@32.gz
```

The helper prints the logical shard count, concrete shard filenames, glob pattern, task-specific filenames, and warnings for common DeepVariant mistakes such as `@0`, suspicious suffixless specs like `examples.gz@32`, mismatched `--examples`/`--gvcf` shard counts, or using `examples@32.gz` without per-task execution.

## Decision Rules

- Treat `filename@N.ext` as a logical collection, not a literal file to open; task `i` writes or reads `filename-0000i-of-000NN.ext`.
- Pair sharded `make_examples --examples` with one `--task` per integer `0..N-1`; high-level wrappers usually generate this task loop for you.
- Keep gVCF stage arguments paired: `make_examples --gvcf` is valid only in calling mode, and `postprocess_variants` needs both `--nonvariant_site_tfrecord_path` and `--gvcf_outfile`.
- Use wrapper `--make_examples_extra_args`, `--call_variants_extra_args`, and `--postprocess_variants_extra_args` only for flags owned by that stage; verify extra args do not override wrapper-set paths unintentionally.
- Expect full stage execution to require official DeepVariant binaries, TensorFlow, compiled Nucleus/DeepVariant modules, and user genomics data; this sub-skill provides planning and lightweight validation by default.

## Evidence Basis

This sub-skill distills DeepVariant r1.10 stage docs, gVCF support notes, fast-pipeline guidance, `make_examples`, `call_variants`, `postprocess_variants`, shared sharded file utilities, constants, and related unit tests. Source evidence is provenance only; runtime instructions here are self-contained.
