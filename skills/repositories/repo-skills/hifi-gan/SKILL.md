---
name: "hifi-gan"
description: "Routes HiFi-GAN training, fine-tuning, waveform inference, and
  checkpoint/config troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# HiFi-GAN

HiFi-GAN is a speech vocoder repository with two user-facing workflows:
training/fine-tuning from LJSpeech-style data and inference from trained
generator checkpoints.

## Use this skill for

- choosing between `config_v1.json`, `config_v2.json`, and `config_v3.json`
- training or fine-tuning HiFi-GAN with the repository's data layout
- wav-to-wav inference or mel-to-wav inference from generator checkpoints
- checkpoint/config pairing, output layout, and filename conventions
- CUDA, TensorBoard, librosa, mel-channel, and data-layout troubleshooting
- quick smoke checks with bundled helpers before expensive runs
- self-contained bundled runtime source/configs when the original checkout is not available

## Do not use this skill for

- ASR, diarization, forced alignment, upstream text-to-mel generation,
  or other speech tasks that are not HiFi-GAN vocoder training/inference
- unrelated audio repos or generic deep-learning engines

## Read first

- `references/model-overview.md`
- `references/configuration.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md`
- `scripts/hifigan_runtime/` for copied core source and bundled configs
- `sub-skills/training/SKILL.md`
- `sub-skills/inference/SKILL.md`

## Route map

- `training` — launch or resume training, fine-tuning, dataset/filelist
  preparation, checkpoint and TensorBoard behavior, and DDP/CUDA
  troubleshooting.
- `inference` — synthesize wavs from wav or mel inputs, pair checkpoints with
  configs, and handle output directories and smoke checks.

## Shared facts

- The generator consumes 80 mel channels and emits one waveform channel.
- The bundled configs keep `num_mels = 80`, `sampling_rate = 22050`, and
  `hop_size = 256`.
- The runtime skill includes copied HiFi-GAN source under
  `scripts/hifigan_runtime/`, including `train.py`, `inference.py`,
  `inference_e2e.py`, `models.py`, `meldataset.py`, `env.py`, `utils.py`,
  `LICENSE`, and bundled V1/V2/V3 configs.
- Use `sub-skills/training/scripts/train_hifigan.py` as the self-contained
  training/fine-tuning entrypoint.
- Use `sub-skills/inference/scripts/infer_hifigan.py` as the self-contained
  wav/mel inference entrypoint.
- Training writes `config.json` into the checkpoint directory and saves
  generator checkpoints as `g_########`.
- Inference reads `config.json` from the checkpoint directory and writes
  `_generated.wav` or `_generated_e2e.wav` files.
- The bundled smoke helpers create tiny synthetic fixtures only; they are for
  wiring checks, not quality evaluation.

## Safe setup

- Use a Python environment that can import `torch`, `librosa`, `scipy`,
  `tensorboard`, and `matplotlib`.
- Prefer the sub-skill smoke helpers before long GPU runs or after dependency
  changes.
- Do not require an external source checkout for core HiFi-GAN code; the
  generated skill bundles the needed runtime source and configs.
- Keep the input directory clean: the bundled inference entrypoint ultimately
  runs code that iterates `os.listdir(...)` directly.
- Keep training filelists basename-only in the first column; do not append
  `.wav`.

## Handoff pattern

1. Start at this root skill to choose the right route.
2. If the request is about training or fine-tuning, open
   `sub-skills/training/SKILL.md`.
3. If the request is about generation, open `sub-skills/inference/SKILL.md`.
4. If the request involves model/config details or failure analysis, read the
   shared `references/` files first.
