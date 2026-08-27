---
name: clearvoice-inference
description: "Operate pretrained ClearVoice inference for speech enhancement,
  speech separation, speech super-resolution, and audio-visual target speaker
  extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ClearVoice Inference

Use this sub-skill when the user wants pretrained ClearVoice inference only.

## Route away
- Send SpeechScore or other objective metrics to the sibling `speechscore-metrics` sub-skill.
- Send training, fine-tuning, config editing, or data generation to the sibling `training-and-data-prep` sub-skill.

## Use it for
- Choosing a ClearVoice `task` and compatible `model_names`.
- File, directory, and `.scp` inference with pretrained checkpoints.
- NumPy/Tensor input mode for audio-only models.
- Output writing, checkpoint download behavior, FFmpeg/media-codec checks, and no-download validation.
- Supported tasks: `speech_enhancement`, `speech_separation`, `speech_super_resolution`, and `target_speaker_extraction`.

## Read or run
- [references/api-reference.md](references/api-reference.md) when you need the `ClearVoice` constructor, call, and `write()` signatures or the tensor/file-mode limits.
- [references/model-catalog.md](references/model-catalog.md) when you need to match a task to the right pretrained model, rate, or checkpoint family.
- [references/workflows.md](references/workflows.md) when you need an end-to-end file, directory, `.scp`, or NumPy workflow and want a safe no-download path first.
- [references/troubleshooting.md](references/troubleshooting.md) when inference fails because of unsupported task/model pairs, missing FFmpeg, checkpoint download problems, output conflicts, sample-rate mismatch, or slow CPU fallback.
- [scripts/clearvoice_inference_recipe.py](scripts/clearvoice_inference_recipe.py) when you want a safe CLI recipe that can list models, validate task/model pairs, and run file-mode inference without loading weights in `--dry-run`.
- [scripts/clearvoice_numpy_recipe.py](scripts/clearvoice_numpy_recipe.py) when you want to validate NumPy/Tensor shapes or run a single-model tensor call with `--run`.

## Important rules
- Pass `model_names` as a list, even for one model.
- Use exactly one model in tensor-to-tensor mode.
- Use video input plus `online_write=True` for AV target speaker extraction.
