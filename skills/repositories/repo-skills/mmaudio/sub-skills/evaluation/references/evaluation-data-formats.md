# Evaluation Data Formats

This reference describes the schemas consumed by MMAudio evaluation and onset scoring. Use it to validate paths and metadata before launching CUDA generation or CPU metrics.

## Batch evaluation dataset selection

The evaluator dispatches by dataset-name prefix in this order:

1. names starting with `audiocaps_full` -> AudioCaps full;
2. names starting with `audiocaps` -> AudioCaps;
3. names starting with `moviegen` -> MovieGen;
4. names starting with `vggsound` -> VGGSound.

Custom suffixes such as `vggsound-local` are acceptable if the prefix still matches. Use the base prefix in `dataset=` unless you intentionally need a custom output namespace.

## Default path keys

| Dataset selector | Required override keys | Distilled default relative paths | Notes |
|---|---|---|---|
| `audiocaps` | `eval_data.AudioCaps.audio_path`, `eval_data.AudioCaps.csv_path` | `../data/AudioCaps-test-audioldm-ver`, `../data/AudioCaps-test-audioldm-ver/data.csv` | Text-only generation; audio directory must exist for listing. |
| `audiocaps_full` | `eval_data.AudioCaps_full.audio_path`, `eval_data.AudioCaps_full.csv_path` | `../data/AudioCaps-test-full-ver`, `../data/AudioCaps-test-full-ver/data.csv` | Same schema as AudioCaps, usually larger. |
| `vggsound` | `eval_data.VGGSound.video_path`, `eval_data.VGGSound.csv_path` | `../data/test-videos`, `../data/vggsound.csv` | Video-conditioned generation from VGGSound test split. |
| `moviegen` | `eval_data.MovieGen.video_path`, `eval_data.MovieGen.jsonl_path` | `../data/MovieGen/MovieGenAudioBenchSfx/video_with_audio`, `../data/MovieGen/MovieGenAudioBenchSfx/metadata` | Video-conditioned generation with one prompt JSON object per video. |

Hydra dotlist examples:

```bash
eval_data.VGGSound.video_path=/datasets/vggsound/test-videos
eval_data.VGGSound.csv_path=/datasets/vggsound/vggsound.csv
eval_data.AudioCaps.csv_path=/datasets/audiocaps/data.csv
eval_data.MovieGen.jsonl_path=/datasets/moviegen/metadata
```

Quote values that contain spaces or shell metacharacters.

## AudioCaps schema

`AudioCapsData` requires:

- `audio_path`: directory containing `.wav` or `.flac` files. The constructor lists this directory, so it must exist even though the batch generator does not condition on these audio files.
- `csv_path`: CSV file with a header row containing at least `name` and `caption`.

Rows become evaluation items with:

| Item key | Source | Output use |
|---|---|---|
| `name` | CSV `name` column | Generated file name `<name>.flac`. |
| `caption` | CSV `caption` column | Text condition for MMAudio generation. |

Important behavior:

- The implementation records all CSV rows as data items; it does not strictly filter rows to only those with matching audio files.
- Use unique, filesystem-safe `name` values to avoid output overwrites.
- Captions should be non-empty strings. Empty captions degrade generation and can hide metadata mistakes.

Minimal valid CSV:

```csv
name,caption
sample_000,a dog barking twice in a room
sample_001,footsteps on gravel with distant traffic
```

## VGGSound schema

`VGGSound` requires:

- `video_path`: directory containing `.mp4` files;
- `csv_path`: comma-separated file without a header, interpreted as columns `id`, `sec`, `caption`, `split`.

For rows where `split == test`, the evaluator expects a video filename:

```text
<id>_<sec as 6-digit zero-padded integer>.mp4
```

Example row and expected file:

```csv
abc123xyz,42,hammering a nail,test
```

Expected video file:

```text
abc123xyz_000042.mp4
```

Only matching test rows are used. Missing videos are skipped with logging, because some original YouTube videos may no longer be available.

Each sample yields:

| Item key | Source / transform |
|---|---|
| `name` | `<id>_<sec:06d>` |
| `caption` | CSV `caption` column |
| `clip_video` | RGB video transformed to CLIP input at 384x384 and 8 FPS |
| `sync_video` | RGB video transformed to Sync input at 224 center crop and 25 FPS |

For `duration_s=8`, a usable video needs at least 64 CLIP frames and 200 Sync source frames before internal sequence downsampling/truncation. The generated model sequence uses a sync sequence length of 192 for the default 8-second config.

## MovieGen schema

The batch evaluator's MovieGen path requires:

- `video_path`: directory containing `.mp4` files;
- `jsonl_path`: directory containing one metadata file per video, named `<video_stem>.jsonl`.

Despite the `.jsonl` suffix, the consumed metadata file is parsed as one JSON object. It must contain an `audio_prompt` field:

```json
{"audio_prompt": "metal tools clanking in a workshop"}
```

Each `.mp4` stem in the video directory becomes an item. For a video file `clip_007.mp4`, the metadata file must be `clip_007.jsonl`, and the output file becomes `clip_007.flac`.

The MovieGen dataset class has a 10-second constructor default, but batch evaluation passes the Hydra `duration_s` value. Make `duration_s` explicit in commands so the intended benchmark length is obvious.

## Video preprocessing assumptions

Both VGGSound and MovieGen video-conditioned evaluation use two streams:

| Condition stream | Resize / crop | Frame rate | Default 8-second expected frames | Failure mode |
|---|---:|---:|---:|---|
| CLIP | resize to 384x384 | 8 FPS | 64 | `CLIP video returned None` or `CLIP video too short`. |
| Sync | resize to 224 then center crop | 25 FPS | 200 raw frames before downstream sequence shaping | `Sync video returned None` or `Sync video too short`. |

Invalid video samples are converted to `None` by the dataset wrapper and filtered by the evaluation collate function. If an entire batch is invalid, the loader can still fail, so a dataset with many short or corrupt videos should be cleaned before a long run.

## Generated audio output schema

Batch evaluation saves one audio file per successful item:

```text
<hydra-run-dir>/<dataset or dataset-output_name>/<sample-name>.flac
```

The sample rate is selected by model mode:

- `small_16k`: 16,000 Hz;
- `small_44k`, `medium_44k`, `large_44k`, `large_44k_v2`: 44,100 Hz.

The writer uses the sample name directly. Avoid duplicate names or names with path separators.

## Onset evaluation input schema

The bundled `scripts/evaluate_onsets.py` scores generated audio against text files of ground-truth event times.

Predicted audio directory:

- contains `.flac` and/or `.wav` files;
- each file should be a single generated 8-second-style prediction unless you override `--duration`;
- default analysis resamples to 22,050 Hz to match the original metric logic.

Ground-truth directory:

- contains one text file per prediction;
- each non-empty line starts with an onset time in seconds;
- additional columns after the first whitespace token are ignored;
- times greater than or equal to `--duration` are ignored.

Default naming in the bundled evaluator:

```text
prediction: sample_denoised.flac
GT file:    sample_times.txt
```

The defaults implement this by stripping `_denoised` from the predicted stem and appending `_times`. If your GT files are `sample.txt`, pass `--gt-suffix ''`. If your predictions do not have a denoising suffix but GT files still use `_times.txt`, the defaults also map `sample.flac` to `sample_times.txt`.

Example ground-truth file:

```text
0.352 impact
1.910
3.044 door_close
```

## Onset metric outputs

The onset evaluator reports aggregate metrics across files:

| Metric | Meaning |
|---|---|
| `Overall accuracy` | Mean per-file hit count divided by number of GT onset times. |
| `Overall AP` | Mean per-file average precision using waveform-window confidence for matched and leftover predicted onsets. |
| `Overall F1` | Mean per-file F1 after converting nonzero predicted confidences to positives. |

By default the bundled script prints results only. Use `--write-results` to create `eval_results.txt` in the prediction directory, or `--output-file <path>` to write elsewhere.
