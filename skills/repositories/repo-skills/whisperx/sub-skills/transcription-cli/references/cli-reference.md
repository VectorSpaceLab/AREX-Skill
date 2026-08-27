# WhisperX CLI Reference

This reference distills the `whisperx` console entry point and the CLI task behavior for WhisperX `3.8.7rc1`. It is for command construction and diagnostics, not for Python API orchestration.

## Entry point and command shape

- Distribution/package: `whisperx`.
- Import name: `whisperx`.
- Supported Python range from package metadata: `>=3.10,<3.14`.
- Console entry point: `whisperx = whisperx.__main__:cli`.
- Command shape:

```bash
whisperx AUDIO [AUDIO ...] [OPTIONS]
```

`AUDIO` is positional and may contain one or more audio file paths. The CLI decodes each audio file with `ffmpeg`, transcribes all inputs, optionally aligns and diarizes, then writes output files in the selected output directory.

## High-level execution order

The CLI parser builds an argument dictionary and calls `transcribe_task`.

1. Creates `--output_dir` if needed.
2. Normalizes `--language` if provided as either a language code or recognized language name.
3. If `--task translate` is selected, sets `no_align=True` internally because translated English text cannot be forced-aligned against the original-language audio.
4. Rejects word-level subtitle options when alignment is disabled.
5. Loads the ASR model and VAD backend through `load_model(...)`.
6. For each audio path, decodes audio with `ffmpeg`, runs VAD-batched ASR, and keeps the result in memory.
7. Unless alignment is disabled, loads an alignment model and aligns segment text to word/character timestamps.
8. If `--diarize` is set, loads the diarization pipeline and assigns speaker labels.
9. Writes output files with the selected writer.

## Model, backend, and cache flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--model` | `small` | Whisper/faster-whisper model name such as `small`, `base`, `large`, or `large-v2`. English-only models ending in `.en` force English language handling. |
| `--device` | `cuda` when CUDA is available to PyTorch, else `cpu` | Common values are `cuda` and `cpu`; device support still depends on the installed PyTorch/CTranslate2 stack. |
| `--device_index` | `0` | FasterWhisper device index; use when selecting a specific GPU. |
| `--compute_type` | `default`; choices: `default`, `float16`, `float32`, `int8` | In the ASR loader, `default` becomes `float16` on CUDA and `float32` on CPU. For CPU workflows, `int8` is often used to reduce memory. |
| `--batch_size` | `8` | Higher values can improve throughput but increase memory use; reduce on OOM. |
| `--threads` | `0` | If greater than zero, sets Torch CPU threads and passes the same count to FasterWhisper. |
| `--model_dir` | unset; package/cache default | Directory used as the model download/cache root for ASR and alignment; also passed as diarization cache when diarization is enabled. |
| `--model_cache_only` | `False` | When `True`, model loaders use local files only and do not attempt downloads. A missing cache becomes an error. The parser accepts `True` or `False` exactly. |
| `--hf_token` | unset | Passed into ASR model loading and diarization setup. For diarization, it may be required by the selected Hugging Face model and accepted model terms. Prefer `--hf_token $ENVVAR`, not literal token values. |

## Language and task flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--task` | `transcribe`; choices: `transcribe`, `translate` | `translate` produces English translation text and disables alignment internally. Do not combine translation with word-level subtitle flags. |
| `--language` | auto-detect | Accepts supported language codes such as `en`, `de`, `fr`, `it`, `ja`, or recognized language names. Passing a language avoids initial detection overhead and steers language-specific alignment. |
| `--initial_prompt` | unset | Prompt text for the first decoding window. Quote shell-special characters. |
| `--hotwords` | unset | Hint phrases for rare or technical terms. Quote comma-separated or space-containing values. |
| `--suppress_tokens` | `-1` | Comma-separated token IDs. |
| `--suppress_numerals` | `False` | Suppresses numeric/currency symbols during sampling to avoid words that cannot be aligned cleanly. |

### Parser flags with limited effect in this version

The parser accepts `--best_of`, `--condition_on_previous_text`, `--fp16`, and `--segment_resolution`. In the inspected CLI task implementation, these values are not consumed by the main `transcribe_task` path in the same way as the core flags above. Prefer `--compute_type`, `--batch_size`, `--temperature*`, and the consumed writer flags when you need predictable CLI behavior.

## Alignment flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--align_model` | auto | Override the phoneme-level ASR model used for alignment. Route model-selection details to `alignment-timestamps`. |
| `--interpolate_method` | `nearest`; choices: `nearest`, `linear`, `ignore` | Method for assigning timestamps to non-aligned words. |
| `--no_align` | off | Skips forced alignment. Required implicitly by `--task translate`. |
| `--return_char_alignments` | off | Adds character-level alignments to JSON output when alignment runs. |

### Alignment conflicts

The CLI rejects these when alignment is disabled by either `--no_align` or `--task translate`:

- `--highlight_words True`
- `--max_line_width N`
- `--max_line_count N`

`--max_line_count` also has no effect unless `--max_line_width` is set.

## VAD flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--vad_method` | `pyannote`; choices: `pyannote`, `silero` | Selects the VAD backend used inside ASR model loading. |
| `--vad_onset` | `0.500` | Speech onset threshold; reduce if speech is missed. Must be between 0 and 1. |
| `--vad_offset` | `0.363` | Speech offset threshold; reduce if speech segments end too early. |
| `--chunk_size` | `30` | Maximum chunk duration in seconds for merging VAD speech segments. Reduce if chunks become too long or memory is tight. |

Backend notes:

- `pyannote` VAD uses the packaged WhisperX VAD model asset and does not use the diarization token path.
- `silero` VAD loads `snakers4/silero-vad` through Torch Hub. It may require network access on first use unless already cached.

## Diarization flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--diarize` | off | Runs speaker diarization after ASR/alignment and assigns speaker labels. |
| `--min_speakers` / `--max_speakers` | unset | Optional constraints when the number of speakers is known. |
| `--diarize_model` | `pyannote/speaker-diarization-community-1` | Speaker diarization model name. Model access may require accepted terms and a Hugging Face token. |
| `--speaker_embeddings` | off | Includes speaker embeddings in JSON only when `--diarize` is also enabled; otherwise the CLI warns that it has no effect. |
| `--hf_token` | unset | Required for many diarization setups. Use an environment variable expansion and never expose the token value. |

Detailed diarization setup and token/model-term handling belongs in `diarization-speakers`.

## Output and logging flags

| CLI flag | Default / choices | Notes |
| --- | --- | --- |
| `--output_dir`, `-o` | `.` | Directory for output files. The real CLI creates it. The bundled command builder does not. |
| `--output_format`, `-f` | `all`; choices: `all`, `srt`, `vtt`, `txt`, `tsv`, `json`, `aud` | `all` uses the standard text/subtitle/TSV/JSON writers; use `aud` explicitly for Audacity labels. Output schemas are owned by `outputs-subtitles`. |
| `--highlight_words` | `False` | For SRT/VTT word highlighting. Requires alignment and parser value `True` or `False`. |
| `--max_line_width` | unset | Subtitle line-width control. Requires alignment. |
| `--max_line_count` | unset | Maximum subtitle lines per segment; only meaningful with `--max_line_width`. Requires alignment. |
| `--verbose` | `True` | Parser value must be exactly `True` or `False`. If no `--log-level` is given, `True` sets info logging and `False` sets warning logging. |
| `--log-level` | unset; choices: `debug`, `info`, `warning`, `error`, `critical` | Overrides `--verbose`. |
| `--print_progress` | `False` | Prints progress in transcribe/align loops. Parser value must be exactly `True` or `False`. |
| `--version`, `-V` | n/a | Prints WhisperX version and exits. |
| `--python-version`, `-P` | n/a | Prints Python runtime version and exits. |

## Safe command-building checklist

Before providing a command for a user to run:

1. Ask whether downloads/network access are allowed. If not, include `--model_cache_only True` and a known model cache directory, and warn that a cache miss fails.
2. Choose `--device cpu --compute_type int8` for conservative CPU command construction.
3. Choose `--device cuda --compute_type float16` only when the environment has compatible CUDA/PyTorch/CTranslate2 libraries and enough VRAM.
4. Avoid `--highlight_words`, `--max_line_width`, and `--max_line_count` when `--no_align` or `--task translate` is used.
5. For diarization, include `--diarize` and pass `--hf_token $ENVVAR` only through an environment variable placeholder.
6. If the user needs exact output file schemas or subtitle rendering, route to `outputs-subtitles`.
