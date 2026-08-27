# Voice Conversion API Reference

This reference captures the voice-conversion surface that future agents should use without opening repository docs or tests.

## Released FreeVC route

| Item | Value | Notes |
| --- | --- | --- |
| Registry name | `voice_conversion_models/multilingual/vctk/freevc24` | Released voice-conversion model entry for FreeVC. Model loading can download/cache weights. |
| Conversion model family | FreeVC | Voice conversion, not generic text-to-speech. |
| Configured input sample rate | `16000` Hz | Wav path inputs are read by the FreeVC audio loader at this rate. |
| Configured output sample rate | `24000` Hz | `voice_conversion_to_file` and `tts_with_vc_to_file` save with this rate for the released FreeVC config. |
| Main path roles | `source_wav`, `target_wav`, `speaker_wav` | `source_wav` is content to convert; `target_wav`/`speaker_wav` is the voice reference. |

## Python API surface

| Method | Verified signature | Use | Output behavior | Required preconditions |
| --- | --- | --- | --- | --- |
| `TTS.voice_conversion` | `voice_conversion(source_wav, target_wav)` | Convert an existing source recording into the target speaker voice. | Returns waveform samples in memory. | A voice-conversion model such as `voice_conversion_models/multilingual/vctk/freevc24` must already be loaded. Both paths must be valid wav files. |
| `TTS.voice_conversion_to_file` | `voice_conversion_to_file(source_wav, target_wav, file_path="output.wav")` | Same conversion, saved to a wav file. | Calls `voice_conversion`, then writes `file_path` at the loaded FreeVC output sample rate. | Same as above; output parent must be writable. |
| `TTS.tts_with_vc` | `tts_with_vc(text, language=None, speaker_wav=None, speaker=None, split_sentences=True)` | Synthesize text with the loaded TTS model, then convert the temporary TTS wav to the target/reference speaker. | Returns waveform samples in memory. | A TTS model must be loaded. `speaker_wav` must point to the target speaker reference. If no voice converter is loaded, the API lazily loads `voice_conversion_models/multilingual/vctk/freevc24`. |
| `TTS.tts_with_vc_to_file` | `tts_with_vc_to_file(text, language=None, speaker_wav=None, file_path="output.wav", speaker=None, split_sentences=True)` | File-writing route for TTS+VC voice cloning. | Calls `tts_with_vc`, then writes `file_path` at the loaded FreeVC output sample rate. | Same as above; `speaker_wav` is required for the conversion step. |

### Role semantics

| Argument | Meaning | Common mistake | Corrective rule |
| --- | --- | --- | --- |
| `source_wav` | Existing utterance whose words, rhythm, and approximate timing are converted. | Treating it as the desired target speaker sample. | If the user says "make this recording sound like Alice", this recording is `source_wav`. |
| `target_wav` | Audio sample of the speaker identity to imitate for direct FreeVC conversion. | Expecting its transcript/content to appear in the result. | If the user says "use Alice's voice as reference", Alice's sample is `target_wav`. |
| `speaker_wav` in TTS+VC | Target/reference speaker used after the text has been synthesized by a TTS model. | Passing `speaker_wav` to the TTS step and assuming FreeVC will know the target. | For `tts_with_vc*`, `speaker_wav` is the FreeVC target reference. `speaker` and `language` select behavior of the TTS model. |
| `file_path` / `out_path` | Destination wav path. | Reusing an existing path unintentionally. | Validate overwrite intent before running a model. |

## Sample-rate and length behavior

- FreeVC path inputs are loaded at the FreeVC configured input sample rate (`16000` Hz for the released config). This is internal loading behavior, not a replacement for data hygiene.
- The target/reference wav is trimmed for leading/trailing silence before speaker conditioning.
- Saved API outputs use the voice converter output sample rate (`24000` Hz for the released config), not necessarily the original source wav sample rate.
- The generated waveform follows the source utterance length/content more than the target reference length. The target reference supplies speaker identity.
- If a task needs controlled resampling, format conversion, loudness normalization, or batch audio repair, route to [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md).

## Minimal installed CLI route

The installed `tts` console exposes the voice-conversion flags `--source_wav` and `--target_wav`. A minimal FreeVC command shape is:

```bash
tts --model_name voice_conversion_models/multilingual/vctk/freevc24 --source_wav source.wav --target_wav target.wav --out_path converted.wav
```

Use this only after model download/cache behavior is approved. For complete CLI flags, pipe output, device flags, and server details, route to [../../server-and-cli/SKILL.md](../../server-and-cli/SKILL.md).
