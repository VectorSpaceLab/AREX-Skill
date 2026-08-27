# Lhotse and Tarred Data

This reference distills `docs/source/dataloaders.rst`, `scripts/speech_recognition/estimate_duration_bins.py`, `estimate_duration_bins_2d.py`, `estimate_data_weights.py`, `convert_to_tarred_audio_dataset.py`, `filter_tarred_audio_dataset.py`, `partial_conversion_to_tarred_audio_dataset.py`, `create_dali_tarred_dataset_index.py`, NeMo Lhotse source, and Lhotse tests.

## When to Use Lhotse

Use Lhotse dataloading when a task benefits from dynamic batch sizes, dynamic bucketing, duration or token-based filtering, weighted dataset multiplexing, CutSet/Shar data, tarred data subsets, or multimodal sampler fusion.

Key advantages:

- `batch_duration` uses total audio seconds per batch instead of fixed item count.
- Dynamic bucketing reduces padding while preserving randomness.
- `quadratic_duration` penalizes long utterances for transformer-like memory behavior.
- `input_cfg` makes dataset weights and tags explicit.
- Tarred datasets and Shar can become infinite dataloaders, which avoids distributed hangs but changes epoch semantics.

Minimum safe ASR-style overrides:

```bash
++model.train_ds.use_lhotse=true \
++model.train_ds.batch_duration=1100 \
++model.train_ds.quadratic_duration=30 \
++model.train_ds.num_buckets=30 \
++model.train_ds.bucket_buffer_size=10000 \
++model.train_ds.shuffle_buffer_size=10000 \
++trainer.use_distributed_sampler=false \
++trainer.limit_train_batches=1000 \
trainer.val_check_interval=1000 \
trainer.max_steps=300000
```

Rules:

- Set `trainer.use_distributed_sampler=false`; Lhotse handles distributed sampling.
- For tarred/Shar infinite data, set an effective pseudo-epoch length with `limit_train_batches` and `val_check_interval`, and set `max_steps`.
- Prefer precomputed `bucket_duration_bins` for large jobs to avoid slow startup sampling.
- Keep `batch_size` unset or use it only as an additional cap when `batch_duration` is active.

## Input Selection

Single NeMo manifest:

```yaml
model:
  train_ds:
    manifest_filepath: data/train.jsonl
    use_lhotse: true
    batch_duration: 900
    min_duration: 0.1
    max_duration: 30.0
```

Tarred NeMo data:

```yaml
model:
  train_ds:
    manifest_filepath: data/tarred/manifest__OP_0..127_CL_.json
    tarred_audio_filepaths: data/tarred/audio__OP_0..127_CL_.tar
    use_lhotse: true
    batch_duration: 1100
    skip_missing_manifest_entries: false
```

Lhotse CutSet:

```yaml
model:
  train_ds:
    cuts_path: data/cuts.jsonl.gz
    use_lhotse: true
    batch_duration: 1100
```

Lhotse Shar:

```yaml
model:
  train_ds:
    shar_path: data/shar
    use_lhotse: true
    batch_duration: 1100
```

Weighted Shar list:

```yaml
model:
  train_ds:
    shar_path:
      - [data/shar_en, 0.7]
      - [data/shar_pl, 0.3]
    use_lhotse: true
```

`cuts_path` overrides NeMo manifest inputs; `shar_path` overrides both NeMo and `cuts_path` inputs. Avoid setting multiple input families unless you are intentionally testing precedence.

## Estimating Duration Bins

Use duration bins to skip startup-time bin estimation and make training reproducible.

Reference-only NeMo duration-bin utility contract:

- Positional input may be a single NeMo manifest such as `data/train.jsonl`.
- Positional input may be an `input_cfg` YAML such as `data/input_cfg.yaml`.
- Positional input may be an inline weighted list such as `[[data/a.jsonl,0.7],[data/b.jsonl,0.3]]`.
- Positional input may be a Lhotse Shar directory or a direct `key=value` dataloading override.

Useful options:

- `-b/--buckets`: desired number of buckets; output `bucket_duration_bins` length is `num_buckets - 1` for 1D bins.
- `-n/--num_examples`: sample size; avoid `-1` on infinite or huge sources unless intentional.
- `-l/--min_duration` and `-u/--max_duration`: match training filters.
- `-q/--quiet`: print only the bins for scripting.

After estimation, copy output into config:

```yaml
model:
  train_ds:
    num_buckets: 30
    bucket_duration_bins: [1.78, 2.34, 2.69]
```

## Estimating 2D Buckets

Use 2D bucketing for attention encoder-decoder or prompted multilingual ASR/AST where output token length matters.

Reference-only NeMo 2D-bin utility contract:

- Required tokenizer input: `--tokenizer tokenizer.model` for one SentencePiece tokenizer, or multiple tokenizer paths for aggregate tokenizers.
- Aggregate tokenizers also require matching `--langs` values such as `spl_tokens en de`.
- Use `--buckets 30` for top-level duration buckets and `--sub-buckets 5` for token-count subdivisions.
- Use `--text-field` and `--lang-field` when manifests do not use `text` and `lang`.
- Prompted models may require `--prompt-format canary` plus a representative `--prompt` slot list such as `[{'role':'user','slots':{'source_lang':'en','target_lang':'de','task':'ast','pnc':'yes'}}]`.
- Positional input is the same dataset input accepted by the 1D duration-bin utility.

2D output uses nested bins like `[[duration, num_tokens], ...]`. Optional `max_tps` values filter token-per-second outliers; include them when transcript quality has obvious outliers.

## Estimating Dataset Weights

Use dataset weight estimation when `input_cfg` sources should be weighted by hours or examples.

Reference-only NeMo dataset-weight utility contract:

- Inputs are one or more `input_cfg` YAML files.
- Output is one merged YAML file with computed `weight` fields.
- `--strategy num_hours` weights by summed example durations.
- `--strategy num_examples` weights by count.
- `--temperature 0.5` or repeated temperature values rebalance same-level sources.

Rules:

- Inputs are YAML lists of dataset entries, optionally with nested `group` entries.
- `--strategy num_hours` requires every example to expose duration; missing duration raises an error.
- `--strategy num_examples` works for durationless text-like entries.
- Multiple `--temperature` values apply different temperatures at nested group levels.
- The output YAML writes normalized weights at each relevant level.

Temperature intuition:

- `1.0`: preserve relative hours/examples.
- `0.5`: reduce dominance of large datasets.
- `0.0`: equalize same-level datasets.
- `>1.0`: amplify large-dataset dominance.

## Converting to NeMo Tarred Data

Use tarred datasets for large ASR-style training when sequential tar reads are better than many individual files.

Plan first:

1. Validate the source manifest with bundled `scripts/validate_manifest.py`.
2. Decide `num_shards`, `min_duration`, `max_duration`, shuffle seed, codec conversion, and whether entries with offsets should be sliced.
3. Use a dry-run mode, when available, to inspect counts without reading audio or writing tar files.
4. Use a manifest-only mode, when available, to inspect shard manifests before writing tar files.
5. Run the full conversion only when the target directory is correct and has enough storage.

Reference-only NeMo tar-conversion utility contract:

- Required source option: `--manifest_path data/train.jsonl`.
- Required output option: `--target_dir data/tarred_train`.
- Required sharding option: `--num_shards 128`.
- Required upper duration bound: `--max_duration 30.0`; optional lower bound: `--min_duration 0.1`.
- Optional shuffle controls: `--shuffle` and `--shuffle_seed 42`.
- Optional layout controls: `--sort_in_shards`, `--slice_with_offset`, `--keep_files_together`, and `--workers 8`.
- Safety controls: `--dry_run` and `--only_manifests` when supported by the runnable utility.

Important flags:

- `--slice_with_offset`: slice audio using manifest `offset` and `duration` fields.
- `--keep_files_together`: keep entries from the same original file together during shuffle; useful for offsets.
- `--force_codec flac` or similar: transcode audio while writing tar members; requires soundfile/libsndfile support.
- `--buckets_num`: static tar-time duration buckets. Do not confuse with Lhotse dynamic `num_buckets`.
- `--dynamic_buckets_num`: estimates dynamic bins metadata; it does not physically bucket tar output.
- `--write_metadata`: create metadata only; fill missing required metadata before later partial shard creation.
- `--no_shard_manifests`: skip per-shard manifests when they are not needed.

Cautions:

- The source script warns that `audio_filepath` should not contain `-sub` because suffixes are used for duplicate filenames with offsets.
- Bucketing at conversion time is not compatible with DALI + WebDataset indexing.
- DALI index generation requires optional `wds2idx`/DALI support; do not assume it is installed.
- Full conversion reads audio and writes many files; run it only in a deliberate workspace, never as a validation smoke test.

## Tarred Subsets and `_skipme`

For filtered tarred data, prefer one of these strategies:

- Add `_skipme` truthy values to tarred manifests when audio tar files remain unchanged and a consumer can skip entries.
- Use `skip_missing_manifest_entries=true` when a manifest references only a subset of tar entries and sequential tar scanning is acceptable.
- Use `filter_tarred_audio_dataset.py` to create a new Lhotse Shar or NeMo tarred subset when repeated reads of a subset should be efficient.
- Use `partial_conversion_to_tarred_audio_dataset.py` only after `convert_to_tarred_audio_dataset.py --only_manifests` and metadata have prepared selected shards.

Reference-only NeMo tar-filter utility contract:

- Positional inputs are full tarred manifest pattern, tar-file pattern, filtered keep-manifest, and output directory.
- `--output-format lhotse_shar` writes Lhotse Shar; `--output-format nemo_tarred` writes NeMo tarred output.
- `--shard-size 1000` controls the desired number of examples per output shard.

The tar-filter utility loads audio and writes output tar/shar data; treat it as a long-running transformation, not a validator.

## DALI Index Files

The reference-only DALI index utility builds `.index` files under `dali_index/` for tar files in a directory when NVIDIA DALI's `wds2idx` support is installed. Its core Hydra-style options are `tar_dir=data/tarred` and `workers=8`.

Use indexes when a consumer such as Speech Data Explorer or DALI/WebDataset path needs fast random byte-range lookup. If `wds2idx` is missing, install compatible DALI support or skip index-dependent workflows.

## OOMptimizer

OOMptimizer empirically searches per-bucket batch sizes by trying model steps until CUDA OOM boundaries are found.

Use it only after:

1. Manifest/config validation passes.
2. Duration or 2D bins are known.
3. The model config and tokenizer are correct.
4. GPU/CUDA/PyTorch compatibility is verified.
5. The run can tolerate short failed CUDA allocation attempts.

It is GPU/training-heavy and not a generic data validation tool. Route model-specific OOMptimizer interpretation to `../asr/SKILL.md` or `../speechlm2/SKILL.md` when model architecture details dominate.

## Multi-Config and Sampler Fusion

Use `multi_config: true` when a training config has separate modality sub-configs such as `audio:` and `text:` and needs fused samplers.

Fusion options:

- `round_robin`: alternate samplers deterministically.
- `randomized_round_robin`: choose samplers using `sampler_weights`.
- `zip`: draw one batch from each sampler and merge into one CutSet; useful for multimodal gradient accumulation.

Safety checks:

- Each sub-config should have its own length filters and bucketing knobs.
- Ensure tarred/non-tarred sampler flavor compatibility across sub-configs.
- For text in multi-GPU training, shard raw text inputs to reduce duplicate examples across workers and ranks.
- Keep `limit_train_batches`, `val_check_interval`, and `max_steps` explicit when any fused source is effectively infinite.

## Preflight Checklist

Before running any long Lhotse/tarred workflow:

- Validate JSONL structure and required keys with the bundled validator.
- Use `--summary` to inspect transcript fields, durations, duplicates, and blend hints.
- Check local files only when the workflow uses direct local file paths.
- Confirm `text_field`, `lang_field`, and tokenizer language tags match data.
- Confirm tar manifest count, tar shard count, and `_OP_..._CL_` ranges match.
- Confirm `shard_id` exists for tarred NeMo manifests and aligns with tar filenames.
- Avoid `force_finite=true` in distributed training unless explicitly required.
- Record whether optional dependencies are required: `lhotse`, `soundfile`, `DALI/wds2idx`, `sentencepiece`, `tokenizers`, `dash`, `ctc-segmentation`, `sox/pysox`, cloud credentials, or GPU/CUDA.
