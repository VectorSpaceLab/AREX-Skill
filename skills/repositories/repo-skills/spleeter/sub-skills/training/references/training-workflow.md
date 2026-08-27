# Training Workflow

This workflow prepares data and configuration before calling Spleeter's TensorFlow estimator training path. It is intentionally conservative: validate files and dimensions first, run a tiny smoke only when needed, and treat real training as a long-running user-managed job.

## Prerequisites

- Runtime: Spleeter 2.4.2 on Python `>=3.8,<3.12`, TensorFlow 2.12.1, and system `ffmpeg`/`ffprobe`. See [installation and runtime](../../../references/installation-and-runtime.md).
- Audio adapter: the default CLI adapter is `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter`, which needs `ffmpeg` and `ffprobe` on `PATH`.
- Hardware: the verified path is TensorFlow CPU. GPU may accelerate training if the user's TensorFlow/CUDA stack is already working, but this skill does not promise GPU verification.
- Scope: this covers custom model training, not pretrained separation or MUSDB scoring. For using a trained model for separation, route to [separation](../../separation/SKILL.md). For metrics, route to [evaluation](../../evaluation/SKILL.md).

## Training CLI

| Option | Alias | Required | Meaning |
| --- | --- | --- | --- |
| `--data DATA_ROOT` | `-d` | yes | Directory that contains the audio files named in CSV rows. CSV row audio paths are joined under this root. |
| `--params_filename CONFIG` | `-p` | yes for custom training | JSON config file. Spleeter reads it through `load_configuration`; file paths inside it are used exactly as stored. |
| `--adapter ADAPTER` | `-a` | no | Dotted audio adapter class. Default is `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter`. |
| `--verbose` | none | no | Enables verbose Spleeter logs. |

Canonical command:

```bash
python -m spleeter train \
  --data DATA_ROOT \
  --params_filename CONFIG.json \
  --adapter spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter \
  --verbose
```

The console entry point `spleeter train ...` is equivalent when the package entry point is installed.

## Tiny smoke fixture

Use the bundled fixture only to verify that a training config and the TensorFlow estimator path are wired correctly. It is not a meaningful source-separation dataset.

From the sub-skill directory, generate a tiny two-stem fixture:

```bash
python scripts/create_training_fixture.py \
  --root ./spleeter-training-fixture \
  --stems 2 \
  --songs-per-split 2 \
  --duration 3 \
  --sample-rate 8000 \
  --write-config ./spleeter-training-fixture/smoke_config.json
```

Validate it:

```bash
python scripts/validate_training_config.py \
  --data ./spleeter-training-fixture \
  --config ./spleeter-training-fixture/smoke_config.json
```

The generated smoke config stores `train_csv` and `validation_csv` relative to the fixture root. Because Spleeter uses CSV paths exactly as stored, either run the training command from the fixture root or edit those CSV paths to absolute paths:

```bash
cd ./spleeter-training-fixture
python -m spleeter train -d . -p smoke_config.json --verbose
```

For a four-stem fixture, use `--stems 4`; columns become `mix_path`, `vocals_path`, `drums_path`, `bass_path`, `other_path`, and `duration`.

## Real training setup

1. Choose the source set.
   - Two stems usually use `instrument_list: ["vocals", "accompaniment"]`.
   - Four stems usually use `instrument_list: ["vocals", "drums", "bass", "other"]`.
   - The mix column name is derived from `mix_name`; with `mix_name: "mix"`, the CSV column is `mix_path`.
2. Build a data root that contains all audio files named by the CSV rows. Row paths should be relative paths under `--data`.
3. Create `train_csv` and `validation_csv` with one row per song or excerpt. Each row needs `{mix_name}_path`, one `<instrument>_path` column for every instrument, and a positive `duration` in seconds.
4. Create a JSON config. Start from the schema in [data-format-and-config.md](data-format-and-config.md), not directly from an embedded pretrained descriptor unless you copy and fix placeholder paths, `null` values, caches, and training limits.
5. Run the validator before invoking TensorFlow:

```bash
python scripts/validate_training_config.py --data DATA_ROOT --config CONFIG.json
```

6. Pick cache locations. `training_cache` and `validation_cache` are TensorFlow dataset cache prefixes; their parent directories must be writable. Keep them near the dataset when possible and clear them when changing audio, CSV rows, STFT dimensions, source stems, or preprocessing settings.
7. Start training with `python -m spleeter train ...`. Real Spleeter training can run for many hours or days depending on dataset size, `train_max_steps`, `batch_size`, hardware, and model size.

## What the train command does

The `train` command:

1. Loads the audio adapter with `AudioAdapter.get(adapter)`.
2. Loads the JSON config with `load_configuration(params_filename)`.
3. Creates a `tf.estimator.Estimator` using `spleeter.model.model_fn`, `model_dir`, and a `RunConfig` using:
   - `save_checkpoints_steps`
   - `random_seed`
   - `save_summary_steps`
   - `log_step_count_steps=10`
   - `keep_checkpoint_max=2`
   - TensorFlow session GPU memory fraction set to 0.45 when a GPU is used.
4. Builds the training input function from `get_training_dataset(params, audio_adapter, data)` and the validation input function from `get_validation_dataset(params, audio_adapter, data)`.
5. Calls `tf.estimator.train_and_evaluate` with `max_steps=params["train_max_steps"]` and validation throttling from `throttle_secs`.
6. Writes a Spleeter model probe in `model_dir` after successful training.

## Checkpoint and output expectations

`model_dir` is the estimator output directory. During or after a successful smoke run, expect files such as:

- `checkpoint`
- `model.ckpt-<step>.index` / `.data-*` / `.meta`
- TensorFlow event files for summaries
- a Spleeter model probe written after the command completes

Do not treat absence of a late checkpoint as proof of failure until logs and `train_max_steps` are checked. With very small `train_max_steps`, the exact checkpoint step depends on TensorFlow estimator behavior and `save_checkpoints_steps`.

## Resource caveats

- Tiny smoke data validates wiring only; it does not produce a useful separator.
- CPU training is valid but slow. GPU logs may appear even on CPU-only systems; only rely on GPU when the user's TensorFlow build actually lists usable GPU devices.
- Larger `F`, `T`, `n_channels`, `batch_size`, and source count increase memory use.
- The default U-Net is sizable; lowering `train_max_steps` is the main smoke-test limiter, not a production recipe.
- Evaluation during `train_and_evaluate` can make a run appear idle while validation input is being built or caches are being populated.
