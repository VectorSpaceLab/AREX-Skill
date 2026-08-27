# WhisperX CLI Workflows

These recipes are self-contained command patterns for future agents. They use placeholder relative paths such as `audio.wav`, `transcripts/`, and `model-cache/`; replace them with user-provided paths. Commands may download models, load credentials, decode audio with `ffmpeg`, and write output files unless you explicitly use the safe builder or cache-only flags.

## Use the safe builder for planning

The bundled builder only prints a shell-quoted command; it does not run WhisperX, inspect files, read tokens, download models, or create directories.

```bash
python scripts/build_whisperx_command.py --audio audio.wav
```

Example output:

```bash
whisperx audio.wav
```

Use it when you need deterministic command assembly or want to catch obvious conflicts before handing a command to a user.

## Basic transcription

Default model (`small`), automatic device default from PyTorch, default VAD, alignment on, all standard outputs in the current directory:

```bash
whisperx audio.wav
```

More explicit command that writes JSON only:

```bash
whisperx audio.wav --model small --output_dir transcripts --output_format json
```

## Conservative CPU command

Use CPU with int8 computation when the user wants portability or is on a machine without CUDA:

```bash
whisperx audio.wav --device cpu --compute_type int8 --batch_size 4 --output_dir transcripts --output_format json
```

If memory is still tight, reduce `--batch_size` further or use a smaller `--model` such as `base`.

## CPU offline/cache-only command construction

Use this pattern when downloads are not allowed and models are expected to already be cached:

```bash
python scripts/build_whisperx_command.py \
  --audio audio.wav \
  --model small \
  --device cpu \
  --compute-type int8 \
  --batch-size 4 \
  --language en \
  --output-dir transcripts \
  --output-format json \
  --model-dir model-cache \
  --model-cache-only
```

Expected printed command:

```bash
whisperx audio.wav --model small --device cpu --compute_type int8 --batch_size 4 --language en --output_dir transcripts --output_format json --model_dir model-cache --model_cache_only True
```

Cache-only means the ASR model, alignment model if alignment is enabled, and diarization model if diarization is enabled must already be available in the chosen cache locations. If only raw transcription is needed and no alignment model is cached, add `--no_align` and avoid word-level subtitle flags.

## CUDA/GPU transcription

Use GPU only when the environment has compatible CUDA, PyTorch, CTranslate2, and enough VRAM:

```bash
whisperx audio.wav --model large-v2 --device cuda --compute_type float16 --batch_size 16 --output_dir transcripts --output_format all
```

If GPU memory is low:

```bash
whisperx audio.wav --model large-v2 --device cuda --compute_type int8 --batch_size 4 --output_dir transcripts
```

Also consider a smaller model such as `base` or `small`.

## Word-highlighted subtitles

Word highlighting requires alignment. Do not combine this with `--no_align` or `--task translate`.

```bash
whisperx audio.wav --model large-v2 --highlight_words True --output_format srt --output_dir subtitles
```

For line wrapping:

```bash
whisperx audio.wav --model large-v2 --output_format vtt --max_line_width 42 --max_line_count 2 --output_dir subtitles
```

Detailed subtitle schemas and rendering behavior belong in `outputs-subtitles`.

## Disable alignment for speed or missing alignment models

Use `--no_align` when the user only needs segment-level transcription, wants to avoid alignment model downloads, or is translating:

```bash
whisperx audio.wav --model small --no_align --output_format json --output_dir transcripts
```

Invalid combination:

```bash
whisperx audio.wav --no_align --highlight_words True
```

Fix by either removing `--no_align` so alignment can run, or removing word-level options.

## Translate to English

Translation disables alignment in the CLI task implementation. Avoid word-level subtitle flags.

```bash
whisperx audio_es.wav --model large-v2 --language es --task translate --no_align --output_format txt --output_dir translations
```

`--no_align` is redundant for translation but makes the intended behavior explicit.

## Multilingual transcription

Passing `--language` avoids initial language detection and selects language-aware alignment behavior. For non-English ASR, use a multilingual model such as `large` or `large-v2`.

```bash
whisperx audio_de.wav --model large-v2 --language de --output_dir transcripts
whisperx audio_fr.wav --model large --language fr --output_dir transcripts
whisperx audio_it.wav --model large --language it --output_dir transcripts
whisperx audio_ja.wav --model large --language ja --output_dir transcripts
```

If the language has no suitable default alignment model or the alignment model is not cached, use `--no_align` or route to `alignment-timestamps` for custom alignment model guidance.

## VAD selection and tuning

Default Pyannote VAD:

```bash
whisperx audio.wav --vad_method pyannote --vad_onset 0.500 --vad_offset 0.363 --chunk_size 30
```

Silero VAD alternative:

```bash
whisperx audio.wav --vad_method silero --vad_onset 0.500 --chunk_size 30
```

Tuning tips:

- Lower `--vad_onset` if speech is missed.
- Lower `--vad_offset` if speech segments are cut off too early.
- Reduce `--chunk_size` if chunks are too long or memory use is high.
- `silero` may trigger Torch Hub cache/network behavior on first use.

## Diarization from the CLI

Diarization runs after ASR/alignment and can require a Hugging Face access token plus accepted model terms. Use an environment variable placeholder; never paste token values into a saved command.

```bash
python scripts/build_whisperx_command.py \
  --audio meeting.wav \
  --model large-v2 \
  --device cuda \
  --compute-type float16 \
  --diarize \
  --hf-token-env HF_TOKEN \
  --output-dir diarized \
  --output-format json
```

Expected token-safe portion of the printed command:

```bash
--diarize --hf_token $HF_TOKEN
```

When speaker count is known, add constraints to the final command manually or with direct CLI flags:

```bash
whisperx meeting.wav --diarize --hf_token $HF_TOKEN --min_speakers 2 --max_speakers 2 --output_format json --output_dir diarized
```

For model access, token scope, accepted terms, speaker embeddings, and assignment details, route to `diarization-speakers`.

## Logging and progress

- Use `--log-level info` or `--log-level debug` when collecting diagnostic output.
- Use `--verbose False` to suppress info logging when no explicit log level is provided.
- Use `--print_progress True` for progress messages in transcribe/align loops.

```bash
whisperx audio.wav --log-level info --print_progress True
```

## Pre-run validation checklist

Before running a real command, verify:

1. `whisperx --version` works in the target environment.
2. `ffmpeg -version` works and can decode the user audio format.
3. Model downloads/network access are allowed, or cache-only mode has all required models.
4. CUDA commands are only used on a compatible GPU stack; otherwise switch to CPU/int8.
5. Diarization commands have a token environment variable set and model terms accepted.
6. Output directory choice is safe and non-destructive for the user's context.
