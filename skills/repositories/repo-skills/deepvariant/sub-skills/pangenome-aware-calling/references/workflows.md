# Pangenome-aware Workflows

Pangenome-aware DeepVariant wraps the normal three-stage DeepVariant flow, but `make_examples` consumes pangenome haplotypes from `--pangenome` in addition to sample reads. Use the packaged `/opt/deepvariant/bin/run_pangenome_aware_deepvariant` binary inside a pangenome-aware DeepVariant Docker image or an equivalent Bazel-built binary environment.

## Command Builder

Use the bundled helper to generate a shell-safe Docker command without executing Docker:

```bash
python scripts/pangenome_command_builder.py \
  --model_type WGS \
  --ref /reference/GRCh38_no_alt_analysis_set.fasta \
  --reads /input/sample.bam \
  --pangenome /input/hprc-v1.1-mc-grch38.gbz \
  --output_vcf /output/sample.output.vcf.gz \
  --output_gvcf /output/sample.output.g.vcf.gz \
  --regions chr20 \
  --num_shards 96 \
  --intermediate_results_dir /output/intermediate_results_dir \
  --mount /host/input:/input \
  --mount /host/reference:/reference \
  --mount /host/output:/output
```

The helper validates required values, image-tag shape, container path assumptions, pangenome identity flags, shared-memory sizing, and WES postprocess behavior. It never reads BAM/CRAM/GBZ/FASTA contents and never runs Docker.

## WGS With BWA- or VG-mapped Reads

Use this pattern for short-read WGS BAM/CRAM aligned either to the linear reference with a mapper such as BWA or to a pangenome graph with a mapper such as VG Giraffe. The reads must still be compatible with `--ref`, and the GBZ must contain the same reference sequence under the name supplied by `--ref_name_pangenome`.

```bash
sudo docker run \
  -v /host/input:/input \
  -v /host/output:/output \
  -v /host/reference:/reference \
  --shm-size 12gb \
  google/deepvariant:pangenome_aware_deepvariant-1.10.0 \
  /opt/deepvariant/bin/run_pangenome_aware_deepvariant \
  --model_type WGS \
  --ref /reference/GRCh38_no_alt_analysis_set.fasta \
  --reads /input/sample.chr20.bam \
  --pangenome /input/hprc-v1.1-mc-grch38.gbz \
  --output_vcf /output/sample.output.vcf.gz \
  --output_gvcf /output/sample.output.g.vcf.gz \
  --num_shards 96 \
  --regions chr20 \
  --intermediate_results_dir /output/intermediate_results_dir
```

For a BWA-mapped BAM, treat the pangenome as additional haplotype evidence while the called sample remains the read sample. For a VG-mapped BAM, still use the pangenome-aware wrapper; do not switch to standard `run_deepvariant` merely because the reads were graph-mapped.

Use `--dry_run=true` on the DeepVariant wrapper when the user wants stage commands for manual inspection rather than execution. The dry run expands the GBZ loader, `make_examples_pangenome_aware_dv`, `call_variants`, and `postprocess_variants` commands.

## WES With BWA-mapped Reads

Use `--model_type WES` for short-read exome data. Keep target BED handling separate from calling unless the user wants region-limited calling: target BEDs are often used only during benchmarking, while `--regions` restricts DeepVariant calling itself.

```bash
sudo docker run \
  -v /host/input:/input \
  -v /host/output:/output \
  -v /host/reference:/reference \
  --shm-size 12gb \
  google/deepvariant:pangenome_aware_deepvariant-1.10.0 \
  /opt/deepvariant/bin/run_pangenome_aware_deepvariant \
  --model_type WES \
  --ref /reference/GRCh38_no_alt_analysis_set.fasta \
  --reads /input/sample.wes.bam \
  --pangenome /input/hprc-v1.1-mc-grch38.gbz \
  --output_vcf /output/sample.output.vcf.gz \
  --output_gvcf /output/sample.output.g.vcf.gz \
  --num_shards 96 \
  --regions chr20 \
  --intermediate_results_dir /output/intermediate_results_dir
```

The r1.10 wrapper sets `postprocess_variants --cpus 0` for WES when `--postprocess_cpus` is not supplied because WES does not benefit from postprocess multiprocessing in this workflow. Mention this before overriding it.

## GBZ Shared-memory Flow

When `--pangenome` ends with `.gbz`, the wrapper prepends a GBZ loader command before pangenome-aware `make_examples`:

1. `load_gbz_into_shared_memory` loads GBZ sequences into a named shared-memory segment using `--pangenome_gbz`, `--ref_name_pangenome`, `--shared_memory_size_gb`, optional `--shared_memory_name`, and `--num_shards`.
2. `make_examples_pangenome_aware_dv` receives the same pangenome path plus `--use_loaded_gbz_shared_memory`, `--ref_name_pangenome`, optional `--gbz_shared_memory_name`, and `--sample_name_pangenome`.
3. `call_variants` uses `/opt/models/pangenome_aware_deepvariant/wgs` or `/opt/models/pangenome_aware_deepvariant/wes` unless `--customized_model` is provided.
4. `postprocess_variants` writes the final VCF and optional gVCF.

Plan these constraints together:

- Docker must provide enough `/dev/shm`; documented workflows use `--shm-size 12gb`, matching wrapper default `--gbz_shared_memory_size_gb 12`.
- `--num_shards` is passed to GBZ loading; set it to the number of `make_examples` shard processes that will use shared memory.
- If multiple runs share a host/container namespace, give each run a distinct `--gbz_shared_memory_name`.
- `--ref_name_pangenome` must match the reference name embedded in the GBZ, not the FASTA filename.

## Intermediate Outputs

If `--intermediate_results_dir` is set, expect container-visible files with these basename patterns:

```text
make_examples_pangenome_aware_dv.tfrecord-?????-of-?????.gz
call_variants_output.tfrecord.gz
gvcf.tfrecord-?????-of-?????.gz
```

The gVCF intermediate appears when `--output_gvcf` is requested. Keep intermediates under a mounted output directory when the user wants to inspect stage outputs, preserve logs, or rerun stage-level commands from a dry run.

## Runtime Reports and VCF Stats

`--logging_dir` enables per-stage logs. `--runtime_report=true` requires `--logging_dir` and produces make_examples runtime-by-region data plus an HTML report. `--vcf_stats_report=true` writes an HTML report next to the final VCF basename; set `--report_title` when the default sample-name title would be ambiguous.

## Roche/SBX Workflow Shape

Roche/SBX pangenome-aware calling is specialized. It uses `google/deepvariant:pangenome_aware_deepvariant-sbx`, a mounted custom model directory, `--customized_model`, a dense `--make_examples_extra_args` list, and `--postprocess_variants_extra_args="multiallelic_mode=product"`. Do not apply SBX options to ordinary WGS/WES pangenome runs unless the user confirms SBX data, the matching model files, and the specialized image.

## Benchmark Handoff

hap.py benchmarking is optional and unsafe to run without user-confirmed truth VCF/BED, reference FASTA, Docker image, mounts, and runtime budget. For WES, benchmark commands often include both confident regions and a target BED; do not treat the benchmark target BED as a required DeepVariant calling flag unless the user asks for region-limited calling.
