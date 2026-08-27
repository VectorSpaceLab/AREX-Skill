# DeepTrio Troubleshooting

Use this reference for family-calling failures. For broad Docker, image, dependency, GPU, mount, and general DeepVariant runtime failures, use the generated root troubleshooting guidance together with this sub-skill.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Command planning reports a missing child flag | `--model-type`, `--ref`, `--reads-child`, `--sample-name-child`, or `--output-vcf-child` is absent | Add the missing child flag and regenerate the command; every path passed to DeepTrio must be visible inside the container. |
| Parent1 flags fail validation | Only one or two of `--reads-parent1`, `--sample-name-parent1`, and `--output-vcf-parent1` were set | Provide all three; DeepTrio duo mode still needs a complete parent1 group. |
| Parent2 appears in a duo command | A stale `--reads-parent2`, `--sample-name-parent2`, `--output-vcf-parent2`, or `--output-gvcf-parent2` remained in the plan | Remove every parent2 flag for duo mode. Do not keep parent2 output paths when the second parent is absent. |
| Parent2 VCF or gVCF is missing after a trio run | Parent2 output flags were omitted, parent2 was accidentally planned as absent, or the output mount was not writable | Verify all parent2 input/sample/output flags and the output mount; rerun only after confirming the intended family mode. |
| Child-focused downstream analysis lacks parent outputs | The plan treated child-only analysis as child-only DeepTrio output | Keep parent VCF/gVCF outputs for supplied parents during DeepTrio. Downstream analysis may choose the child file after family calling completes. |
| Sample names are swapped or duplicated | BAM `SM` headers were ambiguous, or explicit `--sample_name_*` values do not match the pedigree | Regenerate with explicit unique sample names; inspect VCF/gVCF headers before GLnexus, PED-based checks, or report generation. |
| GLnexus fails or produces surprising filtering | Config does not match assay or filtering intent | Use `DeepVariantWES` for WES with capture BED, `DeepVariantWGS` for standard WGS best-practice merging, and `DeepVariant_unfiltered` only when unfiltered behavior is intended or for documented long-read handoff. |
| GLnexus cannot find inputs | Ordinary VCFs were passed instead of gVCFs, gVCF indexes are absent, or container/host paths were confused | Pass `.g.vcf.gz` files, ensure `.tbi` indexes exist, and remember GLnexus input paths are container-visible while shell redirection is host-side. |
| GLnexus merge combines inconsistent files | gVCFs were generated from different references, region policies, model families, or sample-name plans | Stop and rebuild a consistent per-sample gVCF set before merging. Do not merge across incompatible references or contig naming schemes. |
| `make_examples` processes fewer contigs than expected | Reference FASTA and BAM contig names do not match | Compare FASTA `.fai` contigs with BAM header contigs; choose a compatible reference/read alignment pair or restrict regions to shared contigs. |
| Immediate input-file errors | FASTA `.fai` or BAM `.bai` index is missing, files are not mounted, or command paths use host paths where container paths are required | Create indexes, verify mount pairs, and use container-visible paths in DeepTrio flags. |
| PacBio or ONT run has extra candidate-position intermediates | Candidate partitioning is automatically enabled for long-read models | Treat `candidate_positions@N` and two `make_examples` phases as expected. Do not delete intermediates before investigating memory or shard balance. |
| Long-read `make_examples` runs out of memory | Candidate partitioning was disabled in a custom stage plan, shards are too coarse, or data/coverage is larger than expected | Prefer wrapper defaults for `PACBIO`/`ONT`, increase shards cautiously, and keep `--intermediate_results_dir` for debugging. |
| Non-PAR sex-chromosome calls look biologically inconsistent | Both parents were provided where only the transmitting parent is informative for the child's sex chromosome | For non-PAR X/Y, rerun the relevant interval as a duo with child plus the contributing parent; handle autosomes and PAR regions separately. |
| WES output has poor target behavior | WES model was used without capture intervals, or GLnexus merge omitted the capture BED | Provide the capture BED through `--regions` for calling and `--bed` for GLnexus when performing WES cohort merge. |
| Runtime report is absent | `--runtime_report` was set without `--logging_dir`, or logs were not mounted/writable | Provide a writable container-visible logging directory with `--logging_dir`, or omit runtime reporting. |
| Deprecated postprocess extra-args flag fails | The old combined `--postprocess_variants_extra_args` flag was used | Use sample-specific postprocess extra args for child, parent1, and parent2 instead. |

## Recovery Sequence

1. Rebuild the command with `scripts/deeptrio_command_builder.py` and fix validation errors before running anything.
2. Add `--deeptrio-dry-run` so the generated `run_deeptrio` command includes `--dry_run=true` for stage-command inspection.
3. Confirm every host directory has a Docker mount and every DeepTrio flag uses the container-side path.
4. Confirm all present samples have VCF outputs and, for merge workflows, complete gVCF outputs.
5. For GLnexus, verify config, BED, gVCF list, indexes, and host-side redirect path before executing the pipeline.

## When To Stop And Ask The User

Stop instead of guessing when the user has not provided real sample roles, the sex-chromosome transmitting parent is unclear, reference/contig compatibility cannot be established, a long-read GLnexus preset differs from the documented defaults, or the requested run would require downloading data, pulling images, using GPUs, or executing large native pipelines.
