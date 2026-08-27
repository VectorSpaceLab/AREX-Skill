# Stage Contracts

DeepVariant r1.10 has three core stages behind the high-level wrappers. Use this reference to map wrapper dry-run commands or custom orchestration back to low-level binaries without depending on source checkout access.

## Stage Map

| Stage | Purpose | Required core inputs | Primary outputs | Notes |
| --- | --- | --- | --- | --- |
| `make_examples` | Reads the reference and aligned reads, finds candidate variants, and encodes pileup tensors as `tf.Example` records. | `--mode`, `--ref`, `--reads`, `--examples`; calling-mode runs normally also use `--checkpoint` or paired model metadata. | `--examples` TFRecord(s); optional `--gvcf` non-variant-site TFRecord(s); optional candidate, run-info, runtime, phase, sitelist, small-model, and debug outputs. | Single-threaded per task; parallelism comes from multiple tasks over sharded outputs. |
| `call_variants` | Loads a TensorFlow checkpoint or SavedModel and evaluates examples. | `--examples`, `--checkpoint`, `--outfile`. | CallVariantsOutput TFRecord(s), usually a logical `.tfrecord.gz` path that may be dynamically sharded. | TensorFlow-heavy; reads `model.example_info.json` or legacy `example_info.json` to validate shape and channels. |
| `postprocess_variants` | Sorts/merges CallVariantsOutput records, resolves genotypes, writes VCF, and optionally merges gVCF blocks. | `--ref`, `--infile`, `--outfile`. | Final `.vcf` or `.vcf.gz` plus index when supported; optional `--gvcf_outfile`. | Must see the complete CallVariantsOutput set for one sample. |

## Wrapper Dry-run Mapping

High-level wrappers such as `run_deepvariant` generate the same stage sequence. A typical dry-run maps like this:

```bash
make_examples \
  --mode calling \
  --ref REF \
  --reads READS \
  --examples INTERMEDIATE/make_examples.tfrecord@N.gz \
  --checkpoint MODEL \
  --task {}

call_variants \
  --examples INTERMEDIATE/make_examples.tfrecord@N.gz \
  --checkpoint MODEL \
  --outfile INTERMEDIATE/call_variants_output.tfrecord.gz

postprocess_variants \
  --ref REF \
  --infile INTERMEDIATE/call_variants_output.tfrecord.gz \
  --outfile OUTPUT.vcf.gz
```

The `{}` placeholder is a wrapper or parallel substitution. It means run `make_examples` once for each integer task from `0` to `N-1`, not one process with literal braces.

When wrapper-level gVCF output is requested, the low-level dataflow adds:

```bash
make_examples --gvcf INTERMEDIATE/gvcf.tfrecord@N.gz ...
postprocess_variants \
  --nonvariant_site_tfrecord_path INTERMEDIATE/gvcf.tfrecord@N.gz \
  --gvcf_outfile OUTPUT.g.vcf.gz ...
```

## `make_examples` Contract

### Modes

| `--mode` | Use | Required or forbidden stage inputs |
| --- | --- | --- |
| `calling` | Inference example generation for normal variant calling. | Requires reads/ref/examples; do not pass `--truth_variants`; permits `--gvcf`; model metadata can define calling flags and channels. |
| `training` | Labeled example generation for model training. | Requires `--truth_variants`; usually requires `--confident_regions` unless using a VCF candidate importer; forbids `--gvcf`. Route complete training plans to `../training-custom-models/SKILL.md`. |
| `candidate_sweep` | Advanced pre-step that writes candidate-position files for balanced later partitioning. | Requires `--candidate_positions`; incompatible with `--proposed_variants`; must be followed by another `make_examples --mode calling` using those positions. |

### Sharded Execution

`make_examples` is single-threaded for a task. Parallelism comes from pairing a sharded output spec with a `--task` value:

```bash
--examples examples.tfrecord@10.gz --task 0
```

This task writes `examples.tfrecord-00000-of-00010.gz`. All tasks `0..9` together form the logical collection `examples.tfrecord@10.gz`.

Rules:

- If `--examples` is sharded as `@N`, run `N` tasks with `--task` values from `0` through `N-1`.
- `--task` must be less than the shard count. `--task > 0` with an unsharded output is invalid.
- Paired output filespecs such as `--gvcf`, runtime output, and phase-output paths must either all be unsharded or all use the same `@N` as `--examples`.
- `make_examples` writes `.example_info.json` using the examples prefix; for sharded outputs, only the first shard path receives the metadata file.
- Example output filenames must resolve to TFRecord-like names such as `.tfrecord`, `.tfrecord.gz`, `.tfrecords`, `.tfrecords.gz`, or `.bagz`; unexpected extensions can be rejected before data processing.

### Calling-mode Model Metadata

In r1.10, calling-mode flags can be loaded from the model's `model.example_info.json` or older `example_info.json` when `--checkpoint` is supplied. Resolution order is command-line flags, then model metadata, then defaults. This affects channel lists and model-specific `make_examples` behavior. If a customized model is used, ensure the paired metadata is present and compatible.

## `call_variants` Contract

Core command shape:

```bash
call_variants \
  --examples examples.tfrecord@N.gz \
  --checkpoint MODEL_OR_SAVEDMODEL_DIR \
  --outfile call_variants_output.tfrecord.gz
```

Inputs:

- `--examples` accepts comma-separated paths, wildcard patterns, or DeepVariant shard specs.
- `--checkpoint` may be a TensorFlow checkpoint path or a SavedModel directory containing `saved_model.pb`.
- The checkpoint or model directory should contain `model.example_info.json` or legacy `example_info.json` so DeepVariant can validate input shape, channels, and channel ablation metadata.

Outputs:

- `--outfile` must be a concrete sharded filename such as `x-00000-of-00004.tfrecord.gz` or must end in `.tfrecord.gz`.
- If `--outfile` is not already a concrete shard, r1.10 can dynamically rewrite `x.tfrecord.gz` to shards such as `x-00000-of-00001.tfrecord.gz` or more shards depending on writer threads and hardware.
- `postprocess_variants --infile x.tfrecord.gz` discovers matching dynamic CVO shards and validates that they form one coherent shard pattern.

Performance and safety:

- Expect TensorFlow import, model loading, and substantial memory use; compiled extensions and official binaries are normally required for production runs.
- `--batch_size`, `--num_readers`, `--writer_threads`, `--execution_hardware`, `--config_string`, and `--kmp_blocktime` are advanced knobs; do not change them without a runtime reason.
- `--stream_examples=true` is for fast-pipeline shared-memory mode and requires `--num_input_shards` plus matching shared-memory orchestration.
- `--allow_empty_examples=true` lets small-region or small-model runs write an empty CVO instead of failing on no examples.

## `postprocess_variants` Contract

Core command shape:

```bash
postprocess_variants \
  --ref REF.fa \
  --infile call_variants_output.tfrecord.gz \
  --outfile output.vcf.gz \
  --cpus N
```

Inputs:

- `--ref` is a FASTA with `.fai`; it defines VCF header contigs and sort order.
- `--infile` must represent the complete CallVariantsOutput set for one sample, not only one shard unless that shard is the whole run.
- `--regions`, when used, should match the `make_examples` region restriction.
- `--checkpoint_json`, when provided, lets model metadata supply postprocessing flags such as `multiallelic_mode` unless the command line already set them.
- `--sample_name` is a fallback only; sample name is normally read from CVOs first, then non-variant site TFRecords when gVCF input is present, then the flag, then the default.

Outputs:

- `--outfile` is the final variant VCF. Gzipped VCF outputs are normally indexed by tabix or CSI depending on contig lengths.
- `--gvcf_outfile` is the final gVCF and is only valid when paired with `--nonvariant_site_tfrecord_path`.
- Optional debug output can add all candidates as extra ALT alleles or an INFO field; ALT-mode is incompatible with the multiallelic model.

Memory and CPU:

- `postprocess_variants` combines and sorts all CVO records, so it can need substantial memory.
- `--cpus < 2` disables parallel processing. `--num_partitions > --cpus` can trade runtime for lower memory.
- Wrappers use `--postprocess_cpus` to set low-level `--cpus`; high values increase memory pressure, especially with gVCF enabled.

## gVCF Stage Pairing

DeepVariant gVCF generation spans two stages:

1. `make_examples --mode calling --gvcf nonvariant.tfrecord@N.gz` creates Variant protos for non-variant sites.
2. `postprocess_variants --nonvariant_site_tfrecord_path nonvariant.tfrecord@N.gz --gvcf_outfile sample.g.vcf.gz` merges non-variant records with variant calls.

Rules:

- `--gvcf` is not allowed in `make_examples --mode training`.
- `postprocess_variants` requires both `--nonvariant_site_tfrecord_path` and `--gvcf_outfile`; setting only one is an error.
- The gVCF TFRecord shard count should match `--examples` for the same `make_examples` task set.
- `--gvcf_gq_binsize` controls non-variant GQ block merging; larger bins reduce record count with coarser quality granularity.
- `--include_med_dp=true` adds MED_DP in gVCF records when requested through `make_examples` extra args.

## Wrapper Extra Args

Wrappers accept comma-separated `flag=value` strings and append them to the target stage command:

| Wrapper flag | Low-level target | Common examples | Checks |
| --- | --- | --- | --- |
| `--make_examples_extra_args` | `make_examples` | `gvcf_gq_binsize=5`, `include_med_dp=true`, `channel_list=BASE_CHANNELS,haplotype` | Validate mode compatibility, model metadata, and `--channel_list` ownership. |
| `--call_variants_extra_args` | `call_variants` | `batch_size=512`, `execution_hardware=cpu`, `writer_threads=1` | Keep TensorFlow resource limits realistic; avoid unsupported hardware modes in the chosen image. |
| `--postprocess_variants_extra_args` | `postprocess_variants` | `num_partitions=64`, `only_keep_pass=true`, `haploid_contigs=chrX,chrY` | Keep gVCF pair complete; ensure regions and haploid/PAR assumptions match the call. |
| `--postprocess_cpus` | `postprocess_variants --cpus` | `0`, `8`, shard count | `0` or `1` disables parallel processing; high values increase memory pressure. |

Extra-arg values with commas must be quoted according to the wrapper parser. If an extra arg overrides a wrapper-set flag, treat the wrapper warning as a prompt to verify that the override was intentional.

## Fast Pipeline Variant

The fast-pipeline path streams `make_examples` to `call_variants` through shared memory. It is experimental and GPU-oriented. Its config files still follow the same stage contracts:

- `make_examples` config uses sharded `--examples` and optional `--gvcf`.
- `call_variants` config provides `--outfile`, `--checkpoint`, batch/writer options, and stream settings.
- `postprocess_variants` config consumes the CVO output and optional non-variant TFRecords.
- Fast-pipeline `--num_shards` must match the `@N` shard count in the stage config files.
- Shared memory size must exceed the buffer-size-by-shards requirement with headroom.
