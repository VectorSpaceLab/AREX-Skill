# Audio Workflows

This reference gives self-contained procedures for NeMo Speech audio-to-audio work. Evidence was distilled from `docs/source/audio/intro.rst`, `docs/source/audio/models.rst`, `docs/source/audio/datasets.rst`, `docs/source/audio/configs.rst`, `examples/audio/audio_to_audio_train.py`, `examples/audio/process_audio.py`, `examples/audio/audio_to_audio_eval.py`, `examples/audio/save_augmented.py`, `examples/audio/conf/*.yaml`, `nemo/collections/audio/models/*.py`, `nemo/collections/audio/data/**`, and audio tests.

## Choose the Audio Workflow

- Use audio-to-audio processing when the user has a `.nemo` checkpoint or pretrained audio model name and wants enhanced/restored/separated output audio files.
- Use evaluation when the manifest has both processed or input audio and target audio and the user needs objective metrics such as SDR, SI-SDR, STOI, ESTOI, PESQ, or SQUIM metrics.
- Use training or fine-tuning when the user has paired input/target manifests or Lhotse CutSets/Shar data and wants to fit a predictive, masking, score-based, Schrödinger Bridge, flow-matching, or Maxine BNR model.
- Use Lhotse workflows when online augmentation, CutSet/Shar data, modular tar-like storage, or multi-source sampling is needed.
- Use augmentation saving when the user wants to materialize online-augmented Lhotse training samples for debugging or validation-set creation.

## Preflight Manifests

Validate NeMo-format JSONL manifests before long jobs:

```bash
python scripts/check_audio_manifest.py train.jsonl \
  --input-key noisy_filepath \
  --target-key clean_filepath \
  --require-target \
  --min-duration 0.1 \
  --check-files
```

For processing-only manifests where target audio is absent:

```bash
python scripts/check_audio_manifest.py infer.jsonl \
  --input-key audio_filepath \
  --output-dir enhanced_audio \
  --output-manifest enhanced_manifest.json
```

Preflight rules:

- Each line must be one JSON object; blank lines are invalid for NeMo audio manifests.
- `duration` should be a positive numeric value; it drives filtering, truncation, batching, and progress estimates.
- Audio path fields can be strings or lists of strings. Lists are used to compose multi-channel signals from multiple files.
- Relative paths should resolve relative to the manifest file location for NeMo-style loaders and conversion helpers.
- Use `--require-target` for training and evaluation. Leave it off for inference-only processing.
- Validate output locations before processing so a generated output directory or manifest does not accidentally point inside the input tree or overwrite a required input manifest.

## Load Audio Models in Python

Generic model loading:

```python
from nemo.collections.audio.models import AudioToAudioModel

model = AudioToAudioModel.restore_from("enhancer.nemo")
model = AudioToAudioModel.from_pretrained("pretrained-audio-model-name")
model.eval()
```

When restoring an unknown `.nemo`, `AudioToAudioModel.restore_from(..., return_config=True)` can reveal the original target class. The processing script uses that class path to import the concrete subclass before calling `restore_from()`.

Common concrete classes:

```python
from nemo.collections.audio.models.enhancement import EncMaskDecAudioToAudioModel
from nemo.collections.audio.models.enhancement import PredictiveAudioToAudioModel
from nemo.collections.audio.models.enhancement import ScoreBasedGenerativeAudioToAudioModel
from nemo.collections.audio.models.enhancement import SchroedingerBridgeAudioToAudioModel
from nemo.collections.audio.models.enhancement import FlowMatchingAudioToAudioModel
from nemo.collections.audio.models.maxine import BNR2
```

Operational notes:

- `restore_from()` loads a local `.nemo` checkpoint.
- `from_pretrained()` may read a local cache or download from a model registry; confirm network/cache policy before using it.
- Training normally requires GPU/CUDA. Inference can run on CPU for small jobs but GPU is recommended for practical throughput and generative samplers.
- Current NeMo Speech docs target Python 3.12+, PyTorch 2.7+, and GPU/CUDA for normal training. Optional broad extras were not installed during skill generation, so install only the workflow-specific dependencies needed by the user.

## Process Audio Files

Use the `AudioToAudioModel` API directly. This keeps the workflow self-contained and avoids depending on source-tree example scripts.

Model/data selection contract:

- Set exactly one model source: `model_path` for a local `.nemo`, or `pretrained_name` for a registry/cache-backed model name.
- Set at least one data source: `audio_dir` for recursive file discovery, or `dataset_manifest` plus an `input_key`.
- `audio_dir` discovery should filter by a known extension such as `.wav`, `.flac`, or `.mp3`.
- `dataset_manifest` keys commonly include `audio_filepath`, `noisy_filepath`, `input_filepath`, `clean_filepath`, `speech_filepath`, or `target_filepath`; pass the actual input key explicitly.
- `input_channel_selector` may select channels from multi-channel audio. Source/data tests cover integers and lists; the loader type also supports ASR-style channel selector values.
- Keep `output_dir` and `output_filename` explicit. Do not overwrite an existing output directory or input manifest without user approval.
- When processing from a manifest, preserve original fields and add `processed_audio_filepath` in the output manifest.
- When processing from a directory, use `input_dir` so output files can mirror the input directory structure beneath `output_dir`.

Self-contained processing skeleton:

```python
import glob
import json
from pathlib import Path

import lightning.pytorch as pl
import torch
from nemo.collections.audio.models import AudioToAudioModel
from nemo.utils import model_utils


def load_audio_model(model_path=None, pretrained_name=None, cuda=None, override_config_path=None):
    if (model_path is None) == (pretrained_name is None):
        raise ValueError("Provide exactly one of model_path or pretrained_name")
    if cuda is None:
        device = [0] if torch.cuda.is_available() else 1
        accelerator = "gpu" if torch.cuda.is_available() else "cpu"
    elif cuda < 0:
        device = 1
        accelerator = "cpu"
    else:
        device = [cuda]
        accelerator = "gpu"
    map_location = torch.device(f"cuda:{device[0]}" if accelerator == "gpu" else "cpu")
    if model_path:
        cfg = AudioToAudioModel.restore_from(model_path, return_config=True)
        model_class = model_utils.import_class_by_path(cfg.target)
        model = model_class.restore_from(model_path, override_config_path=override_config_path, map_location=map_location)
    else:
        model = AudioToAudioModel.from_pretrained(pretrained_name, map_location=map_location)
    model.set_trainer(pl.Trainer(devices=device, accelerator=accelerator))
    return model.eval()


def manifest_audio_paths(manifest_path, input_key):
    manifest_path = Path(manifest_path)
    paths = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            value = Path(item[input_key])
            paths.append(str(value if value.is_absolute() else manifest_path.parent / value))
    return paths


def process_audio(model, filepaths, output_dir, input_dir=None, input_channel_selector=None, batch_size=1, num_workers=0):
    with torch.no_grad():
        return model.process(
            paths2audio_files=filepaths,
            output_dir=output_dir,
            batch_size=batch_size,
            num_workers=num_workers,
            input_channel_selector=input_channel_selector,
            input_dir=input_dir,
        )


model = load_audio_model(model_path="enhancer.nemo", cuda=0)
filepaths = manifest_audio_paths("infer.jsonl", input_key="noisy_filepath")
processed = process_audio(model, filepaths, output_dir="enhanced_audio", input_dir=str(Path("infer.jsonl").parent))
with open("enhanced_manifest.json", "w", encoding="utf-8") as out, open("infer.jsonl", "r", encoding="utf-8") as src:
    for line, processed_path in zip(src, processed):
        item = json.loads(line)
        item["processed_audio_filepath"] = processed_path
        out.write(json.dumps(item) + "\n")
```

For directory input, replace `manifest_audio_paths(...)` with `glob.glob(str(Path(audio_dir) / "**" / "*.wav"), recursive=True)` and pass `input_dir=audio_dir`.

`AudioToAudioModel.process()` creates a temporary manifest, loads audio with the model sample rate, runs the model in evaluation mode, writes float audio via `soundfile`, and returns processed output paths. It restores the model's previous train/eval mode after processing.

## Evaluate Processed Audio

Evaluation requires a manifest with target audio. Score an already processed manifest, or first create one with the processing skeleton above.

Evaluation contract:

- Use a manifest input; target audio must come from a manifest, not from a bare directory.
- The processed key defaults to the processing output field `processed_audio_filepath`.
- Target keys vary by config: `target_filepath`, `clean_filepath`, `speech_filepath`, or `target_audio_filepath` are common. Pass the actual key.
- Resolve relative processed paths against the processed manifest location. Resolve relative target paths against the target manifest directory or an explicit `target_dataset_dir`.
- If returning per-example metrics, use `batch_size=1`.
- Available metric names in NeMo's audio evaluation evidence include `sdr`, `sisdr`, `stoi`, `estoi`, `pesq`, `squim_mos`, `squim_stoi`, `squim_pesq`, and `squim_si_sdr`.
- PESQ and SQUIM metrics may require optional dependencies or model downloads depending on the runtime stack; use SDR/SI-SDR/STOI/ESTOI first for lightweight checks.
- Fail early if processed or target files are missing, if lengths mismatch, if the processed key is absent, or if the target key is absent.

Self-contained scoring skeleton:

```python
import json
from pathlib import Path

import torch
from nemo.collections.audio.data import audio_to_audio_dataset
from nemo.collections.audio.metrics import AudioMetricWrapper
from nemo.collections.common.parts.preprocessing import manifest as manifest_utils
from torchmetrics.audio.sdr import ScaleInvariantSignalDistortionRatio, SignalDistortionRatio
from torchmetrics.audio.stoi import ShortTimeObjectiveIntelligibility


def metric_from_name(name, sample_rate=16000):
    name = name.lower()
    if name == "sdr":
        return AudioMetricWrapper(metric=SignalDistortionRatio())
    if name == "sisdr":
        return AudioMetricWrapper(metric=ScaleInvariantSignalDistortionRatio())
    if name == "stoi":
        return AudioMetricWrapper(metric=ShortTimeObjectiveIntelligibility(fs=sample_rate, extended=False))
    if name == "estoi":
        return AudioMetricWrapper(metric=ShortTimeObjectiveIntelligibility(fs=sample_rate, extended=True))
    raise ValueError(f"Unsupported lightweight metric: {name}")


def build_scoring_manifest(input_manifest, output_manifest, processed_key, target_key, target_dataset_dir=None):
    input_manifest = Path(input_manifest)
    target_dataset_dir = str(target_dataset_dir) if target_dataset_dir else None
    with input_manifest.open("r", encoding="utf-8") as src, Path(output_manifest).open("w", encoding="utf-8") as out:
        for line in src:
            item = json.loads(line)
            if processed_key not in item or target_key not in item:
                raise KeyError(f"missing {processed_key!r} or {target_key!r}")
            scored = {
                "processed": manifest_utils.get_full_path(item[processed_key], manifest_file=str(input_manifest)),
                "target": manifest_utils.get_full_path(item[target_key], data_dir=target_dataset_dir or str(input_manifest.parent)),
                "duration": item.get("duration"),
            }
            if not Path(scored["processed"]).is_file() or not Path(scored["target"]).is_file():
                raise FileNotFoundError(scored)
            out.write(json.dumps(scored) + "\n")


scoring_manifest = "scoring_manifest.jsonl"
build_scoring_manifest("enhanced_manifest.json", scoring_manifest, "processed_audio_filepath", "clean_filepath")
dataset = audio_to_audio_dataset.get_audio_to_target_dataset({
    "manifest_filepath": scoring_manifest,
    "sample_rate": 16000,
    "input_key": "processed",
    "target_key": "target",
    "batch_size": 1,
})
loader = torch.utils.data.DataLoader(dataset, batch_size=1, collate_fn=dataset.collate_fn, shuffle=False)
metrics = {name: metric_from_name(name) for name in ["sdr", "estoi"]}
for batch in loader:
    processed_signal, processed_length, target_signal, target_length = batch
    if not torch.equal(processed_length, target_length):
        raise RuntimeError("processed and target lengths differ")
    for metric in metrics.values():
        metric.update(preds=processed_signal, target=target_signal, input_length=target_length)
print({name: metric.compute().item() for name, metric in metrics.items()})
```

Add PESQ or SQUIM only after their optional dependency stack is installed; see `references/api-reference.md` for metric class names.

## Train or Fine-Tune Audio Models

Use a user-owned training entry point or notebook that instantiates the class implied by `model.type`. Evidence maps `model.type` values to `mask_based`, `predictive`, `score_based`, `schroedinger_bridge`, `flow_matching`, and `bnr`.

Minimal self-contained training skeleton:

```python
import lightning.pytorch as pl
from omegaconf import OmegaConf
from nemo.collections.audio.models.enhancement import EncMaskDecAudioToAudioModel
from nemo.collections.audio.models.enhancement import FlowMatchingAudioToAudioModel
from nemo.collections.audio.models.enhancement import PredictiveAudioToAudioModel
from nemo.collections.audio.models.enhancement import SchroedingerBridgeAudioToAudioModel
from nemo.collections.audio.models.enhancement import ScoreBasedGenerativeAudioToAudioModel
from nemo.collections.audio.models.maxine import BNR2
from nemo.utils.exp_manager import exp_manager

MODEL_CLASSES = {
    "mask_based": EncMaskDecAudioToAudioModel,
    "predictive": PredictiveAudioToAudioModel,
    "score_based": ScoreBasedGenerativeAudioToAudioModel,
    "schroedinger_bridge": SchroedingerBridgeAudioToAudioModel,
    "flow_matching": FlowMatchingAudioToAudioModel,
    "bnr": BNR2,
}

cfg = OmegaConf.load("audio_experiment.yaml")
trainer = pl.Trainer(**cfg.trainer)
exp_manager(trainer, cfg.get("exp_manager", None))
model_type = cfg.model.get("type", "mask_based")
model_cls = MODEL_CLASSES[model_type]
model = model_cls(cfg=cfg.model, trainer=trainer)
model.maybe_init_from_pretrained_checkpoint(cfg)
trainer.fit(model)
if cfg.model.get("test_ds") is not None and model.prepare_test(trainer):
    trainer.test(model)
```

Training config shape:

```yaml
init_from_nemo_model: null
init_from_pretrained_model: null
model:
  type: predictive
  sample_rate: 16000
  train_ds:
    manifest_filepath: train.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    audio_duration: 4.0
    random_offset: true
    batch_size: 8
    shuffle: true
  validation_ds:
    manifest_filepath: val.jsonl
    input_key: noisy_filepath
    target_key: clean_filepath
    batch_size: 8
    shuffle: false
trainer:
  devices: 1
  accelerator: gpu
  max_epochs: 50
```

Training notes:

- `model.maybe_init_from_pretrained_checkpoint(cfg)` handles `init_from_nemo_model` and `init_from_pretrained_model` when provided through the config.
- Keep architecture-compatible config parameters when fine-tuning from a checkpoint; mismatched encoder/decoder/estimator shapes will fail to load cleanly.
- Use `skip_nan_grad=true` only when you understand the optimization tradeoff; the base model zeros gradients when NaN/Inf appears and synchronizes this decision across distributed workers.
- If `model.test_ds` is present, run test only after confirming the chosen trainer/device setup is safe.
- Generative models can be slow during validation because metric updates require full inference; configs often use `max_utts_evaluation_metrics` to limit metric computation.

## Model Family Selection

Mask-based and beamforming workflows:

- Use `mask_based` configs when the architecture is encoder-mask-decoder, STFT/inverse-STFT, RNN/FlexChannels/GSS mask estimators, mask processors, dereverberation, or multichannel Wiener filtering.
- `masking.yaml`, `beamforming.yaml`, and `beamforming_flex_channels.yaml` evidence shows `audio_filepath` and `target_filepath` or `target_anechoic_filepath` manifest keys, with target channel selection often set to `0`.
- Flex-channel configs load all input channels and select a target channel for supervision.

Predictive workflows:

- Use `predictive` configs when a neural estimator directly predicts encoded target coefficients from input audio.
- Evidence configs use `noisy_filepath` and `clean_filepath`, `normalize_input=true`, STFT encoder/decoder, and NCSN++/Conformer/TransformerUNet-style estimators.
- Streaming predictive configs set `normalize_input=false` and use Lhotse Shar/CutSet data with distributed sampler disabled.

Score-based generative workflows:

- Use `score_based` configs for diffusion/SDE enhancement. The model includes encoder, decoder, score estimator, SDE, and sampler.
- Validation/inference can be expensive; use `max_utts_evaluation_metrics` and sampler overrides to control runtime.

Schrödinger Bridge workflows:

- Use `schroedinger_bridge` configs for data-to-data generative enhancement. The model includes encoder, decoder, estimator, noise schedule, sampler, and optionally separate encoded/time-domain losses.
- Configs and model code use `estimator_output`, `noise_schedule`, `sampler`, `loss_encoded`, `loss_time`, and metric limits.

Flow-matching workflows:

- Use `flow_matching` configs for noise-to-data generative enhancement. The model includes encoder, decoder, estimator, flow, sampler, conditional dropout `p_cond`, and optional SSL pretraining masking.
- SSL pretraining configs can omit target audio; the flow model treats missing target as input for self-reconstruction in its overridden batch parser.
- At inference, `forward()` disables SSL masking; `forward_eval()` enables it for evaluation when configured.

Maxine BNR workflows:

- Use `bnr`/`maxine_bnr.yaml` for Maxine BNR2 background-noise removal.
- `BNR2` currently supports only sample rate 16000 and single-channel input. It pads input to a multiple of 10 ms alignment samples and trims output back to the original length.
- Multi-channel BNR input must be selected or downmixed before the model.

## Lhotse Audio Workflows

Audio configs can use Lhotse CutSet or Shar input by setting `use_lhotse=true` and providing `cuts_path`, `shar_path`, or nested `input_cfg` entries.

CutSet training shape:

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

Shar training shape:

```yaml
model:
  train_ds:
    use_lhotse: true
    shar_path: train_shar
    truncate_duration: 4.0
    truncate_offset_type: random
    batch_size: 8
    shuffle: true
trainer:
  use_distributed_sampler: false
```

Online augmentation shape:

```yaml
model:
  train_ds:
    use_lhotse: true
    cuts_path: clean_speech_cuts.jsonl
    truncate_duration: 4.0
    truncate_offset_type: random
    rir_enabled: true
    rir_path: rir_recordings.jsonl
    noise_path: noise_cuts.jsonl
```

Lhotse notes:

- Audio Lhotse targets live in custom fields named `target_recording`, with optional `reference_recording` and `embedding_vector`.
- NeMo's `LhotseAudioToTargetDataset` returns dictionary batches with `input_signal`, `input_length`, and optional `target_signal`, `reference_signal`, or `embedding_signal`.
- For Lhotse data in Lightning, set `trainer.use_distributed_sampler=false` because Lhotse handles sampling.
- For Shar or infinite-style data, bound training with `trainer.limit_train_batches`, `trainer.val_check_interval`, and `trainer.max_steps` as appropriate.
- When using online augmentation, ensure target recordings are present and that RIR/noise manifests match sample-rate and duration expectations.

## Convert NeMo Manifests to Lhotse

The source docs mention a conversion script; the in-package helper is `convert_manifest_nemo_to_lhotse()`.

Python conversion pattern:

```python
from nemo.collections.audio.data.audio_to_audio_lhotse import convert_manifest_nemo_to_lhotse

convert_manifest_nemo_to_lhotse(
    input_manifest="train.jsonl",
    output_manifest="train_cuts.jsonl",
    input_key="input_filepath",
    target_key="target_filepath",
    reference_key="reference_filepath",
    embedding_key="embedding_filepath",
    force_absolute_paths=False,
)
```

Conversion notes:

- `input_key` maps to the main Lhotse `Cut.recording`.
- `target_key` maps to `cut.target_recording` when present.
- `reference_key` maps to `cut.reference_recording` when present.
- `embedding_key` maps `.npy` arrays to `cut.embedding_vector`.
- Input/target/reference channel selectors in the NeMo manifest are carried through as Lhotse channel selection or custom fields.
- For Shar export, absolute source paths are often easier: call conversion with `force_absolute_paths=True`, then run the user's chosen Lhotse Shar export command.

## Save Online-Augmented Audio

The augmentation-saving workflow materializes augmented input/target pairs from a Lhotse dataloader. It is intended for validation set preparation and debugging, not for in-place mutation of an existing dataset.

Self-contained implementation outline:

```python
from itertools import islice
from pathlib import Path

import lhotse
import soundfile as sf
from lhotse import CutSet, MonoCut, Recording
from nemo.collections.audio.data.audio_to_audio_lhotse import LhotseAudioToTargetDataset
from nemo.collections.common.data.lhotse.dataloader import get_lhotse_dataloader_from_config
from omegaconf import OmegaConf

cfg = OmegaConf.load("audio_experiment.yaml")
input_cuts = Path("cuts.jsonl")
output_cuts = Path("augmented/cuts.augmented.jsonl")
output_cuts.parent.mkdir(parents=True, exist_ok=False)
OmegaConf.update(cfg, "model.train_ds.cuts_path", str(input_cuts), force_add=True)
OmegaConf.update(cfg, "model.train_ds.shuffle", False, force_add=True)
OmegaConf.update(cfg, "model.train_ds.batch_size", 1, force_add=True)
dataloader = get_lhotse_dataloader_from_config(
    OmegaConf.create(cfg.model.train_ds), global_rank=0, world_size=1, dataset=LhotseAudioToTargetDataset()
)
original_cuts = lhotse.CutSet.from_file(input_cuts)
with CutSet.open_writer(output_cuts) as writer:
    for idx, (sample, original_cut) in enumerate(zip(islice(dataloader, 100), original_cuts)):
        input_audio = sample["input_signal"][0].numpy()
        target_audio = sample["target_signal"][0].numpy()
        input_path = output_cuts.parent / "audio" / f"{idx:06}.input.flac"
        target_path = output_cuts.parent / "audio" / f"{idx:06}.output.flac"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(input_path, input_audio, cfg.model.sample_rate, format="FLAC", subtype="PCM_24")
        sf.write(target_path, target_audio, cfg.model.sample_rate, format="FLAC", subtype="PCM_24")
        input_recording = Recording.from_file(input_path)
        target_recording = Recording.from_file(target_path)
        input_recording.sources[0].source = str(input_path.relative_to(output_cuts.parent))
        target_recording.sources[0].source = str(target_path.relative_to(output_cuts.parent))
        cut = MonoCut(id=input_recording.id, start=0, channel=0, duration=input_recording.duration, recording=input_recording)
        cut.target_recording = target_recording
        for field in ("text", "original_text", "language"):
            if hasattr(original_cut, field):
                setattr(cut, field, getattr(original_cut, field))
        writer.write(cut)
```

Augmentation-saving contract:

- Input must be a Lhotse CutSet JSONL of `MonoCut` objects.
- The input cut recording source path should be relative and should exist relative to the input cuts file.
- The output cuts parent directory should be intentionally chosen and empty or newly created.
- Write FLAC files under the output parent, either in an `audio/` subdirectory or by preserving input directory structure.
- Output files should use `.input.flac` and `.output.flac` suffixes and a new CutSet JSONL with `target_recording`.
- Disable shuffle, batch with size 1, and avoid bucketing/filtering changes when a one-to-one deterministic mapping from input cuts to output cuts is required.

## Multi-Channel Handling

NeMo audio code consistently normalizes tensors to multi-channel format `(B, C, T)` inside models.

Manifest and loader patterns:

- A manifest key may hold one audio path, a multi-channel audio file path, or a list of paths.
- A list of paths is concatenated along the channel dimension; tests cover target lists and combinations of target keys.
- `input_channel_selector`, `target_channel_selector`, and `reference_channel_selector` can select a single channel or a list of channels.
- Lhotse conversion supports `input_channel_selector`, `target_channel_selector`, and `reference_channel_selector` and stores target/reference channel selectors as custom fields when needed.
- Flex-channel mask/beamforming configs keep all input channels (`input_channel_selector: null`) and select a target channel for supervision.

Practical guidance:

- Record the intended channel semantics in the manifest or experiment notes before training: microphone array channels, reference playback, target speaker channel, or composed targets.
- For single-channel models such as Maxine BNR2, select or downmix a channel before calling the model.
- When channel counts differ across samples, prefer architectures/configs explicitly designed for flexible channels, or normalize channel layout before training.
- During evaluation, set `processed_channel_selector` and `target_channel_selector` so the compared signals have matching channel counts.

## Source Scripts Policy

The following source scripts are reference-only in this generated skill:

- `examples/audio/audio_to_audio_train.py`: training-heavy, GPU-dependent, long-running, and tied to user-selected configs and datasets.
- `examples/audio/process_audio.py`: may download pretrained models, load checkpoints, create output trees, and run GPU inference; command contracts are distilled here instead of copying the full script.
- `examples/audio/audio_to_audio_eval.py`: depends on processing, objective metric packages, temporary manifests, and GPU/CPU runtime; safe usage is distilled here.
- `examples/audio/save_augmented.py`: mutates an output directory with generated FLAC and CutSet files and depends on Lhotse/soundfile; usage contract is distilled here.
- Audio config YAML files under `examples/audio/conf/`: copied wholesale configs would be stale and architecture-specific; use the summarized config patterns in `references/configuration.md` and preserve user-selected configs externally.

The bundled `scripts/check_audio_manifest.py` is the only adapted runtime helper because it is deterministic, safe by default, standard-library-only, and useful before every long audio workflow.
