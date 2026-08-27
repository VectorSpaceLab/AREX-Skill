# Pangenome-aware Flags

This reference focuses on flags that differ from standard DeepVariant or are easy to confuse in pangenome-aware runs. Route ordinary `run_deepvariant` usage to the germline sub-skill and detailed stage mechanics to the pipeline-stages sub-skill.

## Required Wrapper Flags

| Flag | Use | Notes |
| --- | --- | --- |
| `--model_type` | Select pangenome-aware model family. | r1.10 supports `WGS` and `WES`. |
| `--ref` | FASTA reference used for reads. | Needs a matching `.fai`; must be compatible with reads and the GBZ reference path. |
| `--reads` | Sample reads to call. | Aligned, sorted, indexed BAM or CRAM. Lower-level code accepts comma-separated inputs, but prefer one sample unless the user has a known multi-input plan. |
| `--pangenome` | Pangenome evidence. | Use a `.gbz` for documented pangenome-aware workflows. BAM/CRAM pangenome-style inputs are lower-level and need explicit user evidence. |
| `--output_vcf` | Final VCF path. | Use a mounted output directory in Docker. |

## Pangenome Identity Flags

| Flag | Default | When to set |
| --- | --- | --- |
| `--ref_name_pangenome` | `GRCh38` | Set whenever the reference name inside the GBZ differs from the FASTA basename or expected assembly label. This value must correspond to the reads/reference coordinate system. |
| `--sample_name_pangenome` | `hprc_v1.1` in the wrapper | Set when using a pangenome panel with a different sample/panel name. It must not collide with the reads sample name. |
| `--sample_name_reads` | inferred from reads header | Set when the BAM/CRAM header has multiple samples, no sample, or a sample name that should not appear in the output VCF. |
| `ref_chrom_prefix` via `--make_examples_extra_args` | empty | Use only when GBZ chromosome names need a prefix such as `GRCh38.` to match read/reference contigs. |

For a difficult WGS case where the FASTA is named `GRCh38_no_alt_analysis_set.fasta` but the GBZ stores the reference as `GRCh38`, pass `--ref_name_pangenome GRCh38`; do not infer it from the FASTA basename.

## Shared-memory Flags

| Flag | Default | Use |
| --- | --- | --- |
| Docker `--shm-size` | none | Required Docker resource limit; use at least the wrapper GBZ size, commonly `12gb` for the documented GBZ. |
| `--gbz_shared_memory_size_gb` | `12` | Size passed to the GBZ loader. Increase if loading fails with shared-memory allocation errors. |
| `--gbz_shared_memory_name` | binary default unless set | Set a unique value when concurrent runs might collide or when debugging stale shared-memory segments. |
| `--num_shards` | `1` | Also tells the GBZ loader how many shard processes will use shared memory. Avoid oversizing because stale shared memory can persist longer than intended. |

When `--pangenome` ends in `.gbz`, the wrapper loads sequences into shared memory before `make_examples` and passes `--use_loaded_gbz_shared_memory` internally.

## Model and Data Compatibility

- Use `--model_type WGS` for short-read whole-genome data, whether reads are BWA-mapped to the linear reference or VG-mapped in a pangenome-aware workflow.
- Use `--model_type WES` for short-read exome data; do not substitute the standard WES wrapper when `--pangenome` is required.
- Keep `--ref`, `--reads`, and `--pangenome` on compatible coordinate systems. Pangenome-aware calling can support a GBZ reference name that differs from the FASTA basename through `--ref_name_pangenome`, but it does not fix incompatible assemblies.
- The pangenome wrapper is source/Docker/Bazel oriented in r1.10. A Python package import being available does not mean `run_pangenome_aware_deepvariant` is on `PATH`.

## Outputs and Reports

| Flag | Use |
| --- | --- |
| `--output_gvcf` | Enables gVCF output and creates a sharded `gvcf.tfrecord@N.gz` intermediate. |
| `--intermediate_results_dir` | Keeps pangenome-aware TFRecords, call-variants output, and gVCF intermediates in a user-mounted directory. |
| `--logging_dir` | Writes per-stage logs. Required for `--runtime_report`. |
| `--runtime_report` | Produces make_examples runtime-by-region TSV shards and an HTML report. |
| `--vcf_stats_report` | Produces VCF statistics HTML from the final VCF. |

## Small-model Defaults

The pangenome-aware r1.10 wrapper defines no default pangenome-aware small-model configs and sets `--disable_small_model=true` by default. Only enable a small model when the user supplies a known compatible `--customized_small_model` and threshold/shape guidance through `--make_examples_extra_args`.

If `--customized_small_model` is used, the wrapper allows empty examples in `call_variants` and expects the small-model CVO records path during postprocessing. Treat this as advanced behavior and route detailed stage consequences to the pipeline-stages sub-skill.

## WES Postprocess CPUs

If `--postprocess_cpus` is omitted, the wrapper normally uses `--num_shards`, but for `--model_type WES` it sets postprocess CPUs to `0` because WES does not benefit from multiprocessing in this workflow. If a WES user expects postprocess multiprocessing, explain this default and only override it with `--postprocess_cpus` when they explicitly accept the experiment.

## Extra Args

The wrapper supports comma-separated `flag=value` lists:

- `--make_examples_extra_args`: pangenome-aware `make_examples` flags such as `ref_chrom_prefix`, pileup dimensions, strict insertion filters, read normalization, and haplotype sorting.
- `--call_variants_extra_args`: `call_variants` flags such as batch size or TensorFlow config strings. Default DeepVariant Docker images do not include OpenVINO, so avoid `use_openvino` unless the user confirms a compatible custom image.
- `--postprocess_variants_extra_args`: postprocess flags such as `multiallelic_mode=product` or quality thresholds.

Use `flag=true` or `flag=false` for booleans. The wrapper converts false booleans to `--noflag` in stage commands. A bare flag name without `=` is invalid.

## Roche/SBX Specialized Arguments

Roche/SBX pangenome-aware workflows use a specialized Docker tag and a customized model checkpoint plus a dense `--make_examples_extra_args` list. Treat SBX as data/model-specific rather than a generic pangenome default.

Typical SBX additions include:

```text
--customized_model /model/model.ckpt
--make_examples_extra_args="alt_aligned_pileup=single_row,create_complex_alleles=true,enable_strict_insertion_filter=true,keep_legacy_allele_counter_behavior=true,keep_only_window_spanning_haplotypes=true,keep_supplementary_alignments=true,min_mapping_quality=0,normalize_reads=true,pileup_image_height_pangenome=100,pileup_image_height_reads=100,pileup_image_width=301,sort_by_haplotypes=true,trim_reads_for_pileup=true,vsc_min_fraction_indels=0.08,ws_min_base_quality=25"
--postprocess_variants_extra_args="multiallelic_mode=product"
```

Use an SBX image tag only when the user intentionally targets that workflow and provides the matching model files, including model metadata expected by r1.10.
