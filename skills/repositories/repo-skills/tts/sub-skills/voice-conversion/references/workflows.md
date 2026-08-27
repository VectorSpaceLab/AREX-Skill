# Voice Conversion Workflows

Start every workflow with path validation and an explicit download/cache decision. The bundled helpers validate and dry-run without importing Coqui TTS or downloading models.

## Choose the route

| User intent | Route | Required inputs | Route elsewhere when |
| --- | --- | --- | --- |
| "Convert this recording to sound like that speaker." | Direct FreeVC voice conversion | `source_wav`, `target_wav`, output wav path | The user needs audio format repair or resampling first: [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |
| "Use a single-speaker TTS model but clone a reference voice." | TTS+VC | text, TTS model name, `speaker_wav`, output wav path; `language`/`speaker` only if the TTS model requires them | The selected TTS model itself supports direct `speaker_wav` cloning and the user is not asking for FreeVC: [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md). |
| "Build a command-line voice conversion call." | Installed `tts` CLI with `--source_wav`/`--target_wav` | model name, `source_wav`, `target_wav`, `--out_path` | Full CLI catalog, server, or device flag details: [../../server-and-cli/SKILL.md](../../server-and-cli/SKILL.md). |
| "Prepare speaker embeddings for a dataset." | Not this sub-skill | dataset metadata and encoder plan | Route to [../../training-config-data/SKILL.md](../../training-config-data/SKILL.md). |

## Workflow A: no-download validation

1. Identify roles in plain language before using flags:
   - `source_wav`: the recording to transform.
   - `target_wav`: the target speaker reference for direct FreeVC.
   - `speaker_wav`: the target speaker reference for TTS+VC.
2. Validate direct FreeVC inputs:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/validate_voice_conversion_inputs.py --mode voice-conversion --source-wav source.wav --target-wav target.wav --output-wav converted.wav
```

3. Validate TTS+VC inputs:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/validate_voice_conversion_inputs.py --mode tts-with-vc --speaker-wav target-speaker.wav --output-wav cloned.wav
```

4. If validation reports format or sample-rate warnings, either accept FreeVC's internal wav loading behavior or route audio repair to [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md).

## Workflow B: direct FreeVC conversion through the bundled helper

1. Dry-run first:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/convert_voice.py --mode freevc --source-wav source.wav --target-wav target.wav --out-path converted.wav --dry-run
```

2. Confirm that the user accepts model download/cache/network behavior for `voice_conversion_models/multilingual/vctk/freevc24`.
3. Run with explicit approval:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/convert_voice.py --mode freevc --source-wav source.wav --target-wav target.wav --out-path converted.wav --allow-download
```

4. If CUDA is available and approved, add `--device cuda`; otherwise default CPU works but may be slow.
5. Add `--allow-overwrite` only when replacing the output file is intentional.

## Workflow C: TTS with on-the-fly FreeVC

Use this when a user has a TTS model that does not directly clone the target voice, or explicitly wants the TTS+VC route.

1. Choose the TTS model using [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md). Keep generic `tts_to_file` details there.
2. Validate the target/reference wav:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/validate_voice_conversion_inputs.py --mode tts-with-vc --speaker-wav target-speaker.wav --output-wav cloned.wav
```

3. Dry-run the combined route:

```bash
python skills/disco/tts/sub-skills/voice-conversion/scripts/convert_voice.py --mode tts-with-vc --tts-model-name tts_models/de/thorsten/tacotron2-DDC --text "Example text." --speaker-wav target-speaker.wav --out-path cloned.wav --dry-run
```

4. After explicit model-download approval, run with `--allow-download`. Add `--language` or `--speaker` only when the selected TTS model requires those IDs.
5. Expect the API to synthesize a temporary source wav from text, then convert that temporary wav to the `speaker_wav` voice using FreeVC. The generated text comes from `--text`; the target/reference wav's transcript is not used.

## Workflow D: installed CLI voice conversion

The minimal installed CLI route is:

```bash
tts --model_name voice_conversion_models/multilingual/vctk/freevc24 --source_wav source.wav --target_wav target.wav --out_path converted.wav
```

Rules for future agents:

- Always pass a voice-conversion model name. If omitted, the installed CLI defaults to a TTS model, which is the wrong route for `--source_wav`/`--target_wav` conversion.
- Validate source and target paths before invoking the CLI.
- Treat this as a model-loading command that may use the network/cache. Do not run it until the user has approved downloads.
- For device, progress-bar, pipe output, model-info, list-model, and server options, route to [../../server-and-cli/SKILL.md](../../server-and-cli/SKILL.md).
