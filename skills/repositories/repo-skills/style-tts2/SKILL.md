---
name: style-tts2
description: "Use StyleTTS2 source-checkout workflows for TTS data/config
  preparation, staged CUDA training, fine-tuning, pretrained inference, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# StyleTTS2 repo skill

Use this operating skill when a task involves the StyleTTS2 research repository: text-to-speech training, fine-tuning, pretrained LJSpeech/LibriTTS inference, source-checkout dependency checks, or debugging data/config/checkpoint failures.

## First decision

- Preparing data lists, OOD text, YAML configs, 24 kHz audio roots, or asset paths: read [sub-skills/data-and-config/SKILL.md](sub-skills/data-and-config/SKILL.md).
- Launching first-stage training, second-stage training, fine-tuning, or the one-GPU Accelerate fine-tune path: read [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md).
- Running or troubleshooting pretrained LJSpeech/LibriTTS demos, phonemizer/espeak setup, reference audio, diffusion/style controls, or voice-use cautions: read [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md).

If the request is unclear, start with data/config validation before attempting a training or inference run.

## Repository shape and runtime assumptions

StyleTTS2 is source-checkout research code, not an installable Python distribution. Do not claim that `pip install -e .` works unless packaging metadata has been added after this skill was generated. Use the checkout as the working tree and run the repository launchers through bundled helpers.

Read [references/runtime-overview.md](references/runtime-overview.md) for the distilled repository layout, dependency set, backend expectations, and verified helper APIs. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a different checkout.

## Quick runtime check

Before a task that depends on imports or CUDA, run the bundled safe checker from this skill directory or with an explicit checkout path:

```bash
python scripts/check_runtime.py --repo-root /path/to/StyleTTS2 --check-cuda
```

The checker imports source modules, reports missing hidden dependencies, and can optionally load helper assets without starting training, downloading models, or synthesizing audio.

## Installation notes

The repository README documents:

```bash
pip install -r requirements.txt
```

For local training/inference, also account for runtime imports and demo dependencies discovered from source inspection:

```bash
python -m pip install pandas tensorboard
python -m pip install phonemizer  # inference demos only; also provide espeak-ng or espeak
```

Use a CUDA-enabled PyTorch/Torchaudio build for training and fine-tuning. Inference can run on CPU or CUDA, but CPU is slower.

## Common routes

| Task signal | Route | First safe action |
| --- | --- | --- |
| list row, `root_path`, OOD text, config YAML, missing data | [data-and-config](sub-skills/data-and-config/SKILL.md) | Run `validate_data_lists.py` or `inspect_config.py`. |
| `train_first.py`, `train_second.py`, `train_finetune.py`, checkpoint resume, OOM, NaN | [training](sub-skills/training/SKILL.md) | Run `build_training_command.py` in dry-run mode. |
| LJSpeech/LibriTTS demo, reference audio, phonemizer, `alpha`, `beta`, `diffusion_steps` | [inference](sub-skills/inference/SKILL.md) | Run `check_inference_assets.py`. |
| import failure, CUDA unavailable, missing `pandas`/`tensorboard`, source checkout not importable | [references/troubleshooting.md](references/troubleshooting.md) | Run `scripts/check_runtime.py`. |

## Safety and ethics

Training jobs are long-running CUDA jobs that write checkpoints/logs and may download WavLM through Transformers. Do not start them without explicit user approval. Pretrained voice outputs must be disclosed as synthesized unless the user has voice permission and license rights.

## Router metadata

This skill routes under the speech/audio scenario via [references/repo-routing-metadata.json](references/repo-routing-metadata.json). Do not hand-edit the live repo-skills-router; use the verifier/import helper if the user later asks to import.
