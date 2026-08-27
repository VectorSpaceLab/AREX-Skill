# Audio Configuration Reference

This reference distills NeMo Speech audio Hydra, manifest, Lhotse, model-family, training, processing, evaluation, and output configuration patterns. Evidence was distilled from `docs/source/audio/configs.rst`, `docs/source/audio/datasets.rst`, `examples/audio/conf/*.yaml`, `examples/audio/*.py`, audio model/data source, and audio tests.

## Hydra Override Rules

NeMo audio examples use Hydra/OmegaConf. Typical override rules:

- Override existing fields with `section.key=value`.
- Add new fields with `+field=value` or `++field=value` when the key is not already in the structured config.
- Use YAML values: `null`, `true`, `false`, lists such as `[0,1]`, and quoted strings for paths with shell-sensitive characters.
- Quote list overrides when the shell might expand brackets: `'model.train_ds.input_channel_selector=[0,1]'`.
- Use `--config-path` and `--config-name` for training configs. `--config-name` omits the `.yaml` suffix.
- Inspect the resolved logged Hydra config before a long run.

Common mistakes:

- Passing neither `model_path` nor `pretrained_name` to processing/evaluation.
- Passing both or neither `audio_dir` and `dataset_manifest` to processing.
- Passing `audio_dir` to evaluation; evaluation requires a manifest with target audio.
- Forgetting `+` or `++` when adding `init_from_nemo_model`, `init_from_pretrained_model`, `sampler.*`, `input_cuts`, or `output_cuts` fields.
- Leaving `output_dir` defaulted when a safe explicit destination is required.
- Overriding `input_key` or `target_key` in train but not validation/test.

## NeMo Audio Manifest Format

Paired training/evaluation format:

```json
{"input_filepath":"noisy.wav","target_filepath":"clean.wav","duration":3.147}
```

Common key variants:

| Key | Typical use |
| --- | --- |
| `audio_filepath` | Masking/beamforming input audio in some configs. |
| `target_filepath` | Masking/beamforming target audio. |
| `target_anechoic_filepath` | Flex-channel beamforming target. |
| `noisy_filepath` | Predictive/generative/BNR noisy input. |
| `clean_filepath` | Predictive/generative clean target. |
| `speech_filepath` | Maxine BNR speech target in its config. |
| `input_filepath` | Generic audio-to-audio input and conversion default. |
| `target_filepath` | Generic audio-to-audio target and conversion default. |
| `reference_filepath` | Optional reference signal for reference-aware datasets. |
| `embedding_filepath` | Optional `.npy` embedding vector for embedding-aware datasets. |
| `processed_audio_filepath` | Output key written by processing and read by evaluation. |

Manifest rules:

- One JSON object per line; no blank lines for NeMo manifests.
- Audio paths can be absolute or relative to the manifest directory.
- Audio path values can be strings or lists of strings. Lists are used to build multi-channel signals from multiple files.
- `duration` should be positive and numeric. It is used for filtering and fixed-duration sampling.
- `offset` is used by Lhotse conversion when present.
- Channel selector fields can appear in configs and, for conversion, in manifests: `input_channel_selector`, `target_channel_selector`, and `reference_channel_selector`.
- For inference-only processing, `target_key` may be absent or `null`; for training/evaluation it should be present.

Preflight examples:

```bash
python scripts/check_audio_manifest.py train.jsonl \
  --input-key noisy_filepath \
  --target-key clean_filepath \
  --require-target \
  --check-files
```

```bash
python scripts/check_audio_manifest.py infer.jsonl \
  --input-key audio_filepath \
  --output-dir enhanced_audio \
  --output-manifest enhanced_manifest.json
```

## Dataset Config: NeMo Format

Base train/validation/test shape:

```yaml
model:
  sample_rate: 16000
  skip_nan_grad: false
  train_ds:
    manifest_filepath: train.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    audio_duration: 4.0
    random_offset: true
    min_duration: ${model.train_ds.audio_duration}
    batch_size: 8
    shuffle: true
    num_workers: 8
    pin_memory: true
  validation_ds:
    manifest_filepath: val.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    batch_size: 8
    shuffle: false
    num_workers: 4
    pin_memory: true
  test_ds:
    manifest_filepath: test.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    batch_size: 1
    shuffle: false
    num_workers: 4
    pin_memory: true
```

Key dataset fields:

| Field | Meaning |
| --- | --- |
| `manifest_filepath` | NeMo JSONL manifest path. |
| `sample_rate` | Inherited from `model.sample_rate` when injected by model setup. |
| `input_key` | Manifest key for input audio. |
| `target_key` | Manifest key for target audio; `null` only for inference/self-supervised cases. |
| `audio_duration` | Fixed crop length in seconds for training. |
| `random_offset` | Randomize crop start when the file is longer than `audio_duration`. |
| `min_duration` / `max_duration` | Filter examples by duration. |
| `max_utts` | Limit loaded utterances. |
| `input_channel_selector` | Select input channels, or `null` for all. |
| `target_channel_selector` | Select target channels, often `0` for single target from a multi-channel file. |
| `normalization_signal` | Normalize all loaded signals by `input_signal`, `target_signal`, or another supported signal. |
| `batch_size` | Static examples per batch. |
| `shuffle` | Should be true for train and false for validation/test. |
| `pin_memory` | Useful for GPU training/inference. |

Reference-aware and embedding-aware datasets add `reference_key`, `reference_channel_selector`, `reference_is_synchronized`, `reference_duration`, and `embedding_key`. Use these only when the model/config expects reference or embedding signals.

## Lhotse CutSet and Shar Config

CutSet shape:

```yaml
model:
  train_ds:
    use_lhotse: true
    cuts_path: train_cuts.jsonl
    truncate_duration: 4.0
    truncate_offset_type: random
    batch_size: 64
    shuffle: true
    num_workers: 8
    pin_memory: true
trainer:
  use_distributed_sampler: false
```

CutSet with online augmentation:

```yaml
model:
  train_ds:
    use_lhotse: true
    cuts_path: clean_speech_cuts.jsonl
    truncate_duration: 4.0
    truncate_offset_type: random
    batch_size: 64
    shuffle: true
    rir_enabled: true
    rir_path: rir_recordings.jsonl
    noise_path: noise_cuts.jsonl
trainer:
  use_distributed_sampler: false
```

Shar shape:

```yaml
model:
  train_ds:
    use_lhotse: true
    shar_path: train_shar
    truncate_duration: 4.0
    truncate_offset_type: random
    batch_size: 8
    shuffle: true
    num_workers: 8
    pin_memory: true
trainer:
  use_distributed_sampler: false
```

Lhotse audio field contract:

- The main Cut recording is the input signal.
- Custom `target_recording` is the target signal.
- Custom `reference_recording` is the reference signal.
- Custom `embedding_vector` is the embedding field.
- For online augmentation examples, the clean speech input CutSet also includes `target_recording` with the same signal.
- Lhotse dataloaders own distributed sampling, so set `trainer.use_distributed_sampler=false`.

## Nested Lhotse Input Config and Reweighting

Audio docs describe nested `input_cfg` groups with temperature-based sampling weights.

Scalar temperature:

```yaml
model:
  train_ds:
    use_lhotse: true
    reweight_temperature: 0.5
    input_cfg:
      - type: group
        input_cfg:
          - type: lhotse_shar
            shar_path: dataset_large
            weight: 900
          - type: lhotse_shar
            shar_path: dataset_small
            weight: 100
      - type: nemo_tarred
        manifest_filepath: extra_manifest.json
        tarred_audio_filepath: extra_audio.tar
        weight: 300
```

List temperature by nesting depth:

```yaml
model:
  train_ds:
    use_lhotse: true
    reweight_temperature: [1.0, 0.0]
    input_cfg:
      - type: group
        weight: 0.7
        input_cfg:
          - type: lhotse_shar
            shar_path: task_a_large
            weight: 600
          - type: lhotse_shar
            shar_path: task_a_small
            weight: 400
      - type: group
        weight: 0.3
        input_cfg:
          - type: lhotse_shar
            shar_path: task_b
            weight: 100
```

Temperature rules:

- `temperature=1.0` preserves original weight ratios.
- `temperature=0.0` equalizes datasets at that nesting level.
- `0 < temperature < 1.0` over-samples smaller datasets relative to larger ones.
- `temperature > 1.0` amplifies differences.
- If `reweight_temperature` is a list, its length must match the maximum nesting depth of `input_cfg`, otherwise a `ValueError` is raised.
- If `input_cfg` points to external YAML files, paths with OmegaConf environment interpolation count as one additional unresolved nesting level during depth counting.

## Model Architecture Config

A predictive model skeleton:

```yaml
model:
  type: predictive
  sample_rate: 16000
  skip_nan_grad: false
  num_outputs: 1
  normalize_input: true
  train_ds:
    manifest_filepath: train.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    audio_duration: 2.0
    random_offset: true
    normalization_signal: input_signal
    batch_size: 8
    shuffle: true
  validation_ds:
    manifest_filepath: val.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    batch_size: 8
    shuffle: false
  encoder:
    _target_: nemo.collections.audio.modules.transforms.AudioToSpectrogram
    fft_length: 510
    hop_length: 128
    magnitude_power: 0.5
    scale: 0.33
  decoder:
    _target_: nemo.collections.audio.modules.transforms.SpectrogramToAudio
    fft_length: ${model.encoder.fft_length}
    hop_length: ${model.encoder.hop_length}
    magnitude_power: ${model.encoder.magnitude_power}
    scale: ${model.encoder.scale}
  estimator:
    _target_: nemo.collections.audio.parts.submodules.ncsnpp.SpectrogramNoiseConditionalScoreNetworkPlusPlus
    in_channels: 1
    out_channels: 1
  loss:
    _target_: nemo.collections.audio.losses.MSELoss
  metrics:
    val:
      sisdr:
        _target_: torchmetrics.audio.ScaleInvariantSignalDistortionRatio
  optim:
    name: adam
    lr: 1e-4
trainer:
  devices: 1
  accelerator: gpu
```

Shared model fields:

| Field | Meaning |
| --- | --- |
| `type` | Selects model class in the training script. |
| `sample_rate` | Runtime sample rate for loading and writing audio. |
| `skip_nan_grad` | Zero invalid gradients when NaN/Inf appears. |
| `num_outputs` | Number of outputs/masks where architecture uses it. |
| `normalize_input` | Peak-normalize input and denormalize output in predictive/generative models. |
| `max_utts_evaluation_metrics` | Limits expensive inference-based metrics on validation/test. |
| `encoder` / `decoder` | Analysis/synthesis transform configs. |
| `estimator` | Neural estimator/backbone config. |
| `loss`, `loss_encoded`, `loss_time` | Training loss config depending on family. |
| `metrics.val`, `metrics.test` | Torchmetrics or audio metric configs. |
| `optim` | NeMo/PyTorch optimizer config. |

## Family-Specific Config Notes

Mask-based and beamforming:

- `type` may be omitted; the training script defaults to `mask_based`.
- Common input/target keys are `audio_filepath` and `target_filepath`.
- Flex-channel beamforming uses `input_channel_selector: null` to load all channels and `target_channel_selector: 0` to choose supervision.
- Mask estimator choices include RNN, FlexChannels, or GSS; mask processor may be a simple mask or multichannel Wiener filter.

Predictive:

- Use `type: predictive`.
- Common keys are `noisy_filepath` and `clean_filepath`.
- `normalize_input: true` is common for non-streaming predictive configs; streaming predictive configs may set it false.
- Estimators include NCSN++, Conformer, TransformerUNet, and ConformerUNet variants.

Score-based generative:

- Use `type: score_based`.
- Requires `sde` and `sampler` configs at the model level.
- Do not place `sde` or `score_estimator` inside the sampler config; model code rejects that.
- Use `max_utts_evaluation_metrics` to bound validation inference cost.
- `validation_ds.normalize_input` may be false while the model itself normalizes for inference.

Schrödinger Bridge:

- Use `type: schroedinger_bridge`.
- Requires `noise_schedule`, `sampler`, and `estimator_output`.
- Configure either a single `loss` or a split `loss_encoded` and `loss_time`, not both.
- Use `max_utts_evaluation_metrics` to bound expensive metrics.

Flow matching:

- Use `type: flow_matching`.
- Requires `flow` and `sampler` configs.
- `estimator_target` defaults to `conditional_vector_field`; set intentionally when using `data`.
- `p_cond` controls conditional dropout.
- `ssl_pretrain_masking` enables SSL-style masking; target can be omitted for self-reconstruction in the flow model parser.
- `flow_matching_generative_ssl_pretraining.yaml` uses Lhotse Shar for training and a clean manifest for validation.

Maxine BNR:

- Use `type: bnr`.
- `sample_rate` must be 16000.
- Input must be single-channel; use `input_channel_selector` or preprocessed mono audio if source files are multi-channel.
- Common manifest keys are `noisy_filepath` and `speech_filepath`.
- Training config may include `model.train.enable_weight_norm`.

## Processing Config

`process_audio.py` dataclass fields:

```yaml
model_path: null
pretrained_name: null
audio_dir: null
dataset_manifest: null
max_utts: null
input_channel_selector: null
input_key: null
output_dir: null
output_filename: null
batch_size: 1
num_workers: 0
override_config_path: null
sampler: {}
cuda: null
amp: false
audio_type: wav
overwrite_output: false
```

Rules:

- Set one model source: `model_path` or `pretrained_name`.
- Set one data source: `audio_dir` or `dataset_manifest`.
- `input_key` defaults to `audio_filepath` for manifest processing.
- `cuda=null` means use CUDA device 0 if available, otherwise CPU. A negative `cuda` value forces CPU. A non-negative integer selects that CUDA device.
- `amp=true` enables CUDA AMP only when CUDA and `torch.cuda.amp.autocast` are available.
- `sampler` overrides require the loaded model to have a `sampler` attribute and the named sampler fields to exist.
- If `output_dir` is omitted, the script creates a default processed directory based on input source and model name.
- If `output_filename` is omitted, it is derived from `output_dir`.
- If `output_dir` exists and `overwrite_output=false`, the script raises to prevent accidental overwrite.

Safe output guidance:

- Prefer explicit `output_dir` and `output_filename` chosen by the user.
- Avoid putting outputs inside the input audio tree unless mirroring is intentional.
- Do not set `overwrite_output=true` until the user confirms replacement is safe.
- Preflight with the bundled checker using `--output-dir` and `--output-manifest`.

## Evaluation Config

`audio_to_audio_eval.py` extends processing config with:

```yaml
processed_channel_selector: null
processed_key: processed_audio_filepath
target_dataset_dir: null
target_channel_selector: null
target_key: target_audio_filepath
sample_rate: 16000
only_score_manifest: false
metrics: [sdr, estoi]
return_values_per_example: false
```

Rules:

- `dataset_manifest` is mandatory.
- `audio_dir` is not allowed for evaluation.
- `target_key` defaults to `target_audio_filepath`, but many audio configs use `target_filepath`, `clean_filepath`, or `speech_filepath`; override it explicitly.
- `processed_key` defaults to `processed_audio_filepath` for manifests produced by processing.
- `only_score_manifest=true` skips processing and assumes `dataset_manifest` already has processed and target paths.
- `return_values_per_example=true` requires `batch_size=1`.
- `metrics` must be a subset of `sdr`, `sisdr`, `stoi`, `estoi`, `pesq`, `squim_mos`, `squim_stoi`, `squim_pesq`, `squim_si_sdr`.
- `sample_rate` is used by STOI/PESQ/SQUIM metrics and the temporary scoring dataloader.

## Augmentation-Saving Config

Materializing Lhotse online augmentation uses a normal audio model config plus caller-owned fields that identify input and output CutSets:

```yaml
input_cuts: cuts.jsonl
output_cuts: augmented/cuts.augmented.jsonl
keep_directory_structure: true
num_samples: 100
model:
  sample_rate: 48000
  train_ds:
    use_lhotse: true
    cuts_path: ${input_cuts}
    batch_size: 1
    shuffle: false
    rir_enabled: true
    rir_path: rir_recordings.jsonl
```

Rules:

- `input_cuts` and `output_cuts` are required caller-owned fields for the materialization workflow.
- `input_cuts` must be a `.jsonl` CutSet of `MonoCut` objects with relative recording source paths that exist relative to the CutSet file.
- `output_cuts` parent directory should be intentionally selected and should not overwrite existing valuable artifacts.
- `num_samples` optionally limits saved examples.
- `keep_directory_structure=true` preserves input relative directories; otherwise output audio can go under an `audio/` subdirectory.
- Force deterministic order by disabling shuffle, setting batch size 1, disabling bucketing, and resetting dataloader filters when a one-to-one input/output mapping is required.

## Trainer and Experiment Config

Common trainer fields:

```yaml
trainer:
  devices: 1
  accelerator: gpu
  max_epochs: 50
  precision: 32
  log_every_n_steps: 10
  val_check_interval: 1.0
```

Guidance:

- Use `accelerator=gpu` and an appropriate device count for real training.
- Use `accelerator=cpu` only for tiny smoke checks; CPU training is impractical for real audio models.
- For Lhotse, set `trainer.use_distributed_sampler=false`.
- For Shar/infinite-style dataloading, bound training with max steps or limit batches.
- Keep `exp_manager` output paths under user-approved experiment directories.
- If post-fit test is configured by `model.test_ds`, the training script destroys an existing distributed process group and runs test on one device.

## Configuration Review Checklist

Before launch:

- Manifest keys in YAML match actual JSONL keys.
- `duration` exists and passes numeric/positive validation.
- Input/target/reference channel selectors match the expected channel counts.
- `model.sample_rate` matches the checkpoint/model family and data assumptions.
- For BNR, audio is 16 kHz and single-channel.
- For Lhotse, targets are `target_recording` custom fields and `trainer.use_distributed_sampler=false`.
- For generative models, sampler settings and `max_utts_evaluation_metrics` are intentionally bounded.
- Output paths are explicit and safe.
- `init_from_nemo_model` or `init_from_pretrained_model` is compatible with the architecture config.
- Optional dependencies are installed only when the selected workflow needs them.
