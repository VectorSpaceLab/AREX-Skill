# Training Troubleshooting

Start with the validator:

```bash
python scripts/validate_training_config.py --data DATA_ROOT --config CONFIG.json
```

Then use this guide for workflow-specific failures. For install/import, TensorFlow package, model download, and global ffmpeg issues, also see [root troubleshooting](../../../references/troubleshooting.md).

## Config and CSV failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Configuration file ... not found` | `--params_filename/-p` points to a missing JSON file or the command is launched from a different working directory than expected. | Use an absolute config path, or launch from the directory where the relative path resolves. |
| `FileNotFoundError` or Pandas CSV read errors for `train_csv` / `validation_csv` | Spleeter uses CSV paths exactly as stored in the config; it does not join them under `--data`. | Store absolute CSV paths, or run training from the directory that makes the config's CSV paths valid. |
| KeyError for `mix_path`, `vocals_path`, `accompaniment_path`, or another source column | CSV columns do not match `mix_name` and `instrument_list`. | Add `{mix_name}_path`, every `<instrument>_path`, and `duration`. A two-stem `instrument_list` with `accompaniment` requires `accompaniment_path`. |
| Audio file not found after dataset expansion | CSV row path is missing, absolute, has `..`, or is not under `--data`. | Make every row audio path relative to `DATA_ROOT` and verify the joined file exists. |
| `duration` parse errors or non-positive duration | CSV `duration` is empty, non-numeric, zero, or negative. | Store duration in seconds as a positive number. |
| Embedded descriptor has placeholder CSV paths or `null` values | Pretrained descriptors are not complete training configs. | Copy the descriptor to a custom JSON and set real CSVs, `model_dir`, caches, `chunk_duration`, and `n_chunks_per_song`. |

## Dimension and segment failures

| Symptom | Source-derived rule | Fix |
| --- | --- | --- |
| `F is too large and must be set to at most frame_length/2+1` | `F <= frame_length / 2 + 1` | Decrease `F` or increase `frame_length`. |
| `T is too large considering STFT parameters and chunk duratoin` | `(chunk_duration * sample_rate - frame_length) / frame_step >= T` | Decrease `T`, decrease `frame_step`, decrease `frame_length`, increase `chunk_duration`, or use longer audio. |
| `n_chunks_per_song must be positif` | `n_chunks_per_song > 0` | Set `n_chunks_per_song` to `1` for smoke or a positive integer for real training. |
| Dataset builds but training sees no useful batches or appears to hang early | Rows are too short, audio files fail to load, or filters remove all examples after STFT shape checks. | Validate row durations, inspect adapter load errors, use longer fixture audio, and reduce `T` for smoke. |
| Shape errors in model or loss | `n_channels`, `T`, `F`, or instrument list does not match data/features/labels. | Keep config, CSV columns, and actual audio channel intent consistent; regenerate caches after changes. |

The validator intentionally reports multiple errors in one pass, so invalid `F` and `n_chunks_per_song=0` can be fixed together before invoking TensorFlow.

## Cache issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Long preprocessing before first training step | Dataset cache is being populated or audio loading/STFT is slow. | This is normal on first run. Use a tiny fixture for smoke and production caches for real data. |
| Training reuses stale examples after CSV/config changes | TensorFlow dataset cache prefix still points to old cached preprocessing. | Clear cache files or use a new `training_cache` / `validation_cache` prefix whenever data, stems, STFT dimensions, or preprocessing settings change. |
| Programmatic builder waits forever for cache | `wait_for_cache=True` waits for `<cache>.index` that another process never produced. | Use `wait_for_cache=False` unless coordinating cache creation deliberately; delete stale partial cache files if needed. |
| Cache path errors | Parent directory is not writable or cache prefix is treated like a directory path by mistake. | Use a writable file prefix such as `cache/training`, not a source checkout path or protected location. |

## TensorFlow, memory, and GPU warnings

| Symptom | Meaning | Fix |
| --- | --- | --- |
| TensorFlow logs mention missing CUDA libraries or no GPU | GPU acceleration is optional and unverified for this skill. | Continue on CPU for smoke, or use a user-managed TensorFlow GPU environment if GPU training is required. |
| Out-of-memory during graph build or first batches | `batch_size`, source count, `T`, `F`, `n_channels`, or U-Net size is too large. | Lower `batch_size`; for smoke lower `T`/`F`; for production use suitable hardware and monitor memory. |
| Training is very slow on CPU | Real source-separation training is expensive. | Use tiny smoke data only for wiring. For real jobs, plan long runtime or validated GPU acceleration. |
| Estimator logs stop during evaluation | `train_and_evaluate` is building/iterating validation data or waiting due to `throttle_secs`. | Check CPU/disk activity, reduce validation data for smoke, and keep `throttle_secs` reasonable. |

## Checkpoint and output issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No files in `model_dir` | Training failed before estimator initialization, `model_dir` path is unwritable, or command launched from an unexpected directory. | Validate config first, use a writable `model_dir`, and check logs from the start of the run. |
| `checkpoint` exists but expected step file is absent | `save_checkpoints_steps`, `train_max_steps`, and estimator behavior do not align with the expected step. | Inspect all `model.ckpt-*` files and logs; for smoke, do not require a specific checkpoint step unless the run is controlled. |
| Later separation cannot find the custom model | `model_dir` is incomplete or `params_filename` for separation points to the wrong config/model directory. | Finish training successfully, keep the config with the trained `model_dir`, then route custom separation usage to [separation](../../separation/SKILL.md). |
| TensorBoard summaries absent | `save_summary_steps` is too high for a tiny smoke or training stopped early. | Lower `save_summary_steps` for smoke or run more steps. |

## Adapter and audio decoding errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ffmpeg` or `ffprobe` command errors | Default `FFMPEGProcessAudioAdapter` needs system binaries and decodable audio. | Confirm installation in [installation and runtime](../../../references/installation-and-runtime.md), then retry with readable WAV/FLAC/MP3 files. |
| Some files load and others fail | Bad paths, unsupported codecs, corrupt files, or inconsistent permissions. | Validate paths, run `ffprobe` on failing files, and convert data to a known-good WAV format if necessary. |
| Mono/stereo mismatch | Config `n_channels` does not match training intent or adapter output. | Use consistent source files and set `n_channels` explicitly; regenerate fixtures/caches after changing it. |

## Model function errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No model function ... found` | `model.type` does not resolve under Spleeter's model-functions package. | Use `unet.unet` or `unet.softmax_unet`, or install/package a compatible model function in Spleeter's expected layout. |
| `Invalid mask_extension parameter ...` | `mask_extension` is not `zeros` or `average`. | Set `mask_extension` to `"zeros"` for common Spleeter-style configs. |
| Optimizer/loss errors | Unsupported `optimizer`, `loss_type`, or missing `learning_rate`. | Use the default Adam path with `learning_rate`, or verify supported values before customizing. |

## Fixture-specific issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Generated smoke config fails because CSV paths cannot be read | The helper wrote relative CSV paths and training was launched outside the fixture root. | `cd` into the fixture root before `python -m spleeter train -d . -p smoke_config.json`, or edit the config to use absolute CSV paths. |
| Validator says fixture rows are too short | Duration is too small for the selected `T`, `sample_rate`, `frame_length`, and `frame_step`. | Regenerate with a longer `--duration`, lower `--T`, or use the helper defaults. |
| Real training quality is poor after using fixture settings | Fixture settings are intentionally tiny. | Use production sample rate, realistic stems, enough data, and meaningful `train_max_steps`; the fixture is only for command/config smoke. |
