---
name: deepvariant
description: "Use DeepVariant and DeepTrio for genomics variant-calling command
  planning, input validation, pipeline-stage troubleshooting, custom training,
  and report analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepVariant Repo Skill

Use this repo skill when a user asks for help with DeepVariant, DeepTrio, pangenome-aware DeepVariant, DeepVariant pipeline stages, custom DeepVariant training, or DeepVariant output analysis. It distills DeepVariant `1.10.0` repository evidence into self-contained routing, references, and safe command-planning helpers.

This skill is primarily for planning, validating, adapting, and troubleshooting workflows. Do not assume a lightweight Python package import is enough to run production variant calling: official execution normally uses released Docker/Singularity images or Bazel-built binaries with TensorFlow, compiled genomics modules, and user-provided genomics data.

## Route Requests

| User intent | Read next | Why |
| --- | --- | --- |
| Single-sample germline calling with `run_deepvariant`, WGS/WES/PacBio/ONT/hybrid/MAS-Seq/RNA-seq, gVCF, haploid/PAR, Docker/Singularity, custom model inference | `sub-skills/germline-calling/SKILL.md` | Owns standard DeepVariant command construction and preflight checks. |
| Trio or duo family calling with child/parent reads, DeepTrio outputs, gVCFs, or GLnexus merge handoff | `sub-skills/trio-calling/SKILL.md` | Owns DeepTrio family-specific flags, outputs, and failure modes. |
| Pangenome-aware DeepVariant with GBZ inputs, pangenome reference/sample names, shared memory, or pangenome WGS/WES | `sub-skills/pangenome-aware-calling/SKILL.md` | Owns `run_pangenome_aware_deepvariant` and GBZ-specific planning. |
| Separate `make_examples`, `call_variants`, `postprocess_variants`, sharded TFRecords, gVCF internals, `*_extra_args`, or stage failures | `sub-skills/pipeline-stages/SKILL.md` | Owns lower-level stage contracts and sharded path semantics. |
| Custom training, labeled examples, `dv_config`, fine-tuning, checkpoint export, `model.example_info.json`, or `--customized_model` readiness | `sub-skills/training-custom-models/SKILL.md` | Owns training data, config, checkpoint, and custom-model handoff. |
| VCF stats HTML, runtime-by-region report, `show_examples`, hap.py summaries, benchmark interpretation, or visual inspection | `sub-skills/analysis-visualization/SKILL.md` | Owns post-run report and visualization workflows. |

## Shared References

- `references/install-and-runtime.md` explains Docker/Singularity, source-build, GPU/CPU, mount, image, and lightweight Python inspection constraints.
- `references/model-and-data-compatibility.md` explains model-type selection, reference/read/index contracts, contig/region compatibility, gVCF, sample naming, and custom-model metadata.
- `references/troubleshooting.md` covers cross-cutting install, container, data, model, optional dependency, and workflow-routing failures.
- `references/repo-provenance.md` records the DeepVariant source snapshot used to generate this skill and when to refresh it.
- `references/repo-routing-metadata.json` is structured metadata used by `repo-skills-router` during managed import.

## Shared Helpers

Run these only as lightweight local validators or note generators. They never execute Docker, Singularity, Bazel, DeepVariant binaries, TensorFlow, hap.py, GLnexus, network downloads, or large genomics IO.

```bash
python scripts/deepvariant_input_check.py --help
python scripts/docker_command_notes.py --help
```

- `scripts/deepvariant_input_check.py` checks common FASTA/read/index/region/model/output path mistakes for DeepVariant-style workflows.
- `scripts/docker_command_notes.py` prints workflow-specific container image, mount, GPU, and command-review reminders.

## Start Here

1. Identify the workflow family before giving commands: single-sample, family/trio, pangenome-aware, stage-level, training/custom model, or analysis/reporting.
2. Collect the minimum data contract: reference FASTA and `.fai`, sorted indexed BAM/CRAM, sample names where required, model type, regions or BED if restricted, output VCF/gVCF paths, runtime engine, and whether Docker/Singularity/GPU is approved.
3. Use the nearest sub-skill helper to preview commands or the root input checker to catch missing companions before recommending execution.
4. Treat full runs, image pulls, GPU setup, native tests, benchmark downloads, Beam/Dataflow jobs, GLnexus merge runs, and source builds as conditional actions that need explicit user approval and real data access.
5. Keep final user commands self-contained: all mounted host paths must match the container-visible paths used in flags, and every output parent directory must be mounted and writable.

## Important Boundaries

- Do not use this skill for read alignment, reference genome construction, raw sequencing QC, or general genomics preprocessing except where those inputs must be validated for DeepVariant.
- Do not treat DeepSomatic as covered beyond a related repository note; use a DeepSomatic-specific skill or docs when the user asks for somatic calling.
- Do not silently install TensorFlow, CUDA toolkits, Docker, Singularity, GLnexus, hap.py, Apache Beam, or cloud dependencies.
- Do not present skipped native tests or dry-run command previews as proof that a production variant-calling run passed.
- Do not rely on the original repository checkout for future use; all actionable runtime guidance and helpers are bundled in this generated skill.
