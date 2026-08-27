# InternVideo dataset troubleshooting

## JSON versus JSONL confusion

- InternVideo2 multi-modality loaders generally expect JSON arrays loaded with `json.load`.
- InternVideo3 SFT expects JSONL, one chat object per line.
- A file with valid JSON objects on separate lines is not a valid JSON array; a JSON array is not valid JSONL for the SFT loader.

## Empty or missing dataset

- Many configs default to placeholders such as `your_path`; set the relevant data path variables or config fields before launch.
- Check both annotation path and media root/prefix. A valid annotation file can still produce runtime failures if media paths are relative to a different root.
- Line-list parsers split on the configured delimiter without CSV quoting. Paths containing spaces produce field-count errors.
- Caption filtering can remove samples with very short captions unless `jump_filter` is enabled.

## InternVideo3 tokenization drops or fakes records

- SFT dataset code catches many per-record exceptions and can substitute fake data. If training appears to continue but useful sample counts are low, inspect tokenizer warnings and validate JSONL.
- Missing `image_wh` for images/videos prevents reliable token counting during packing.
- Placeholder counts must match media counts. Use `<IMG_CONTEXT>` for each image item and `<VIDEO_CONTEXT>` for each video item.
- `processed_video_length` and `processed_fps` must appear together. `frames_timestamp` length must match processed length.
- If no origin video metadata is provided, random frame-count sampling is used and precise timestamps are unavailable.

## Audio/video records fail

- `audio_video` records can read an explicit `audio` path or extract audio from video, depending on config. Mismatching records and flags leads to loader recursion or failures.
- Audio loading needs `librosa` or `torchaudio` plus codecs. Missing audio streams can be padded only when the config asks for zero-audio padding.
- Remote object storage requires a configured Petrel/Ceph client. Do not assume `s3://` paths work in a plain local environment.

## Video decode problems

- `decord` is the default reader in many video loaders. `.webm` may force lower thread counts in some paths.
- Corrupt or missing videos often cause loaders to resample another index, hiding the true failure rate. Run validation/path checks on a sample before training.
- Frame counts, fps, and clip start/end values must be consistent. Negative sentinel values should be intentional.
- For frame folders, verify naming templates and frame counts; for video files, check decoder support for the suffix and codec.

## InternVideo-Next list quirks

- The multi pretraining list needs exactly six fields: `source path total_time start_time end_time label`.
- The current loader path supports video decoding only for multi pretraining; frame-folder fallback is not implemented there.
- `source == ssv2` controls a special transform. Normalize source labels before large runs.

## Benchmark data caveats

- InternVideo3 evaluation scripts often set `HF_DATASETS_OFFLINE=1`; datasets must be staged or cached in advance.
- VINDLU-style retrieval JSONs, MVBench, VideoMME, MLVU, LongVideoBench, temporal grounding, and other benchmarks have separate licenses/layouts. Do not treat benchmark names as proof that local data exist.
- YouTube-derived datasets can lose videos over time. Record missing-media rates separately from annotation syntax errors.

## Shared-memory/cache issues

- InternVideo3 SFT tokenization uses caches and may create shared-memory-backed offsets/token counts. Very large JSONL files can exhaust `/dev/shm` or cache storage.
- Change cache tags or clear per-run caches after altering processor, pixel budget, fps, frame caps, `add_vision_id`, or max sequence length.
- Use `--max-records` in the bundled validator for cheap syntax/schema checks before running full tokenization.

## Recommended debug path

1. Validate annotation syntax/schema with the bundled validator.
2. Re-run with `--check-paths --media-root <media-root>` on a small sample if local data are staged.
3. For video decode issues, test one representative short file with the same reader family (`decord`, `av`, or image-folder loader) in the intended environment.
4. Only then schedule distributed training/evaluation.
