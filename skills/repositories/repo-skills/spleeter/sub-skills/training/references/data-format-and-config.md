# Data Format and Training Config

Spleeter training is controlled by a JSON config plus CSV manifests. The config defines the source set, audio/STFT dimensions, caches, model function, and estimator limits. The CSVs point to audio files under `--data DATA_ROOT`.

## Directory layout examples

Two-stem layout:

```text
DATA_ROOT/
  train/
    song001/
      mix.wav
      vocals.wav
      accompaniment.wav
    train.csv
  validation/
    song101/
      mix.wav
      vocals.wav
      accompaniment.wav
    validation.csv
```

Four-stem layout:

```text
DATA_ROOT/
  train/
    song001/
      mix.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
    train.csv
  validation/
    song101/
      mix.wav
      vocals.wav
      drums.wav
      bass.wav
      other.wav
    validation.csv
```

The audio file layout can differ, but each CSV audio path should be a relative path under `DATA_ROOT`.

## CSV schema

Required columns derive from `mix_name` and `instrument_list`.

| Column | Required | Meaning |
| --- | --- | --- |
| `{mix_name}_path` | yes | Mix audio path relative to `--data`. With the default `mix_name: "mix"`, this is `mix_path`. |
| `<instrument>_path` | yes for every instrument | Ground-truth source audio path relative to `--data`. Examples: `vocals_path`, `accompaniment_path`, `drums_path`, `bass_path`, `other_path`. |
| `duration` | yes | Positive song or excerpt duration in seconds. Spleeter uses it to choose segment start offsets. |

Two-stem CSV header with default mix name:

```csv
mix_path,vocals_path,accompaniment_path,duration
train/song001/mix.wav,train/song001/vocals.wav,train/song001/accompaniment.wav,180.0
```

Four-stem CSV header:

```csv
mix_path,vocals_path,drums_path,bass_path,other_path,duration
train/song001/mix.wav,train/song001/vocals.wav,train/song001/drums.wav,train/song001/bass.wav,train/song001/other.wav,180.0
```

Rules:

- Keep row paths relative, not absolute. `DatasetBuilder.expand_path` joins each row value under `--data`.
- Keep every referenced audio file readable by the selected adapter.
- Source files should have compatible duration, sample rate after adapter loading, and channel count for `n_channels`.
- Extra columns are ignored by Spleeter's dataset loader, but missing required columns fail when the TensorFlow dataset is built.

## Config path caveat

`params_filename` can be an embedded descriptor such as `spleeter:2stems` or a filesystem JSON path. For custom training, prefer a filesystem JSON file.

Spleeter reads `train_csv` and `validation_csv` exactly as strings from the config. They are not automatically resolved relative to `--data` or relative to the config file. Use one of these safe patterns:

- Put the config in `DATA_ROOT`, store `train_csv: "train/train.csv"`, and run `python -m spleeter train -d . -p config.json` from `DATA_ROOT`.
- Store absolute CSV paths in the config for a non-portable but unambiguous local run.
- Store CSV paths relative to the process working directory and always launch training from that directory.

The CSV row audio paths are different: those should remain relative to `--data`.

## Core config fields

Fields used directly by CLI training and dataset/model construction:

| Field | Required for real training | Notes |
| --- | --- | --- |
| `train_csv` | yes | CSV path for `get_training_dataset`. See path caveat above. |
| `validation_csv` | yes | CSV path for `get_validation_dataset`. |
| `model_dir` | yes | TensorFlow estimator output/checkpoint directory. |
| `mix_name` | yes | Usually `"mix"`; determines the mix CSV column and feature key. |
| `instrument_list` | yes | Non-empty list of target sources. Each instrument needs `<instrument>_path` in CSVs. |
| `sample_rate` | yes | Adapter target sample rate. Spleeter examples use 44100. |
| `frame_length` | yes | STFT frame length. |
| `frame_step` | yes | STFT hop length. |
| `T` | yes | Spectrogram time dimension used by the model. |
| `F` | yes | Number of frequency bins retained. Must fit `frame_length`. |
| `n_channels` | yes | Usually 1 or 2; must match training intent. |
| `chunk_duration` | recommended | Training chunk length in seconds. If absent, `get_training_dataset` uses 20.0. Do not set it to `null`. |
| `n_chunks_per_song` | recommended/validated | Training segment count per row. If present, it must be positive. Use 1 for central segment smoke runs. |
| `batch_size` | recommended | Defaults to 8 in dataset helpers, but make it explicit for reproducible resource use. |
| `training_cache` | optional | TensorFlow dataset cache prefix for training preprocessing. |
| `validation_cache` | optional | TensorFlow dataset cache prefix for validation preprocessing. |
| `train_max_steps` | yes | Max estimator training steps. Use a tiny value only for smoke. |
| `throttle_secs` | yes | Minimum seconds between estimator evaluations. |
| `random_seed` | yes | Used for estimator and dataset randomness. |
| `save_checkpoints_steps` | yes | Estimator checkpoint interval. |
| `save_summary_steps` | yes | Estimator summary interval. |
| `separation_exponent` | yes | Used by model masks. Common value: 2. |
| `mask_extension` | yes | `"zeros"` or `"average"`; invalid values raise during model output construction. |
| `learning_rate` | yes | Used by the default Adam optimizer unless another optimizer is configured. |
| `model.type` | yes | Model function descriptor under `spleeter.model.functions`, such as `unet.unet` or `unet.softmax_unet`. |
| `model.params` | yes | Parameters forwarded to the model function. U-Net examples set activation names here. |

Minimal smoke-style two-stem config shape:

```json
{
  "train_csv": "train/train.csv",
  "validation_csv": "validation/validation.csv",
  "model_dir": "model",
  "mix_name": "mix",
  "instrument_list": ["vocals", "accompaniment"],
  "sample_rate": 8000,
  "frame_length": 1024,
  "frame_step": 256,
  "T": 64,
  "F": 128,
  "n_channels": 2,
  "chunk_duration": 3.0,
  "n_chunks_per_song": 1,
  "separation_exponent": 2,
  "mask_extension": "zeros",
  "learning_rate": 0.0001,
  "batch_size": 1,
  "training_cache": "cache/training",
  "validation_cache": "cache/validation",
  "train_max_steps": 1,
  "throttle_secs": 20,
  "save_checkpoints_steps": 10,
  "save_summary_steps": 5,
  "random_seed": 0,
  "model": {
    "type": "unet.unet",
    "params": {"conv_activation": "ELU", "deconv_activation": "ELU"}
  }
}
```

Use production dimensions and sample rate for real models; the tiny values above are for wiring checks only.

## Embedded descriptor caveats

Embedded descriptors such as `spleeter:2stems`, `spleeter:4stems`, and `spleeter:5stems` are primarily pretrained-model descriptors. They are useful templates, but they are not ready-to-run custom training configs:

- Some descriptor CSV fields are placeholders such as `path/to/train.csv`.
- Some `chunk_duration` or `n_chunks_per_song` values may be `null`; actual training needs concrete compatible values or defaults that do not resolve to `null`.
- `model_dir` names such as `2stems` or `4stems` may collide with existing pretrained-model caches or user directories.
- For custom training, copy the structure into a new JSON file and validate it.

For descriptor loading and model-cache behavior, see [models and configuration](../../../references/models-and-configuration.md).

## Model function notes

Spleeter resolves `model.type` through `spleeter.model.get_model_function`. A value like `unet.unet` imports `spleeter.model.functions.unet` and selects the `unet` function. Evidence-backed model function values include:

- `unet.unet`: independent U-Net mask output per instrument.
- `unet.softmax_unet`: softmax mask over instruments; used by five-stem resources.

U-Net `model.params` commonly include:

- `conv_activation`: `"ELU"`, `"ReLU"`, or default LeakyReLU behavior.
- `deconv_activation`: `"ELU"`, `"LeakyReLU"`, or default ReLU behavior.
- `conv_n_filters`: optional list of convolution filter counts; larger lists increase memory and compute.

Custom model functions must be importable under Spleeter's model-functions package layout, not arbitrary external dotted paths.

## Validation rules from `DatasetBuilder`

Run [validate_training_config.py](../scripts/validate_training_config.py) before training. The key source-derived rules are:

1. Frequency bins:

   ```text
   F <= frame_length / 2 + 1
   ```

   If this fails, decrease `F` or increase `frame_length`.

2. Time frames for training chunks:

   ```text
   (chunk_duration * sample_rate - frame_length) / frame_step >= T
   ```

   If this fails, decrease `T`, decrease `frame_step`, decrease `frame_length`, increase `chunk_duration`, or use longer audio.

3. Segment count:

   ```text
   n_chunks_per_song > 0
   ```

   Use `1` for deterministic central-segment smoke data; use a larger value for real multi-segment training.

4. CSV columns:

   ```text
   {mix_name}_path + every <instrument>_path + duration
   ```

   Missing source columns fail based on the `instrument_list`; for example, a two-stem config with `instrument_list: ["vocals", "accompaniment"]` requires `accompaniment_path`.

5. File and duration sanity:

   - Every row path must stay under `--data` and point to an existing file.
   - `duration` must be positive.
   - Rows shorter than the minimum seconds implied by `T`, `sample_rate`, `frame_length`, and `frame_step` are not valid training examples.
