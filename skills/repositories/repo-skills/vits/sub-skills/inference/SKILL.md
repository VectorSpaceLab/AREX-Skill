---
name: inference
description: "Routes VITS text-to-speech synthesis and voice-conversion tasks
  from checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this route when you need to synthesize speech from a checkpoint or run voice conversion with a VITS model.

## Use this route when

- You have a checkpoint and want generated audio.
- You need to choose synthesis settings such as noise scale, length scale, or speaker id.
- You need the LJ Speech single-speaker inference path or the VCTK multi-speaker path.
- You need voice conversion from a source audio file or spectrogram to a target speaker.
- You need to troubleshoot checkpoint mismatches, sample-rate mismatches, or speaker-id problems.

## Do not use this route when

- You are preparing filelists or building the extension; use `data-preparation`.
- You are launching training or resuming checkpoints; use `training`.
- You only need a quick environment sanity check; use `../../scripts/check_install.py` or `../../scripts/model_smoke.py`.

## Read first

- `../../references/workflows.md` for the synthesis and voice-conversion command flow.
- `../../references/configuration.md` for the config and file-layout differences.
- `../../references/api-reference.md` for `SynthesizerTrn.infer` and `voice_conversion`.
- `../../references/troubleshooting.md` for cross-cutting failures.
- `references/troubleshooting.md` in this sub-skill for checkpoint and speaker-id failures.

## Bundled helpers

- `../../scripts/synthesize.py` — run TTS or voice conversion from a checkpoint.
- `../../scripts/model_smoke.py` — validate inference and voice-conversion wiring on synthetic inputs.
- `../../scripts/check_install.py` — confirm the repo imports and the backend is ready.

## Common workflow

1. Confirm the checkpoint matches the config family.
2. Build the monotonic-alignment extension and verify CUDA.
3. For TTS, provide text and speaker id when the config is multi-speaker.
4. For voice conversion, provide source audio and both source and target speaker ids.
5. Use `model_smoke.py` when you need to check the model path without a real checkpoint.

## Ownership boundaries

- Include checkpoint-driven TTS, voice conversion, and audio-output planning here.
- Exclude dataset cleanup and training launch; route those to sibling sub-skills.
