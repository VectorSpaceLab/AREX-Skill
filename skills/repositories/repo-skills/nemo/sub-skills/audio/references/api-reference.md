# Audio API Reference

This reference summarizes NeMo Speech audio APIs most often needed by coding agents. Evidence was distilled from `docs/source/audio/api.rst`, `nemo/collections/audio/models/audio_to_audio.py`, `nemo/collections/audio/models/enhancement.py`, `nemo/collections/audio/models/maxine/bnr.py`, `nemo/collections/audio/data/audio_to_audio.py`, `nemo/collections/audio/data/audio_to_audio_dataset.py`, `nemo/collections/audio/data/audio_to_audio_lhotse.py`, audio modules/losses/metrics source, and audio tests.

## Import Roots

```python
from nemo.collections.audio.models import AudioToAudioModel
from nemo.collections.audio.models.enhancement import EncMaskDecAudioToAudioModel
from nemo.collections.audio.models.enhancement import PredictiveAudioToAudioModel
from nemo.collections.audio.models.enhancement import ScoreBasedGenerativeAudioToAudioModel
from nemo.collections.audio.models.enhancement import SchroedingerBridgeAudioToAudioModel
from nemo.collections.audio.models.enhancement import FlowMatchingAudioToAudioModel
from nemo.collections.audio.models.maxine import BNR2
```

Installed facts captured during generation:

- Distribution: `nemo-toolkit` version `3.1.0+8f85359`.
- Import root `nemo` was verified from an editable source-backed inspection environment.
- Package metadata declares Python `>=3.10`, while current NeMo Speech docs recommend Python 3.12+, PyTorch 2.7+, and GPU/CUDA for training.
- Optional broad extras, compiled extensions, CUDA extras, dev, and docs groups were not installed during skill generation; optional-heavy workflows should document prerequisites rather than assume them.

## Model Loading API

Generic loading:

```python
from nemo.collections.audio.models import AudioToAudioModel

model = AudioToAudioModel.restore_from("checkpoint.nemo")
model = AudioToAudioModel.from_pretrained("pretrained-audio-model-name")
```

Unknown concrete class recovery:

```python
from nemo.collections.audio.models import AudioToAudioModel
from nemo.utils import model_utils

model_cfg = AudioToAudioModel.restore_from("checkpoint.nemo", return_config=True)
model_class = model_utils.import_class_by_path(model_cfg.target)
model = model_class.restore_from("checkpoint.nemo")
```

Notes:

- Use `restore_from()` for a local `.nemo` file.
- Use `from_pretrained()` only when a registry/cache-backed pretrained name is acceptable; it may require network access or a populated model cache.
- Use a concrete subclass only when creating a model from a config or using subclass-specific behavior.
- `AudioToAudioModel.list_available_models()` delegates to subclass pretrained metadata resolution, but some audio subclasses return an empty list or `None`; do not assume every family exposes public pretrained names.

## Base `AudioToAudioModel`

Core behavior:

- Inherits from `ModelPT` and expects an OmegaConf-style model config.
- Stores `sample_rate` from `cfg.sample_rate`.
- Initializes `loss` from `cfg.loss` when present.
- Supports training, validation, and test dataloaders from config.
- Handles tuple-style NeMo audio batches and dict-style Lhotse batches.
- Normalizes batch signals to `(B, C, T)` for model computation.
- Supports `skip_nan_grad` to zero invalid gradients across distributed ranks.
- Can add audio/spectrogram logging callbacks when `log_config` is present.

Important methods:

| Method | Use |
| --- | --- |
| `setup_training_data(config)` | Build train dataloader; defaults `shuffle=true`. |
| `setup_validation_data(config)` | Build validation dataloader; defaults `shuffle=false`. |
| `setup_test_data(config)` | Build test dataloader; defaults `shuffle=false`. |
| `_setup_dataloader_from_config(config)` | Chooses Lhotse or NeMo-format dataset based on `use_lhotse`. |
| `_parse_batch(batch)` | Converts dict or tuple batches to `input_signal`, `target_signal`, `input_length`. |
| `process(paths2audio_files, output_dir, ...)` | Batch inference that writes processed audio files and returns output paths. |
| `match_batch_length(input, batch_length)` | Pads/crops model output to match input length. |
| `_normalize()` / `_denormalize()` | Peak-normalize input and restore scale. |

Dataloader constraints:

- Lhotse is selected by `config.use_lhotse=true` and uses `LhotseAudioToTargetDataset`.
- Non-Lhotse concat is not implemented in audio base dataloading.
- Non-Lhotse tarred audio datasets are not supported by the audio base dataloader.
- If `manifest_filepath` is explicitly `None`, the dataloader setup returns `None` with a warning.

## Processing API

`AudioToAudioModel.process()` signature:

```python
processed_paths = model.process(
    paths2audio_files=["a.wav", "b.wav"],
    output_dir="processed",
    batch_size=1,
    num_workers=None,
    input_channel_selector=None,
    input_dir=None,
)
```

Contract:

- `paths2audio_files` is a list of audio paths; empty input returns an empty mapping-like result.
- A temporary NeMo manifest is built with `input_filepath` and `duration` for each file.
- `input_channel_selector` selects or averages channels according to the channel selector accepted by the ASR audio segment loader.
- `input_dir` controls whether output paths mirror the input directory structure.
- Output files are written with the model `sample_rate` and float audio data via `soundfile`.
- The model is temporarily switched to eval/frozen mode and restored afterward.
- The output is cropped to each input's valid length before writing.

Shape expectations:

- Model inputs use `(B, C, T)` for multi-channel audio.
- Single-channel `(B, T)` batches are expanded to `(B, 1, T)` by batch parsing or processing code.
- Outputs should be time-domain audio with the same valid length as the input after `match_batch_length()`.

## Processing Model Families

| Family | Class | Config `model.type` | Main blocks | Notes |
| --- | --- | --- | --- | --- |
| Encoder-mask-decoder | `EncMaskDecAudioToAudioModel` | `mask_based` or omitted default | encoder, mask estimator, mask processor, decoder | Good for masking, separation, beamforming, dereverberation. |
| Predictive | `PredictiveAudioToAudioModel` | `predictive` | encoder, neural estimator, decoder | Directly predicts encoded target coefficients. |
| Score-based generative | `ScoreBasedGenerativeAudioToAudioModel` | `score_based` | encoder, decoder, score estimator, SDE, sampler | Diffusion/SDE inference through sampler. |
| Schrödinger Bridge | `SchroedingerBridgeAudioToAudioModel` | `schroedinger_bridge` | encoder, decoder, estimator, noise schedule, sampler | Data-to-data generative enhancement. |
| Flow matching | `FlowMatchingAudioToAudioModel` | `flow_matching` | encoder, decoder, estimator, flow, sampler, optional SSL masking | Noise-to-data generation and SSL pretraining support. |
| Maxine BNR2 | `BNR2` | `bnr` | SEASR denoising network | 16 kHz, single-channel BNR, 10 ms alignment padding. |

## Model Forward Contracts

Encoder-mask-decoder:

- Accepts `input_signal` and optional `input_length`.
- Encodes audio, estimates masks, processes masked representation, decodes to time-domain output.
- Evaluation computes configured loss and metrics on processed versus target signal.

Predictive:

- Accepts `(B, C, T)` input and optional lengths.
- Optionally normalizes input peak level with `normalize_input`.
- Encoder produces latent representation; estimator predicts target representation; decoder returns waveform.
- Output is denormalized when needed and padded/cropped to input length.

Score-based generative:

- Uses SDE time sampling during training and sampler-based generation during inference.
- Config must define SDE at model level, not inside sampler config; model code rejects sampler configs containing `sde` or `score_estimator`.
- `max_utts_evaluation_metrics` limits expensive full-inference metric updates during validation/test.

Flow matching:

- Uses flow time sampling during training and sampler-based generation during inference.
- `estimator_target` defaults to `conditional_vector_field`; `data` is also supported.
- `p_cond` controls conditional input dropout during training.
- Optional `ssl_pretrain_masking` masks encoded input for self-supervised pretraining.
- `_parse_batch()` treats missing target as a clone of input, enabling SSL-style self-reconstruction.

Schrödinger Bridge:

- Uses `noise_schedule`, `sampler`, and `estimator_output`.
- Supports a single `loss` or split `loss_encoded` plus `loss_time`; configuring both styles together raises an error.
- `estimator_output='data_prediction'` is implemented in the inspected model code.
- Validation/test metric generation can be limited by `max_utts_evaluation_metrics`.

Maxine BNR2:

- Accepts `(B, T)` or `(B, 1, T)` input only.
- Raises on multi-channel input where channel dimension is not 1.
- Requires 16 kHz sample rate.
- Pads input to a multiple of 10 ms samples and trims output to original length.
- Optional training config can enable weight normalization in internal GRU/conv/linear layers.

## Dataset APIs

Factory imports:

```python
from nemo.collections.audio.data import audio_to_audio_dataset

dataset = audio_to_audio_dataset.get_audio_to_target_dataset(config)
dataset = audio_to_audio_dataset.get_audio_to_target_with_reference_dataset(config)
dataset = audio_to_audio_dataset.get_audio_to_target_with_embedding_dataset(config)
```

Core classes:

```python
from nemo.collections.audio.data.audio_to_audio import AudioToTargetDataset
from nemo.collections.audio.data.audio_to_audio import AudioToTargetWithReferenceDataset
from nemo.collections.audio.data.audio_to_audio import AudioToTargetWithEmbeddingDataset
```

Common config fields:

| Field | Use |
| --- | --- |
| `manifest_filepath` | NeMo JSONL manifest path. |
| `sample_rate` | Target loading sample rate. |
| `input_key` | Manifest key for input audio. |
| `target_key` | Manifest key for target audio; can be `None` for inference. |
| `reference_key` | Manifest key for reference audio in reference dataset. |
| `embedding_key` | Manifest key for `.npy` embedding vector. |
| `audio_duration` | Fixed segment duration in seconds. |
| `random_offset` | Randomize segment offset when duration is fixed. |
| `min_duration` / `max_duration` | Filter examples by manifest duration. |
| `max_utts` | Limit number of utterances. |
| `input_channel_selector` | Select input channels. |
| `target_channel_selector` | Select target channels. |
| `reference_channel_selector` | Select reference channels. |
| `reference_is_synchronized` | Load reference with the same segment as input/target when true. |
| `reference_duration` | Independent reference duration when unsynchronized. |
| `normalization_signal` | Normalize all audio by one signal's peak. |

Dataset behavior:

- `AudioToTargetDataset` returns input/target signals and lengths.
- `AudioToTargetWithReferenceDataset` also returns reference signal and length; reference can be synchronized or independently loaded.
- `AudioToTargetWithEmbeddingDataset` also returns an embedding vector and length; `.npy` is the supported embedding file format in source code.
- Audio path values can be strings or lists. Lists are concatenated along the channel dimension.
- The collate function zero-pads each signal type to the longest sample in the batch and interleaves signals and lengths.
- For fixed-duration segments, input and target segments are synchronized; random offset uses the shortest available synchronized duration.
- `normalization_signal` can be `input_signal`, `target_signal`, `reference_signal`, or `None` depending on dataset type.

## Audio Processor API

`ASRAudioProcessor` is the audio collection's internal loader/processor despite the ASR prefix.

```python
from nemo.collections.audio.data.audio_to_audio import ASRAudioProcessor, SignalSetup

processor = ASRAudioProcessor(sample_rate=16000, random_offset=True, normalization_signal="input_signal")
processor.sync_setup = SignalSetup(
    signals=["input_signal", "target_signal"],
    duration=4.0,
    channel_selectors=[None, 0],
)
```

Key behaviors:

- Synchronous signals share the same start and duration.
- Asynchronous signals can use independent durations and offsets.
- Embedding signals are loaded as vectors, currently from `.npy` files.
- `get_samples_from_file()` supports single files or lists of files. Lists become multi-channel arrays.
- Single-channel arrays are shape `(samples,)`; multi-channel arrays are shape `(channels, samples)`.
- If requested duration plus offset exceeds the shortest synchronized file, the segment is shortened to available duration.
- `fixed_offset` greater than the shortest file raises `ValueError`.

## Lhotse API

Imports:

```python
from nemo.collections.audio.data.audio_to_audio_lhotse import LhotseAudioToTargetDataset
from nemo.collections.audio.data.audio_to_audio_lhotse import convert_manifest_nemo_to_lhotse
from nemo.collections.common.data.lhotse import get_lhotse_dataloader_from_config
```

Dataset behavior:

- Main recording audio is collated into `input_signal` and `input_length`.
- If every retained cut has custom `target_recording`, target audio is collated into `target_signal` and `target_length`.
- If every retained cut has custom `reference_recording`, reference audio is collated into `reference_signal` and `reference_length`.
- If every retained cut has custom `embedding_vector`, custom arrays are collated.
- Mixed cuts are reduced to their first non-padding cut for target/reference handling.
- Main input collation uses `fault_tolerant=True`; target/reference collation does not in inspected code.

Conversion API:

```python
convert_manifest_nemo_to_lhotse(
    input_manifest="pairs.jsonl",
    output_manifest="pairs_cuts.jsonl",
    input_key="input_filepath",
    target_key="target_filepath",
    reference_key="reference_filepath",
    embedding_key="embedding_filepath",
    force_absolute_paths=False,
)
```

Conversion behavior:

- Creates a Lhotse recording from `input_key` and truncates the cut to manifest `duration`, with optional `offset`.
- Adds `target_recording`, `reference_recording`, and `embedding_vector` custom fields when present.
- Supports multi-file recordings by creating multiple audio sources and asserting matching sample rates.
- Supports `.npy` embedding arrays.
- Preserves relative paths when `force_absolute_paths=false`; writes absolute-resolved paths when true.
- Carries unconsumed manifest fields into the cut's custom metadata.

Known source caveat:

- The inspected conversion helper uses the target path variable while making the reference recording relative. Be cautious with reference conversion and verify output CutSets when using `reference_key`.

## Metrics and Losses

Common imports:

```python
from nemo.collections.audio.metrics import AudioMetricWrapper
from nemo.collections.audio.metrics import SquimMOSMetric, SquimObjectiveMetric
from nemo.collections.audio.losses import MAELoss, MSELoss, SDRLoss
```

Metric names used by `audio_to_audio_eval.py`:

| Name | Metric |
| --- | --- |
| `sdr` | `torchmetrics.audio.sdr.SignalDistortionRatio` wrapped by `AudioMetricWrapper`. |
| `sisdr` | `ScaleInvariantSignalDistortionRatio` wrapped by `AudioMetricWrapper`. |
| `stoi` | `ShortTimeObjectiveIntelligibility(extended=False)`. |
| `estoi` | `ShortTimeObjectiveIntelligibility(extended=True)`. |
| `pesq` | `PerceptualEvaluationSpeechQuality(mode='wb')`. |
| `squim_mos` | `SquimMOSMetric`. |
| `squim_stoi` | `SquimObjectiveMetric(metric='stoi')`. |
| `squim_pesq` | `SquimObjectiveMetric(metric='pesq')`. |
| `squim_si_sdr` | `SquimObjectiveMetric(metric='si_sdr')`. |

Metric wrapper notes:

- Audio metrics operate on predicted/target tensors and valid lengths.
- Some objective metrics require matching processed and target lengths.
- PESQ/STOI/SQUIM can require optional dependencies and particular sample-rate assumptions.
- Model validation metrics are configured under `model.metrics.val` and `model.metrics.test` by Hydra.

## Transform, Masking, and Multi-Channel Modules

Transform classes documented by the API docs include:

```python
from nemo.collections.audio.modules.transforms import AudioToSpectrogram, SpectrogramToAudio
from nemo.collections.audio.modules.features import SpectrogramToMultichannelFeatures
from nemo.collections.audio.modules.projections import MixtureConsistencyProjection
```

Masking and beamforming classes include:

```python
from nemo.collections.audio.modules.masking import MaskEstimatorRNN, MaskEstimatorFlexChannels, MaskEstimatorGSS
from nemo.collections.audio.modules.masking import MaskReferenceChannel, MaskBasedBeamformer, MaskBasedDereverbWPE
```

Multi-channel submodules include:

```python
from nemo.collections.audio.parts.submodules.multichannel import ChannelAugment
from nemo.collections.audio.parts.submodules.multichannel import TransformAverageConcatenate, TransformAttendConcatenate
from nemo.collections.audio.parts.submodules.multichannel import ChannelAveragePool, ChannelAttentionPool
from nemo.collections.audio.parts.submodules.multichannel import ParametricMultichannelWienerFilter
from nemo.collections.audio.parts.submodules.multichannel import ReferenceChannelEstimatorSNR, WPEFilter
```

Generative submodules include diffusion, flow, Schrödinger Bridge, NCSN++, and TransformerUNet components documented in the API docs. Prefer instantiating these via Hydra `_target_` configs unless writing tests or small probes; config-driven instantiation keeps checkpoint compatibility clearer.

## Training Script Model Type Mapping

`examples/audio/audio_to_audio_train.py` maps `model.type` as follows:

| `model.type` | Class |
| --- | --- |
| `mask_based` | `EncMaskDecAudioToAudioModel` |
| `predictive` | `PredictiveAudioToAudioModel` |
| `score_based` | `ScoreBasedGenerativeAudioToAudioModel` |
| `schroedinger_bridge` | `SchroedingerBridgeAudioToAudioModel` |
| `flow_matching` | `FlowMatchingAudioToAudioModel` |
| `bnr` | `BNR2` |

If `model.type` is missing, the training script defaults to `mask_based` with a warning.

## Safe API Use Checklist

Before writing audio code:

- Confirm the user wants audio-to-audio, not ASR transcription or TTS synthesis.
- Identify model family and checkpoint source.
- Confirm sample rate and channel count match the model, especially for BNR2 and multi-channel beamforming.
- Validate manifests with the bundled checker.
- Use `restore_from()` for local `.nemo`; use `from_pretrained()` only with download/cache approval.
- Keep output directories and output manifests explicit and outside input data directories when possible.
- Use Lhotse only when its optional dependency stack is installed and the data is actually CutSet/Shar or online-augmentation oriented.
