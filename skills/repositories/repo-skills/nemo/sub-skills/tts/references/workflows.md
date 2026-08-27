# TTS Workflows

This reference gives concrete NeMo Speech TTS procedures without requiring future agents to open or run original repository docs, examples, scripts, or tests. Commands here either run this sub-skill's bundled checker or use installed NeMo Python APIs in caller-owned code. Training normally requires GPU/CUDA; inference can run on CPU only for small checks and is usually GPU-recommended.

## Preflight a Manifest

Run the bundled checker from this sub-skill directory:

```bash
python scripts/check_tts_manifest.py train.jsonl --mode tts --require-audio --check-files --min-duration 0.1 --max-duration 30
```

For MagpieTTS with speaker context:

```bash
python scripts/check_tts_manifest.py magpie_train.jsonl --mode magpie --require-audio --require-context --min-duration 0.2 --max-duration 20 --style-summary
```

For G2P training:

```bash
python scripts/check_tts_manifest.py g2p_train.jsonl --mode g2p --grapheme-field text_graphemes --phoneme-field text
```

Preflight rules:

- Require audio for training/evaluation manifests and allow missing audio only for pure text inference or G2P inference.
- Treat empty `text`, whitespace-only strings, blank lines, non-object JSON, nonnumeric durations, and duplicate IDs/audio paths as blockers.
- Warn on mixed grapheme/phoneme fields, missing speaker IDs in multispeaker or context workflows, language mismatches, and duration outliers.
- Use `--audio-base-dir` when manifest paths are relative to a dataset root rather than the manifest parent.

## Install and Dependency Planning

Use the smallest dependency set that supports the task:

- Base NeMo Speech import plus TTS collection for model APIs and configs.
- `nemo_text_processing` for text normalization; check platform support before promising it on constrained platforms.
- Phonemizer/G2P extras and language dictionaries for phoneme-tokenized workflows.
- `soundfile`, `librosa`, and system audio libraries for reading/writing audio.
- PyTorch 2.7+ and Python 3.12+ are expected by current NeMo Speech docs.
- GPU/CUDA is required for practical training and recommended for inference. Do not start large training without user confirmation of hardware, output location, and checkpoint/cache policy.
- MagpieTTS inference/evaluation can require ASR, speaker verification, Hugging Face, UTMOS/FCD/EoU, PESQ, and codec model dependencies. Disable or localize optional metrics when offline.

## Load TTS Checkpoints

Local checkpoint:

```python
import nemo.collections.tts as nemo_tts

model = nemo_tts.models.FastPitchModel.restore_from("model.nemo")
model.eval()
```

Registry/cache-backed checkpoint:

```python
import nemo.collections.tts as nemo_tts

model = nemo_tts.models.FastPitchModel.from_pretrained("tts_en_fastpitch")
```

List names for a class:

```python
import nemo.collections.tts as nemo_tts

for info in nemo_tts.models.FastPitchModel.list_available_models():
    print(info.pretrained_model_name)
```

Guidelines:

- Use `restore_from()` for `.nemo` paths.
- Use `from_pretrained()` only when downloads/cache access are allowed.
- Load with the concrete model class. FastPitch, HiFi-GAN, MagpieTTS, EasyMagpieTTS, AudioCodecModel, and G2PModel checkpoints are not interchangeable.
- For unknown `.nemo` files, inspect the checkpoint config in the caller's environment and route to the recorded target class.
- Put models in `eval()` mode for inference and use `torch.no_grad()`.

## FastPitch + HiFi-GAN Synthesis

Use this path for classic cascaded synthesis from text.

```python
from pathlib import Path

import soundfile as sf
import torch
import nemo.collections.tts as nemo_tts

out_path = Path("speech.wav")
text = "NeMo can synthesize this sentence with a cascaded TTS model."

spec_generator = nemo_tts.models.FastPitchModel.from_pretrained("tts_en_fastpitch")
vocoder = nemo_tts.models.HifiGanModel.from_pretrained(model_name="tts_en_hifigan")
spec_generator.eval()
vocoder.eval()

with torch.no_grad():
    tokens = spec_generator.parse(text, normalize=True)
    spectrogram = spec_generator.generate_spectrogram(tokens=tokens, pace=1.0)
    audio = vocoder.convert_spectrogram_to_audio(spec=spectrogram)

sf.write(out_path, audio.squeeze().detach().cpu().numpy(), 22050)
```

Multispeaker FastPitch:

```python
speaker_id = 0
spectrogram = spec_generator.generate_spectrogram(tokens=tokens, speaker=speaker_id)
```

Checklist:

- Match FastPitch checkpoint language and tokenizer to input text: ARPABET, IPA, grapheme, or mixed.
- Use the vocoder released for the same language/sample-rate family where possible.
- If output is too fast/slow, adjust `pace`; if pitch/prosody is wrong, verify pitch statistics and checkpoint fit.
- If `nemo_text_processing` is missing, either install it for text normalization or pass already-normalized text and avoid relying on `normalize=True`.
- If the checkpoint has a speaker encoder/reference path, provide the required speaker ID or reference spectrogram inputs.

## FastPitch Training and Finetuning

Use caller-owned training code or a copied/adapted wrapper around NeMo's installed APIs. Do not depend on a source checkout example path. A minimal training wrapper should use this pattern:

```python
import lightning.pytorch as pl
from omegaconf import OmegaConf
from nemo.collections.tts.models import FastPitchModel
from nemo.utils.exp_manager import exp_manager

cfg = OmegaConf.load("fastpitch_train.yaml")
trainer = pl.Trainer(**cfg.trainer)
exp_manager(trainer, cfg.get("exp_manager"))
model = FastPitchModel(cfg=cfg.model, trainer=trainer)
model.maybe_init_from_pretrained_checkpoint(cfg=cfg)
trainer.fit(model)
```

The corresponding caller-owned config should contain these fields:

```yaml
trainer:
  accelerator: gpu
  devices: 1
exp_manager:
  exp_dir: experiments/fastpitch
init_from_nemo_model: null
init_from_pretrained_model: null
init_from_ptl_ckpt: null
model:
  train_ds:
    dataset:
      manifest_filepath: train.jsonl
      sample_rate: 44100
      sup_data_path: sup_data
      sup_data_types: [align_prior_matrix, pitch]
      min_duration: 0.1
      max_duration: null
    dataloader_params:
      batch_size: 32
      shuffle: true
      num_workers: 8
  validation_ds:
    dataset:
      manifest_filepath: val.jsonl
  optim:
    lr: 0.0001
```

Operational sequence:

1. Validate train/validation manifests.
2. Choose a config that matches language, sample rate, tokenizer, and speaker setup.
3. Generate or configure supplementary data such as alignment priors, pitch, and energy when the config requires it.
4. Start with a low learning rate when adapting a pretrained model.
5. Keep tokenizer, text normalizer, G2P dictionary, speaker IDs, and sample rate stable across splits.
6. Verify a small batch and validation step before launching a long run.

The original FastPitch training and finetuning scripts/configs are reference-only because they are Hydra/GPU/training-output heavy and depend on source-tree config paths.

## HiFi-GAN Training and Finetuning

Use caller-owned training code around `HifiGanModel`:

```python
import lightning.pytorch as pl
from omegaconf import OmegaConf
from nemo.collections.tts.models import HifiGanModel
from nemo.utils.exp_manager import exp_manager

cfg = OmegaConf.load("hifigan_train.yaml")
trainer = pl.Trainer(**cfg.trainer)
exp_manager(trainer, cfg.get("exp_manager"))
model = HifiGanModel(cfg=cfg.model, trainer=trainer)
model.maybe_init_from_pretrained_checkpoint(cfg=cfg)
trainer.fit(model)
```

Use config fields equivalent to:

```yaml
trainer:
  accelerator: gpu
  devices: 1
  max_epochs: 50
exp_manager:
  exp_dir: experiments/hifigan
init_from_nemo_model: hifigan_base.nemo
model:
  train_ds:
    manifest_filepath: train.jsonl
  validation_ds:
    manifest_filepath: val.jsonl
  optim:
    lr: 0.00001
```

Checklist:

- Validate waveform manifests and duration outliers.
- Match sample rate and mel preprocessing to the source acoustic model.
- Do not train on mels produced by a different preprocessor than the vocoder config expects.
- Keep generator/discriminator training output in an explicit experiment directory.
- Expect adversarial training instability; inspect generated samples early.

The original HiFi-GAN scripts/configs are reference-only because they perform long GPU training, write experiment outputs, and rely on source-tree config paths.

## MagpieTTS Batch Inference

Use the installed Magpie APIs directly for small jobs and caller-owned wrappers for batch generation. Do not depend on an original checkout inference script unless the user explicitly supplies that checkout and asks to run it. A caller-owned batch wrapper should implement this argument contract:

```yaml
model_type: magpie
nemo_files: [magpietts_model.nemo]
hparams_files: null
checkpoint_files: null
codecmodel_path: codec_model.nemo
datasets_json_path: evalset_config.json
datasets_base_path: null
datasets: null
out_dir: outputs/magpie
batch_size: 8
temperature: 0.7
topk: 80
use_cfg: true
cfg_scale: 2.5
apply_attention_prior: true
use_local_transformer: false
legacy_codebooks: false
legacy_text_conditioning: false
longform_mode: auto
max_decoder_steps: 500
run_evaluation: false
```

If using `.ckpt` plus hparams instead of `.nemo`, set `nemo_files: null` and provide matching `hparams_files` plus `checkpoint_files` arrays.

Long-form adjustments:

```yaml
longform_mode: auto
max_decoder_steps: 50000
language: en
```

Notes:

- `codecmodel_path` is required.
- Choose exactly one loading mode: `.nemo` files or hparams plus `.ckpt` files.
- Use a dataset metadata JSON; use `datasets` to select named subsets.
- Use deterministic seeding only for test-like reproducibility, understanding that backend generation may still vary.
- Use Local Transformer for frame-stacked checkpoints that need that decoding path.
- MaskGit settings apply only when the checkpoint supports that decoding path.

The original Magpie inference script is reference-only for runtime skill content because it is model/checkpoint/network/GPU/output-heavy, imports many optional packages, reads source-tree modules, and writes audio/evaluation outputs.

## EasyMagpieTTS Batch Inference

For decoder-only EasyMagpie checkpoints, use the same caller-owned wrapper contract with these additions:

```yaml
model_type: easy_magpie
phoneme_input_type: gt
phoneme_sampling_method: argmax
dropout_text_input: false
phoneme_tokenizer_path: null
disable_cas_for_context_text: false
legacy_codebooks: false
legacy_text_conditioning: false
```

Legacy flags:

- `legacy_codebooks`: old codec/special-token layout.
- `legacy_text_conditioning`: old text-conditioning config behavior.
- `disable_cas_for_context_text`: skip CAS embeddings for context text in old EasyMagpie checkpoints.
- `phoneme_tokenizer_path`: override a moved or invalid tokenizer path stored in the checkpoint.

## MagpieTTS Direct Python Inference

For simple single-item inference, use model methods when the caller's environment has the required package and checkpoints:

```python
import soundfile as sf
import torch
from nemo.collections.tts.models import MagpieTTSModel

model = MagpieTTSModel.restore_from("magpietts.nemo")
model.eval()
model.cuda()

with torch.no_grad():
    audio, audio_len = model.do_tts(
        transcript="Read this paragraph in the reference speaker's voice.",
        language="en",
        apply_TN=True,
        temperature=0.7,
        topk=80,
        use_cfg=True,
        cfg_scale=2.5,
    )

sf.write("magpie.wav", audio[0, : audio_len[0]].detach().cpu().numpy(), 22050)
```

Use batch wrapper-style inference when context audio, context text, cached codes, evaluation metrics, or multiple checkpoints are involved. Direct `do_tts()` is best for controlled smoke tests.

## MagpieTTS Finetuning

Use caller-owned training code around `MagpieTTSModel` or its preference-optimization subclasses. A training config for same-language new-speaker adaptation should include fields equivalent to:

```yaml
trainer:
  accelerator: gpu
  devices: 1
  precision: 32
exp_manager:
  exp_dir: experiments/magpie_speaker
init_from_ptl_ckpt: pretrained.ckpt
batch_size: 16
max_epochs: 100
train_ds_meta:
  en_sft:
    manifest_path: train.jsonl
    audio_dir: audio
    feature_dir: features
    sample_weight: 1.0
    tokenizer_names: [english_phoneme]
val_ds_meta:
  en_val:
    manifest_path: val.jsonl
    audio_dir: audio
    feature_dir: features
    sample_weight: 1.0
    tokenizer_names: [english_phoneme]
model:
  codecmodel_path: codec_model.nemo
  context_duration_min: 5.0
  context_duration_max: 5.0
  alignment_loss_scale: 0.0
  prior_scaling_factor: null
  load_cached_codes_if_available: true
  optim:
    lr: 0.000005
    sched: null
```

New-language adaptation changes:

- Define a tokenizer under `model.text_tokenizers.<language_key>`.
- Use one `train_ds_meta` and one `val_ds_meta` entry per language.
- Increase `sample_weight` for low-resource languages.
- Use transcript format matching the tokenizer: IPA/phoneme for phoneme tokenizers, raw/byte text for byte-level tokenizers.
- Typical multilingual learning rate can be higher than same-language speaker adaptation, but still far below pretraining rates.

Checklist:

- Require a codec model compatible with the checkpoint.
- Prefer cached codec code paths for faster finetuning.
- Disable alignment prior during finetuning unless there is a specific reason to keep it.
- Use `trainer.precision=32` for small-data finetuning stability.
- Keep output directories explicit and avoid overwriting prior experiments.

The original Magpie training scripts/configs are reference-only because they launch long GPU training, write experiment/checkpoint artifacts, and use source-tree Hydra configs.

## Magpie Preference Optimization

Use preference optimization after a supervised Magpie checkpoint is already usable. GRPO is usually simpler than DPO. A caller-owned GRPO config should include fields equivalent to:

```yaml
mode: onlinepo_train
batch_size: 2
init_from_ptl_ckpt: magpie_checkpoint.ckpt
model:
  codecmodel_path: codec_model.nemo
  num_generations_per_item: 12
  reference_free: true
  inference_cfg_prob: 0.5
  inference_cfg_scale: 2.5
  cer_reward_weight: 0.45
  ssim_reward_weight: 0.45
  pesq_reward_weight: 0.1
  use_pesq: true
  reward_asr_model: whisper
  cfg_unconditional_prob: 0.0
  decoder:
    p_dropout: 0.0
  encoder:
    p_dropout: 0.0
  alignment_loss_scale: 0.0
  prior_scaling_factor: null
  optim:
    lr: 0.0000001
```

DPO requires text-context pair generation, sample generation, preference-pair creation, and DPO finetuning. Treat DPO helper scripts as reference-only because they generate large intermediate audio/manifests and depend on checkpoint/evaluation metrics.

## G2P Training, Evaluation, and Inference

G2P manifest shape:

```json
{"text_graphemes": "Swifts, flushed from chimneys.", "text": "ˈswɪfts, ˈfɫəʃt ˈfɹəm ˈtʃɪmniz."}
```

Training/evaluation config contract:

```yaml
pretrained_model: null
do_training: true
do_testing: true
trainer:
  accelerator: gpu
  devices: 1
model:
  train_ds:
    manifest_filepath: train_g2p.jsonl
    phoneme_field: text
    grapheme_field: text_graphemes
  validation_ds:
    manifest_filepath: val_g2p.jsonl
    phoneme_field: text
    grapheme_field: text_graphemes
  test_ds:
    manifest_filepath: test_g2p.jsonl
    phoneme_field: text
    grapheme_field: text_graphemes
```

Inference contract:

```yaml
pretrained_model: g2p_model.nemo
manifest_filepath: input_graphemes.jsonl
output_file: predicted_phonemes.jsonl
grapheme_field: text_graphemes
pred_field: pred_text
batch_size: 32
num_workers: 4
```

Guidelines:

- T5 G2P and CTC G2P use different configs and tokenizer requirements.
- For CTC G2P, provide the pretrained tokenizer directory and keep punctuation/lowercase settings consistent.
- For sentence-level data, keep context punctuation when the model expects it.
- G2P source scripts are reference-only because they are training/inference-output scripts with Hydra configs and optional ASR/tokenizer dependencies.

## Audio Codec Training

Use caller-owned training code around `AudioCodecModel` and a config contract like:

```yaml
trainer:
  accelerator: gpu
  devices: 1
exp_manager:
  exp_dir: experiments/audio_codec
train_ds_meta:
  my_data:
    manifest_path: train.jsonl
    audio_dir: audio
    sample_weight: 1.0
model:
  sample_rate: 22050
  train_ds:
    dataset_meta: ${train_ds_meta}
  validation_ds:
    dataset_meta: ${val_ds_meta}
```

Checklist:

- Pick config sample rate to match intended Magpie checkpoint: 16 kHz, 22.05 kHz, 24 kHz, or 44.1 kHz.
- Validate segment duration and min/max duration against the config.
- Confirm codebook size and number of codebooks before using the codec with MagpieTTS.
- Treat codec examples/configs as reference-only because training is GPU-heavy, output-heavy, and checkpoint-coupled.

## Evaluation Workflow

A caller-owned Magpie evaluation wrapper should expose these fields:

```yaml
run_evaluation: true
num_repeats: 3
confidence_level: 0.95
sv_model: titanet
asr_model_name: nvidia/parakeet-tdt-1.1b
eou_model_name: facebook/wav2vec2-base-960h
disable_utmosv2: false
disable_fcd: false
cer_target: 0.03
ssim_target: 0.60
violin_plot_metrics: [cer, pred_context_ssim, utmosv2]
```

When dependencies are restricted:

- Disable optional metrics such as UTMOSv2 and FCD.
- Provide local ASR/EoU model paths instead of model IDs if downloads are disallowed.
- Run inference without evaluation first to verify manifest/context/model compatibility.
- Record skipped metrics explicitly in the user's report.

## Safe Output Planning

Before any synthesis or training:

- Ask before overwriting output directories, manifests, or experiment roots.
- Keep generated audio, checkpoints, and metrics outside input data directories.
- For multi-checkpoint Magpie inference, use a separate output root per checkpoint or a naming scheme that includes checkpoint name, temperature, top-k, CFG, prior, and dataset.
- For legacy checkpoint sweeps, record which flags were used per checkpoint: `legacy_codebooks`, `legacy_text_conditioning`, `disable_cas_for_context_text`, forced special-token IDs, and codec path.
- For privacy-sensitive voice cloning, treat context audio and generated samples as user data; avoid uploading or logging to remote services unless explicitly authorized.

## Source Script Handling

The following original source scripts are useful evidence but should remain reference-only in this generated skill:

- Magpie inference script: imports optional ASR/TTS/evaluation stacks, may download models, writes audio/metrics, and is checkpoint/GPU/output-heavy.
- FastPitch and HiFi-GAN training/finetuning scripts: launch long Hydra/PyTorch Lightning training, depend on checkout-relative configs, and write experiment outputs.
- Audio codec training script/configs: GPU-heavy and checkpoint-coupled, with significant generated artifacts.
- G2P train/inference scripts: Hydra/output-producing workflows with tokenizer/model dependencies.
- TTS dataset preprocessing scripts: dataset-download/extract/normalize/supplementary-data workflows with external data and checkout-relative paths.

The bundled `scripts/check_tts_manifest.py` is safe because it is deterministic, read-only, standard-library-only, and does not import NeMo or open audio contents.
