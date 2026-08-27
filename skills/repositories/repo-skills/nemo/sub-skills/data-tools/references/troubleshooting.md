# Troubleshooting

This guide covers shared NeMo Speech data-tool failures from the data-loading docs, utility scripts, Lhotse adapters/tests, tokenizer scripts, ASR evaluator, CTC segmentation, Speech Data Explorer, Speech Data Simulator, checkpoint utilities, and customization dataset prep.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: nemo`, `lhotse`, `soundfile`, `sentencepiece`, `tokenizers`, `dash`, `ctc_segmentation`, `pyarrow`, `wds2idx`, `pandas`, or `numpy`.
- NeMo imports work but a utility fails on an optional package.
- Source checkout scripts assume NeMo is importable from the active environment.

Actions:

1. Confirm the active Python environment has NeMo Speech installed and imports `nemo`.
2. Install only the optional package group needed for the selected workflow; do not install broad extras just to validate data.
3. For tar/audio tools, confirm `soundfile` and system/libsndfile support the target codec.
4. For DALI indexes, install a compatible NVIDIA DALI build that provides `wds2idx`; otherwise skip DALI index generation.
5. For tokenizers, install `sentencepiece` for SPE workflows and `tokenizers` for WPE workflows.
6. For customization prep, install pandas/numpy and the reader backend needed by the file extension, such as Excel support for `.xlsx`.
7. For CTC segmentation, install the tool requirements plus NeMo ASR and audio conversion tools needed by the input formats.
8. For web apps such as Speech Data Explorer, install Dash requirements and confirm the environment can open or proxy the selected port.

## CUDA, GPU, and Compiled Backend Mismatches

Symptoms:

- CUDA OOM or allocator errors during OOMptimizer, ASR evaluator, CTC segmentation, or model-backed data generation.
- PyTorch reports CUDA unavailable or incompatible driver/runtime.
- `gpuRIR`, `pyroomacoustics`, DALI, or compiled audio packages fail to import.

Actions:

1. Separate metadata-only validation from model/GPU workflows; run `scripts/validate_manifest.py` first because it needs no NeMo or CUDA.
2. Check PyTorch/CUDA compatibility before launching model-backed tools.
3. Use CPU-only paths only for lightweight metadata operations or explicitly CPU-supported tools; training and practical inference generally need GPU.
4. Lower batch sizes, shard sizes, worker counts, or sample counts for pilot runs.
5. For OOMptimizer, expect controlled CUDA OOM during search; do not treat the first OOM as an unrelated data failure.
6. For DALI, match DALI, CUDA, and Python versions; if unavailable, omit DALI indexes and use sequential tar access where supported.
7. For RIR simulation, install either `gpuRIR` or `pyroomacoustics` according to the selected mode; compiled build failures usually require system build tools.

## Manifest Schema Mistakes

Symptoms:

- Key errors for `audio_filepath`, `duration`, `text`, or `shard_id`.
- Duration filters drop all samples.
- Dataset weight estimation fails because duration is missing.
- Speech Data Explorer loads but WER/CER is meaningless.
- Lhotse metadata iteration succeeds but actual audio loading fails later.

Actions:

1. Run:

   ```bash
   python scripts/validate_manifest.py data.jsonl \
     --required audio_filepath duration text \
     --min-duration 0.1 --max-duration 30 --summary
   ```

2. For tarred manifests, add `shard_id` to `--required` and omit `--check-files` unless `audio_filepath` intentionally names local files.
3. For manifests with alternative transcript keys, set model/tool `text_field` and validate with `--text-keys text normalized_text pred_text`.
4. Convert single JSON arrays to JSONL when a tool expects one JSON object per line.
5. Fix nonnumeric, negative, or zero durations before duration weighting, bucketing, and training.
6. Treat duplicate `audio_filepath` values as suspicious unless offsets intentionally create multiple segments from one file.
7. Include `sampling_rate` or `sample_rate` when metadata-only workflows should avoid audio header I/O.
8. Use `_skipme` only when a consumer supports it; otherwise remove skipped rows or create filtered data.

## Audio Path Problems

Symptoms:

- File-not-found errors for relative paths.
- Tarred data tries to open tar member names as local files.
- Remote URI paths fail in tools that only support local paths.
- Offset slicing reads unexpected audio.

Actions:

1. Decide path semantics before validation: local non-tarred paths, tar member names, remote URIs, or datastore paths.
2. Use `--check-files` only for local non-tarred paths.
3. For relative local paths, resolve them relative to the manifest location unless the consuming tool documents another base path.
4. For Speech Data Explorer, use `--audio-base-path` for relative audio and `--tar-base-path` for tar member names.
5. For tarred data, ensure manifest `audio_filepath` values match member names inside tar files, not arbitrary source file paths.
6. For offset manifests, confirm `offset + duration` does not exceed the underlying recording.
7. For remote S3/AIS usage, configure credentials through the tool's supported mechanism and never embed secrets in manifests or configs.

## Lhotse Config and Sampling Failures

Symptoms:

- `IncompleteConfigError` asking for `manifest_filepath`, `cuts_path`, or `shar_path`.
- Training hangs in distributed runs.
- `reweight_temperature` length mismatch.
- Dynamic bucketing emits buffer-size warnings.
- Text/multimodal batches duplicate examples across ranks.

Actions:

1. Set exactly one primary input family: NeMo manifest, CutSet, Shar, or `input_cfg`.
2. For Lhotse training, set `trainer.use_distributed_sampler=false`.
3. For tarred/Shar/infinite data, set `limit_train_batches`, `val_check_interval`, and `max_steps`.
4. Avoid `force_finite=true` in normal distributed training; it can cause uneven-rank hangs.
5. If `reweight_temperature` is a list, match its length to `input_cfg` nesting depth; use a scalar to broadcast.
6. Increase `bucket_buffer_size` when Lhotse warns that dynamic bucketing cannot fill buckets well.
7. Precompute `bucket_duration_bins` to avoid slow startup and stabilize runs.
8. Shard raw text files for multi-GPU text or multimodal dataloading.
9. Keep `text_field`, `lang_field`, tokenizer language names, and prompt slots aligned.

## Tarred Dataset and Shard Alignment Failures

Symptoms:

- `shard_id` missing or mismatched.
- Manifest shard ranges and tar shard ranges have different counts.
- Filtered tarred manifests refer to entries not present in tar files.
- DALI index files are missing or named differently from tar files.
- Conversion produces zero valid samples.

Actions:

1. Run tar conversion with `--dry_run` before writing archives.
2. Confirm `num_shards > 0`, `max_duration` is set, and duration filters do not drop all rows.
3. Match `_OP_start..end_CL_` ranges between manifest and tar patterns.
4. Include `shard_id` in tarred manifests and confirm IDs map to the expected tar shard names.
5. Use `_skipme` or `skip_missing_manifest_entries=true` only when the consumer supports subset reading.
6. Use `filter_tarred_audio_dataset.py` to materialize efficient filtered tar/shar subsets when repeated subset reads matter.
7. If DALI indexing fails, check `wds2idx` availability and DALI compatibility; otherwise run without DALI indexes.
8. Avoid conversion-time static bucketing when a DALI/WebDataset path requires compatibility.
9. If audio filenames collide, confirm the converter's duplicate-name/offset handling is acceptable; avoid source paths containing `-sub` where the converter reserves that pattern.

## Hydra CLI Misuse

Symptoms:

- `Key not in struct`, override ignored, or config path not found.
- Shell expands brackets or commas inside overrides.
- A boolean/list override is parsed as a string.

Actions:

1. Use `key=value` syntax for existing Hydra config keys.
2. Use `++key=value` only when adding keys not present in the structured config.
3. Quote list/dict overrides: `bucket_duration_bins='[1.2,2.4]'` or `--prompt "[...]"`.
4. For script-level argparse flags, use `--flag value`; for Hydra scripts, use `key=value` after script/config args.
5. Keep `--config-path` and `--config-name` separate from Hydra field overrides.
6. Test complex commands with `--help` or a small/dry-run mode before launching the full job.

## Tokenizer Failures

Symptoms:

- Missing `text` key in manifest.
- Vocabulary unexpectedly lowercased.
- SentencePiece training runs out of RAM.
- Special-token insertion fails because `sentencepiece_model_pb2.py` is missing or token already exists.

Actions:

1. Validate transcript key consistency before tokenizer training.
2. Use `--data_file` when the corpus is already one text example per line.
3. Pass `--no_lower_case` for case-sensitive tasks.
4. Use `--spe_sample_size` for large corpora and consider `--spe_train_extremely_large_corpus` only on machines with enough RAM.
5. Set language-appropriate `--spe_character_coverage`.
6. For aggregate tokenizers, keep language names aligned with manifest `lang` values.
7. For special-token insertion, generate the required protobuf helper and choose a new output file unless overwriting is intentional.

## ASR Evaluator Failures

Symptoms:

- Model cannot load, downloads fail, or GPU is unavailable.
- Noise augmentation manifest missing.
- Analyst metadata grouping reports empty classes.

Actions:

1. Validate evaluator manifest and any noise manifest first.
2. Confirm model name/checkpoint, tokenizer, and decoding mode with the ASR sub-skill.
3. Pilot on a small manifest before full inference.
4. Ensure metadata fields configured in analyst slots exist in the manifest and have expected value types.
5. Keep augmentation paths and output paths explicit.

## CTC Segmentation Failures

Symptoms:

- Poor or empty segments.
- Text/audio normalization mismatch.
- Audio conversion fails for mp3/flac/ogg.
- Filtering removes most segments.

Actions:

1. Normalize transcripts consistently before segmentation.
2. Confirm audio sample rate and conversion tooling.
3. Start with a short pilot file before large corpora.
4. Tune `window_len`, CER/WER/edge thresholds, and duration thresholds based on pilot metrics.
5. Use GPU-backed ASR inference for practical segmentation speed.
6. Inspect rejected segments to distinguish model mismatch from bad source transcripts.

## Speech Data Explorer Failures

Symptoms:

- Browser cannot connect to the app.
- App loads slowly or consumes too much memory.
- Tarred audio playback fails.
- S3/AIS paths fail authentication.

Actions:

1. Pick an available `--port` and confirm the environment allows local web apps.
2. Validate manifest and use a subset for initial exploration.
3. Disable expensive audio metrics unless needed; `--estimate-audio-metrics` opens audio.
4. For tarred audio, pass `--tar-base-path` and, when available, matching `--dali-index-base`.
5. For two-manifest comparison, pass exactly two manifests and `--names_compared`.
6. For S3/AIS, configure credentials through `--s3cfg` or environment variables and keep secrets out of skill content.

## Speech Data Simulator Failures

Symptoms:

- Missing alignments or speaker IDs.
- RIR simulation package errors.
- Output sessions do not contain all intended speakers.
- Storage usage grows unexpectedly.

Actions:

1. Confirm the input manifest includes the alignment fields required by the simulator workflow.
2. Use speaker enforcement mode when every session must contain the target number of speakers.
3. Disable RIR first, then add `gpuRIR` or `pyroomacoustics` after near-field simulation works.
4. Set output directory, session count, and session duration conservatively for pilots.
5. Route diarization-specific label interpretation to the speaker-diarization sub-skill when present.

## Customization Dataset Prep Failures

Symptoms:

- Template validation fails.
- All completions are empty.
- Completion classes are imbalanced.
- Prompt/completion lacks suffix conventions.
- Prepared train/validation split is too small.

Actions:

1. Use simple brace templates such as `Context: {context} Question: {question} Answer:` and `{answer}\n`.
2. Avoid nested braces, doubled braces, or missing braces.
3. Inspect the first prepared example before training.
4. Use `--drop_duplicates` only when duplicate prompt+completion rows are not meaningful.
5. Set `--val_proportion` based on dataset size; very small datasets may need manual splits.
6. Fix empty completions before training unless the file is explicitly inference-only.
7. Check class imbalance warnings before using classification-style completions.

## Safe Escalation Pattern

When a data workflow fails:

1. Reproduce on the smallest manifest or subset.
2. Validate JSONL and path semantics with the bundled script.
3. Confirm optional dependencies for only the selected workflow.
4. Run the source tool's `--help`, `--dry_run`, `--only_manifests`, or small-sample mode if available.
5. Only then run network downloads, archive writes, model inference, web apps, checkpoint mutation, or GPU-heavy searches.
