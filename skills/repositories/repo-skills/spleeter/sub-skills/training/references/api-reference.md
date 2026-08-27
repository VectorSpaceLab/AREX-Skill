# Training API Reference

Use these APIs when a task needs programmatic training data construction, custom input functions, or estimator adaptation. Prefer the CLI for ordinary training; use APIs only when the user needs to inspect or customize the TensorFlow data path.

## Config loading

```python
from spleeter.utils.configuration import load_configuration

params = load_configuration("path/to/config.json")
# or an embedded descriptor such as "spleeter:2stems"
```

For custom training, a filesystem JSON config is safer than an embedded descriptor because training CSVs, `model_dir`, caches, and segment counts must be explicit and writable.

## Audio adapter

```python
from spleeter.audio.adapter import AudioAdapter

audio_adapter = AudioAdapter.get(
    "spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter"
)
```

The default adapter uses system `ffmpeg` and `ffprobe`. It loads paths joined under the `audio_path` passed to `DatasetBuilder`.

## Dataset helper signatures

```python
from spleeter.dataset import get_training_dataset, get_validation_dataset

get_training_dataset(audio_params: dict, audio_adapter, audio_path: str) -> object
get_validation_dataset(audio_params: dict, audio_adapter, audio_path: str) -> object
```

Behavior distilled from the source:

- `get_training_dataset` builds `DatasetBuilder(audio_params, audio_adapter, audio_path, chunk_duration=audio_params.get("chunk_duration", 20.0), random_seed=audio_params.get("random_seed", 0))` and then calls `build(...)` with:
  - `csv_path=str(audio_params.get("train_csv"))`
  - `cache_directory=audio_params.get("training_cache")`
  - `batch_size=audio_params.get("batch_size", 8)`
  - `n_chunks_per_song=audio_params.get("n_chunks_per_song", 2)`
  - `random_data_augmentation=False`
  - `convert_to_uint=True`
  - `wait_for_cache=False`
- `get_validation_dataset` uses a fixed validation `chunk_duration=12.0` and calls `build(...)` with:
  - `csv_path=str(audio_params.get("validation_csv"))`
  - `cache_directory=audio_params.get("validation_cache")`
  - `batch_size=audio_params.get("batch_size", 8)`
  - `infinite_generator=False`
  - `n_chunks_per_song=1`
  - `random_time_crop=False`
  - `shuffle=False`
  - `random_data_augmentation=False`

Safe usage:

```python
from spleeter.audio.adapter import AudioAdapter
from spleeter.dataset import get_training_dataset, get_validation_dataset
from spleeter.utils.configuration import load_configuration

params = load_configuration("config.json")
audio_adapter = AudioAdapter.get("spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter")
train_ds = get_training_dataset(params, audio_adapter, "DATA_ROOT")
valid_ds = get_validation_dataset(params, audio_adapter, "DATA_ROOT")
```

Validate `params`, CSV columns, and file paths before creating these datasets; missing columns or bad files can surface later as TensorFlow graph/data errors.

## `DatasetBuilder`

Constructor:

```python
DatasetBuilder(
    audio_params: dict,
    audio_adapter,
    audio_path: str,
    random_seed: int = 0,
    chunk_duration: float = 20.0,
)
```

Build method:

```python
DatasetBuilder.build(
    csv_path: str,
    batch_size: int = 8,
    shuffle: bool = True,
    convert_to_uint: bool = True,
    random_data_augmentation: bool = False,
    random_time_crop: bool = True,
    infinite_generator: bool = True,
    cache_directory: str | None = None,
    wait_for_cache: bool = False,
    num_parallel_calls: int = 4,
    n_chunks_per_song: int = 2,
)
```

Important construction details:

- `audio_params` must include `T`, `F`, `sample_rate`, `frame_length`, `frame_step`, `mix_name`, `n_channels`, and `instrument_list`.
- The builder's instrument set is `[mix_name] + instrument_list`; each member needs a CSV column named `<name>_path`.
- `check_parameters_compatibility()` runs during construction and raises when:
  - `F > frame_length / 2 + 1`
  - the selected `chunk_duration`, `sample_rate`, `frame_length`, and `frame_step` cannot provide at least `T` frames.
- `compute_segments()` raises when `n_chunks_per_song <= 0`.
- `cache_directory` is a TensorFlow dataset cache prefix. When `wait_for_cache=True`, the builder waits for `<cache_directory>.index` before proceeding; CLI training does not expose this wait flag.
- The dataset output is a `(features, labels)` pair:
  - features: `{f"{mix_name}_spectrogram": ...}`
  - labels: `{f"{instrument}_spectrogram": ... for instrument in instrument_list}`

Custom builder example:

```python
from spleeter.audio.adapter import AudioAdapter
from spleeter.dataset import DatasetBuilder

params = {...}  # validated Spleeter-style training config
audio_adapter = AudioAdapter.get("spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter")
builder = DatasetBuilder(
    params,
    audio_adapter,
    "DATA_ROOT",
    random_seed=params.get("random_seed", 0),
    chunk_duration=params.get("chunk_duration", 20.0),
)
dataset = builder.build(
    params["train_csv"],
    batch_size=params.get("batch_size", 8),
    cache_directory=params.get("training_cache"),
    n_chunks_per_song=params.get("n_chunks_per_song", 2),
)
```

## Model function and estimator

CLI training builds:

```python
import tensorflow as tf
from functools import partial
from spleeter.dataset import get_training_dataset, get_validation_dataset
from spleeter.model import model_fn

estimator = tf.estimator.Estimator(
    model_fn=model_fn,
    model_dir=params["model_dir"],
    params=params,
    config=tf.estimator.RunConfig(
        save_checkpoints_steps=params["save_checkpoints_steps"],
        tf_random_seed=params["random_seed"],
        save_summary_steps=params["save_summary_steps"],
        log_step_count_steps=10,
        keep_checkpoint_max=2,
    ),
)
train_spec = tf.estimator.TrainSpec(
    input_fn=partial(get_training_dataset, params, audio_adapter, "DATA_ROOT"),
    max_steps=params["train_max_steps"],
)
eval_spec = tf.estimator.EvalSpec(
    input_fn=partial(get_validation_dataset, params, audio_adapter, "DATA_ROOT"),
    steps=None,
    throttle_secs=params["throttle_secs"],
)
tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
```

`model_fn(features, labels, mode, params)` delegates to `EstimatorSpecBuilder`:

- `PREDICT`: waveform-in/waveform-out separation graph.
- `EVAL`: spectrogram input and source spectrogram labels; returns loss and per-source metrics.
- `TRAIN`: spectrogram input and source spectrogram labels; returns training op and metrics.

For training, `features` must include `{mix_name}_spectrogram`; `labels` must include one `<instrument>_spectrogram` key for each instrument. The provided dataset helpers produce that shape.

## Model function descriptors

`model.type` is resolved relative to Spleeter's model-functions package:

```python
"model": {
  "type": "unet.unet",
  "params": {"conv_activation": "ELU", "deconv_activation": "ELU"}
}
```

Evidence-backed descriptors include `unet.unet` and `unet.softmax_unet`. An invalid descriptor raises when the estimator graph tries to import or call the model function. See [data format and config](data-format-and-config.md) for caveats.

## Safety checklist before API use

- Run [validate_training_config.py](../scripts/validate_training_config.py) or equivalent checks before constructing datasets.
- Avoid relying on embedded pretrained descriptors as-is for training.
- Keep `n_chunks_per_song` positive and concrete.
- Use small `batch_size`, `T`, and `F` for smoke; use production dimensions only when resources are available.
- Keep custom cache prefixes separate for materially different configs.
- Do not treat optional GPU logs as proof of GPU training; inspect TensorFlow devices in the user's runtime if GPU acceleration matters.
