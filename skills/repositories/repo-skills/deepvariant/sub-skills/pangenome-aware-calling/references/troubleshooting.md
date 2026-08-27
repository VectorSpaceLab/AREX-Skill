# Pangenome-aware Troubleshooting

Use this page for failures specific to pangenome-aware DeepVariant. For generic Docker permissions, missing BAM/FASTA indexes, standard reference/read mismatches, or general installation failures, route to the broader DeepVariant troubleshooting material.

## GBZ Path, Mount, and Shared-memory Failures

Symptoms:

- Docker starts but `load_gbz_into_shared_memory` cannot find the GBZ.
- `make_examples_pangenome_aware_dv` reports GBZ reader errors or cannot attach to shared memory.
- The run fails with `/dev/shm`, allocation, stale shared-memory, or unexpected early deletion messages.

Recovery:

- Confirm the GBZ path is container-visible through a Docker `-v host:container` mount; do not use a host path in `--pangenome` unless it is also valid inside the container.
- Set Docker `--shm-size` at least as large as `--gbz_shared_memory_size_gb`; documented workflows use `--shm-size 12gb` and `--gbz_shared_memory_size_gb 12`.
- Keep `--num_shards` consistent across the wrapper and GBZ loader; it controls how many processes use the shared memory.
- Use a unique `--gbz_shared_memory_name` for concurrent runs or when retrying after an interrupted run.
- If a run was killed, remove stale containers and shared-memory state according to the user’s container/runtime policy before retrying.

## Reference Name Mismatch Inside GBZ

Symptoms:

- GBZ loading succeeds but `make_examples` cannot find expected contigs or reference paths.
- Errors mention missing paths, unknown reference names, contig mismatches, or no pangenome haplotypes for requested regions.
- The FASTA filename suggests one reference label while the GBZ reference path uses another.

Recovery:

- Ask for the reference name embedded in the GBZ; do not infer only from the FASTA basename.
- Pass `--ref_name_pangenome`, commonly `GRCh38` for GRCh38-based HPRC GBZ files.
- If contig names differ by a prefix, pass `ref_chrom_prefix=...` through `--make_examples_extra_args` only after confirming the exact GBZ/read naming convention.
- Keep `--regions` names in the read/reference coordinate system, then map GBZ naming through `--ref_name_pangenome` and any confirmed prefix.

## Pangenome and Reads Sample-name Confusion

Symptoms:

- Output VCF sample name is unexpected.
- `make_examples_pangenome_aware_dv` reports that reads and pangenome sample names are the same.
- A multi-sample BAM/CRAM or GBZ-derived pangenome panel creates ambiguous sample inference.

Recovery:

- Use `--sample_name_reads` for the called sample when BAM/CRAM header inference is ambiguous.
- Use `--sample_name_pangenome` for the pangenome panel; the wrapper default is `hprc_v1.1`.
- Never set reads and pangenome sample names to the same value; pangenome evidence is not the called sample.
- In final user-facing commands, label which sample name controls the output VCF and which labels the pangenome panel.

## WES Postprocess Multiprocessing Surprise

Symptoms:

- A WES user expects `postprocess_variants` to use `--num_shards` CPUs.
- A wrapper dry run shows `postprocess_variants --cpus 0` for WES.

Recovery:

- Explain that the r1.10 wrapper sets WES postprocess CPUs to `0` by default because WES does not benefit from multiprocessing in this pangenome-aware workflow.
- Do not override this just to mirror WGS behavior.
- If the user explicitly wants to experiment, set `--postprocess_cpus N` and mark it as a conditional performance experiment.

## Small-model Defaults and Custom Models

Symptoms:

- User expects a small model to run by default.
- Custom model run fails because model metadata is missing.
- Custom small model changes example/call/postprocess behavior unexpectedly.

Recovery:

- Explain that pangenome-aware r1.10 has no default pangenome-aware small-model config and the wrapper default is `--disable_small_model=true`.
- Use `--customized_model` only with model files and matching metadata expected by r1.10, including model example-info metadata in the model directory.
- Use `--customized_small_model` only with explicit threshold and compatibility guidance; route detailed model-shape concerns to training/custom-model or pipeline-stage material.

## Pangenome-specific Extra Args

Symptoms:

- The wrapper rejects `--make_examples_extra_args` with unpacking or parse errors.
- A dry-run stage command contains unexpected `--noflag` or quoted values.
- An SBX/Roche command fails after copying only part of the specialized argument list.

Recovery:

- Format each extra arg as `flag=value`, comma-separated, with no bare flag names.
- Use `true` or `false` for booleans; the wrapper converts false booleans to `--noflag` in dry-run stage commands.
- Keep SBX arguments together with the matching SBX image and customized model; do not mix them into generic WGS/WES pangenome runs without user confirmation.
- Avoid `use_openvino` with default DeepVariant Docker images unless the image explicitly includes OpenVINO.

## Docker Image Tag Mismatch

Symptoms:

- Container lacks `/opt/deepvariant/bin/run_pangenome_aware_deepvariant`.
- A standard DeepVariant image is used with pangenome flags.
- An SBX command fails with a normal pangenome image, or a normal pangenome command uses an SBX-only image.

Recovery:

- Use a tag that starts with `pangenome_aware_deepvariant-` for generic pangenome-aware workflows, for example `google/deepvariant:pangenome_aware_deepvariant-1.10.0`.
- Use `google/deepvariant:pangenome_aware_deepvariant-sbx` only for the Roche/SBX workflow with matching model and arguments.
- If the user supplies a custom image, ask them to confirm that it contains `run_pangenome_aware_deepvariant`, `make_examples_pangenome_aware_dv`, `load_gbz_into_shared_memory`, `call_variants`, and `postprocess_variants` binaries.

## BWA/VG Evidence and Region Mismatches

Symptoms:

- A VG-mapped BAM is rejected as if only BWA evidence is supported.
- A BWA-mapped BAM is assumed to be non-pangenome because the reads are linear-reference aligned.
- `--regions` uses names that do not match the reads/reference coordinate system.

Recovery:

- Both BWA-mapped and VG-mapped short-read BAMs can be used with the pangenome-aware wrapper when the reads, FASTA, and GBZ are compatible.
- The called sample is always the read sample; the pangenome provides supporting haplotype evidence.
- Keep `--regions` in the read/reference coordinate vocabulary. Use `--ref_name_pangenome` and, only when confirmed, `ref_chrom_prefix=...` for GBZ naming differences.
