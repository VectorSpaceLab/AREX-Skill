# `tts` CLI Reference

This reference distills the installed Coqui TTS `tts` entry point for version `0.22.0`. Use it to compose commands, not to inspect repository scripts.

## Low-side-effect commands

| Task | Command | Side effects |
| --- | --- | --- |
| Show parser/help | `tts --help` | No synthesis or model download. |
| List released registry entries | `tts --list_models` | Reads bundled registry; no checkpoint download. |
| Query model metadata by full name | `tts --model_info_by_name tts_models/en/ljspeech/tacotron2-DDC` | Reads registry; no checkpoint download. |
| Query model metadata by index | `tts --model_info_by_idx tts_models/3` | Reads registry; no checkpoint download. |

If a user ran only `tts`, or only supplied model-selection flags without `--text`, `--list_models`, `--model_info_by_*`, `--list_speaker_idxs`, `--list_language_idxs`, `--reference_wav`, `--source_wav`, or `--target_wav`, this version prints help and exits instead of synthesizing. Diagnose that as a missing action flag, not as successful inference.

## Model-name grammar

Use names exactly as printed by `tts --list_models`.

| Registry family | Full-name pattern | Notes |
| --- | --- | --- |
| TTS model | `tts_models/<language>/<dataset>/<model_name>` | Required for `--model_name` when loading released TTS models. Some older examples omit the `tts_models/` prefix; prefer the full listed name. |
| Vocoder model | `vocoder_models/<language>/<dataset>/<model_name>` | Use with `--vocoder_name`; not every vocoder is compatible with every TTS model. |
| Voice conversion model | `voice_conversion_models/<language>/<dataset>/<model_name>` | Use with `--model_name` plus `--source_wav` and `--target_wav`. |
| Metadata by index | `<family>/<index>` such as `tts_models/3` | Indexes come from `--list_models` output and can change with package version. |

Fairseq TTS entries use the same TTS-family grammar, for example `tts_models/<lang-iso-code>/fairseq/vits`.

## Core flags

| Flag | Use | Validation before running |
| --- | --- | --- |
| `--text TEXT` | Text to synthesize. | Required for TTS synthesis. If omitted outside list/info/speaker-language/VC modes, the command prints help. |
| `--out_path PATH` | WAV output path; default is `tts_output.wav`. | Ensure parent directory exists and the path will not overwrite important audio. |
| `--model_name NAME` | Released TTS or voice-conversion model. Defaults to `tts_models/en/ljspeech/tacotron2-DDC` when no custom model is supplied. | Full listed name; released model loading can download checkpoints. |
| `--vocoder_name NAME` | Released vocoder model. If omitted for many released TTS models, the model's default vocoder is used. | Full listed vocoder name; verify compatibility with the TTS model. |
| `--config_path PATH` + `--model_path PATH` | Custom TTS config/checkpoint. | Supply both. Check file existence and that config matches checkpoint architecture. |
| `--vocoder_path PATH` + `--vocoder_config_path PATH` | Custom vocoder checkpoint/config. | Supply both when using a custom vocoder. Check mel/audio compatibility. |
| `--encoder_path PATH` + `--encoder_config_path PATH` | Speaker encoder checkpoint/config for models that need it. | Supply both and confirm model expects a speaker encoder. |
| `--device DEVICE` | Device string such as `cpu`, `cuda`, or `cuda:0`. | Prefer this over legacy `--use_cuda`; check backend availability first. |
| `--use_cuda True` | Legacy CUDA switch. | If set true, it overrides `--device` to `cuda`; avoid mixing both unless that override is intended. |
| `--progress_bar True|False` | Download/progress display. | Use `False` for cleaner logs in automation. |

## Speaker, language, and reference flags

| Flag | Use | Notes |
| --- | --- | --- |
| `--speakers_file_path PATH` | Custom speakers JSON for custom multi-speaker models. | Pair with custom model/config and `--speaker_idx` when required. |
| `--language_ids_file_path PATH` | Custom language-id JSON for custom multilingual models. | Pair with custom model/config and `--language_idx` when required. |
| `--speaker_idx ID` | Select a known speaker id. | Use `--list_speaker_idxs` first for released or custom multi-speaker models. |
| `--language_idx ID` | Select a known language id. | Use `--list_language_idxs` first for multilingual models. |
| `--speaker_wav WAV [WAV ...]` | Reference wav(s) for voice cloning or speaker-encoder conditioning. | Multiple paths are accepted; the embedding is averaged. Validate paths and audio format before running. |
| `--reference_wav WAV` | Reference wav to convert in the voice of `--speaker_idx` or `--speaker_wav`. | Advanced synthesis route; confirm the target model supports it. |
| `--reference_speaker_idx ID` | Speaker id for `--reference_wav`. | Use only with compatible models. |
| `--gst_style VALUE` | GST style reference. | Model-specific; not a generic voice-cloning flag. |
| `--capacitron_style_wav WAV` / `--capacitron_style_text TEXT` | Capacitron prosody reference and transcription. | Model-specific; validate support first. |
| `--voice_dir DIR` | Voice directory for Tortoise models. | Tortoise-specific cache/voice reference location. |

Multi-speaker models can stop with a clear message if neither `--speaker_idx` nor `--speaker_wav` is provided. Multilingual voice-cloning models usually need both a speaker reference and a language id; see [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md) for model-specific API behavior.

## Query speaker and language ids

These commands load the selected model and may download checkpoints before printing ids.

```bash
tts --model_name tts_models/<language>/<dataset>/<model_name> --list_speaker_idxs
tts --model_name tts_models/<language>/<dataset>/<model_name> --list_language_idxs
```

Use them after approving network/cache/disk side effects. They are not equivalent to registry-only metadata queries.

## Synthesis command patterns

Released single-speaker model with default vocoder:

```bash
tts --text 'Text for TTS' \
  --model_name tts_models/en/ljspeech/tacotron2-DDC \
  --out_path output.wav \
  --device cpu
```

Released model with explicit vocoder:

```bash
tts --text 'Text for TTS' \
  --model_name tts_models/en/ljspeech/glow-tts \
  --vocoder_name vocoder_models/en/ljspeech/hifigan_v2 \
  --out_path output.wav \
  --device cpu
```

Multispeaker or multilingual voice-cloning-style command:

```bash
tts --text 'Hello from a cloned speaker.' \
  --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
  --speaker_wav ref_a.wav ref_b.wav \
  --language_idx en \
  --out_path output.wav \
  --device cuda
```

Custom TTS checkpoint with Griffin-Lim fallback:

```bash
tts --text 'Text for a custom checkpoint.' \
  --model_path model.pth \
  --config_path config.json \
  --out_path output.wav \
  --device cpu
```

Custom TTS checkpoint with custom vocoder:

```bash
tts --text 'Text for a custom checkpoint.' \
  --model_path model.pth \
  --config_path config.json \
  --vocoder_path vocoder.pth \
  --vocoder_config_path vocoder_config.json \
  --out_path output.wav \
  --device cpu
```

## Voice-conversion CLI flags

For a released FreeVC-style model, the CLI uses `--model_name`, `--source_wav`, `--target_wav`, and `--out_path`:

```bash
tts --model_name voice_conversion_models/multilingual/vctk/freevc24 \
  --source_wav source.wav \
  --target_wav target_reference.wav \
  --out_path converted.wav \
  --device cuda
```

Treat `source_wav` as the audio to transform and `target_wav` as the reference voice target. For deeper FreeVC semantics and Python alternatives, use [../../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md).

## Pipe output

`--pipe_out` writes WAV bytes to stdout for shell pipelines while also using `--out_path` as the output filename. Keep logs and raw bytes separate:

```bash
tts --text 'Pipe this audio.' \
  --model_name tts_models/en/ljspeech/tacotron2-DDC \
  --out_path piped.wav \
  --pipe_out \
  --device cpu > piped.stdout.wav
```

Avoid mixing `--pipe_out` with tools that expect text logs on stdout. If a downstream audio player reads from stdin, keep stderr available for diagnostics.

## Bundled command helpers

- Use [../scripts/check_tts_cli.py](../scripts/check_tts_cli.py) to confirm the installed `tts` command exposes the expected help, registry, and model-info paths without synthesis.
- Use [../scripts/build_tts_command.py](../scripts/build_tts_command.py) to generate shell-quoted commands and catch missing text, missing speaker/language references, custom checkpoint path pairs, wrong model-name grammar, and accidental download assumptions.

## Source-script bundling decision

The installed `tts` entry point is wrapped instead of copied. The public CLI already owns model loading and registry behavior; the bundled scripts in this sub-skill add safe validation and no-synthesis checks around that entry point. Direct copies of the upstream command implementation are intentionally excluded because they would duplicate loader logic, drift from the installed package, and encourage future agents to run source-tree scripts instead of the installed console command.
