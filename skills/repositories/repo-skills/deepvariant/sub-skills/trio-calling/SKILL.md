---
name: trio-calling
description: "Plans DeepTrio trio and duo variant-calling workflows with child
  and parent inputs, per-sample VCF/gVCF outputs, and GLnexus merge handoff."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepTrio Trio Calling

Use this sub-skill when a user needs DeepTrio family calling for a child with one or two parents. It covers Docker/Bazel-style `run_deeptrio` command planning, duo behavior when one parent is absent, model-type choice, per-sample output planning, gVCF merge handoff, and family-specific troubleshooting.

## Route The Request

- Use this sub-skill for DeepTrio `run_deeptrio` workflows, trio/duo sample planning, child/parent output naming, gVCF planning, GLnexus handoff, and sex-chromosome parent-selection caveats.
- Route single-sample `run_deepvariant` germline calling to the `germline-calling` sub-skill.
- Route pangenome-aware DeepVariant workflows to the `pangenome-aware-calling` sub-skill.
- Route low-level `make_examples`, `call_variants`, `postprocess_variants`, sharded TFRecords, and extra-args internals to the `pipeline-stages` sub-skill.
- Route benchmarking reports, Mendelian-violation analysis, `hap.py`, RTG, and visualization to the `analysis-visualization` sub-skill.

## Fast Path

1. Identify family mode: trio has `child`, `parent1`, and `parent2`; duo has `child` and exactly one parent.
2. Choose `--model_type` from `WGS`, `WES`, `PACBIO`, or `ONT` according to the sequencing data and image/model availability.
3. Require an indexed FASTA and sorted, indexed, compatible BAMs for every supplied sample.
4. Require one VCF output for every supplied sample, and request a matching gVCF for every supplied sample when GLnexus or cohort merging is planned.
5. Use [`scripts/deeptrio_command_builder.py`](scripts/deeptrio_command_builder.py) to validate the plan and print a reviewable command without executing Docker, DeepTrio, or GLnexus.
6. Read [`references/workflows.md`](references/workflows.md), [`references/deeptrio-flags.md`](references/deeptrio-flags.md), and [`references/troubleshooting.md`](references/troubleshooting.md) for command patterns, flag contracts, and recovery steps.

## Bundled Helper

The helper is a command planner only:

```bash
python scripts/deeptrio_command_builder.py --help
```

It validates child/parent flag groups, makes duo mode explicit by omitting every parent2 flag, warns about WES regions and long-read candidate partitioning, and can emit a GLnexus handoff command when a complete gVCF set is present.

## Safety

Do not run Docker, GLnexus, network downloads, GPU jobs, or native DeepTrio tests without explicit user approval and real user-provided genomics inputs. Treat generated commands as plans until the user confirms the runtime environment, container mounts, and data paths.
