---
name: voice-conversion
description: "Use FreeVC voice conversion and TTS-with-VC voice cloning in Coqui
  TTS while preserving source, target, and reference wav semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MPL 2.0
---

# Voice Conversion

Use this sub-skill when a task involves FreeVC, `voice_conversion`, `voice_conversion_to_file`, `tts_with_vc`, `tts_with_vc_to_file`, or the installed `tts` CLI route using `--source_wav` and `--target_wav`.

## Route first

- Direct voice conversion: convert the utterance in `source_wav` so it sounds like the speaker in `target_wav`. Read [references/api-reference.md](references/api-reference.md) and [references/workflows.md](references/workflows.md).
- TTS with voice conversion: synthesize text with a TTS model, then convert the generated speech to the reference speaker in `speaker_wav`. Read [references/workflows.md](references/workflows.md).
- Full installed CLI flag catalogs and server behavior belong in [../server-and-cli/SKILL.md](../server-and-cli/SKILL.md).
- Generic TTS model selection, `tts_to_file`, voice-cloning models that directly consume `speaker_wav`, and model-zoo discovery belong in [../inference-and-model-zoo/SKILL.md](../inference-and-model-zoo/SKILL.md).
- Audio conversion, resampling, duration trimming, and format repair belong in [../vocoder-and-audio-tools/SKILL.md](../vocoder-and-audio-tools/SKILL.md).
- Speaker embedding dataset computation belongs in [../training-config-data/SKILL.md](../training-config-data/SKILL.md).

## Operating rules

1. Use `voice_conversion_models/multilingual/vctk/freevc24` for the released FreeVC route unless the user explicitly selects another compatible local setup.
2. Never swap roles: `source_wav` supplies the spoken content to transform; `target_wav` supplies the target speaker identity. In TTS+VC, `speaker_wav` is the target/reference speaker for the conversion step.
3. Validate paths before model load. Use `scripts/validate_voice_conversion_inputs.py` for no-download checks.
4. Avoid model downloads by default. Use `scripts/convert_voice.py --dry-run` for planning; require `--allow-download` before the helper imports and loads Coqui TTS models.
5. FreeVC reads wav paths through the model audio loader, resampling them to its configured input rate, and saves `*_to_file` outputs at the FreeVC output sample rate. See [references/api-reference.md](references/api-reference.md) for the exact defaults.
6. For install/import/PyTorch/cache issues that are not specific to voice conversion, also check [../../references/troubleshooting.md](../../references/troubleshooting.md). For voice-conversion-specific failures, check [references/troubleshooting.md](references/troubleshooting.md).

## Bundled helpers

From the generated skill tree, run:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/validate_voice_conversion_inputs.py --mode voice-conversion --source-wav source.wav --target-wav target.wav --output-wav converted.wav
python skills/disco/tts/sub-skills/voice-conversion/scripts/convert_voice.py --mode freevc --source-wav source.wav --target-wav target.wav --out-path converted.wav --dry-run
```

Only add `--allow-download` after the user accepts model download/cache/network behavior.
