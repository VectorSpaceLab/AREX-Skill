---
name: audio-music
description: "Routes Lumina text-to-audio and text-to-music demo, config,
  checkpoint, and structure-caption tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Audio and Music

Use this subskill for the audio and music demo branches.
It covers the `demo_audio.py` and `demo_music.py` workflows, the checkpoint-folder requirements, and the structure-caption helper used by the audio path.

## Include here

- Text-to-audio demo launch and config editing.
- Text-to-music demo launch and config editing.
- FlashAttention-backed model imports for the demo stack.
- Checkpoint-folder validation for the audio and music branches.
- The structure-caption helper and its OpenAI / proxy setup.
- Shared `sample_rate`, vocoder, and checkpoint-path troubleshooting.

## Exclude or route elsewhere

- Image generation or conversion: use `image-generation`.
- Image-model training: use `image-training`.
- Visual anagrams: use `visual-anagrams`.
- ImageNet benchmark training: use `imagenet-training`.

## Read first

- `references/workflows.md` for the command patterns and checkpoint tree.
- `references/configuration.md` for the YAML fields that must be edited before a demo run.
- `references/troubleshooting.md` for API-key, checkpoint, and dependency failures.
- `scripts/check_audio_music_inputs.py` before a demo launch if the checkpoint tree is uncertain.

## Fast routing hints

- If the user says `structure caption`, `openai key`, `demo_audio.py`, or `audio_generation`, stay here.
- If the user says `demo_music.py`, `music_generation`, or `vocoder`, stay here.
