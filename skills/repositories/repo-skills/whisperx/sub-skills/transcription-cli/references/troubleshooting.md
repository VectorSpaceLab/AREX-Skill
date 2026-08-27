# WhisperX CLI Troubleshooting

Use this reference when a `whisperx` command fails, hangs on setup, triggers unexpected downloads, or combines incompatible options.

## Quick triage

1. Reproduce with the smallest command that still fails.
2. Add `--log-level info` or `--log-level debug` for parser/runtime logs.
3. Check whether the command is supposed to run online or offline/cache-only.
4. Check whether the command needs CUDA, a Hugging Face token, or a specific model cache.
5. If the failure is about output file schemas or subtitle rendering, route to `outputs-subtitles` after resolving CLI option validity.

## ffmpeg missing or audio decode failure

Symptoms:

- Error resembles `Failed to load audio: ...`.
- `ffmpeg` command not found.
- Decode errors for a particular codec/container.

Likely cause:

- WhisperX CLI decodes audio by launching `ffmpeg` and down-mixing/resampling to mono 16 kHz. Missing or incompatible `ffmpeg` prevents transcription before model inference is useful.

Recovery:

1. Ask the user to run `ffmpeg -version` in the same environment where they run `whisperx`.
2. Try a tiny known-good WAV/MP3 file to distinguish install failure from corrupt input.
3. Convert unusual containers/codecs outside WhisperX before retrying.
4. Keep `--log-level info` enabled while diagnosing.

## Model downloads, offline mode, and cache-only misses

Symptoms:

- Command tries to access the network unexpectedly.
- Cache-only command fails to find model files.
- Error mentions local files only, missing model snapshots, or unavailable alignment/diarization models.

Likely cause:

- `--model_cache_only True` prevents downloads but requires all needed models to already be cached.
- `--model_dir` controls the ASR/alignment download/cache root and is also passed as diarization cache when diarization is enabled.
- Alignment and diarization can require additional models beyond the ASR model.

Recovery:

1. If network is allowed, remove `--model_cache_only True` for the first run so required models can populate the cache.
2. If offline is required, confirm the cache contains the selected ASR model and, unless `--no_align` is used, the alignment model for the selected/detected language.
3. If diarization is enabled, confirm the diarization model is cached and token/model-term requirements have already been satisfied.
4. For raw offline transcription only, add `--no_align --output_format json` and avoid word-level subtitle flags.

## CUDA or compute type mismatch

Symptoms:

- CUDA initialization fails.
- CTranslate2/PyTorch rejects the selected `compute_type`.
- Errors mention fp16 unsupported on CPU, cuDNN loading, or GPU libraries not found.

Likely cause:

- `--compute_type default` maps to `float16` on CUDA and `float32` on CPU.
- CPU environments usually need `--device cpu` and often work best with `--compute_type int8` or `float32`.
- CUDA commands require compatible NVIDIA driver, CUDA runtime, PyTorch, CTranslate2, and cuDNN libraries.

Recovery:

1. For a portable fallback, rerun with:

```bash
whisperx audio.wav --device cpu --compute_type int8 --batch_size 4
```

2. For GPU, verify the target environment can import PyTorch and report CUDA availability before running the long transcription.
3. If an error says cuDNN cannot be loaded or the runtime cuDNN version conflicts with the PyTorch build, remove conflicting CUDA/cuDNN paths from the process environment or point the dynamic linker at the cuDNN library that matches the installed PyTorch package. Avoid hard-coded paths in reusable guidance; use the user's actual package environment.
4. If GPU remains blocked, switch to CPU/int8 or ask the user to fix the CUDA stack before promising GPU throughput.

## Out of memory or very slow execution

Symptoms:

- CUDA OOM.
- Process killed by the OS.
- Transcription is much slower than expected.

Likely cause:

- Model too large, batch size too high, chunks too long, or compute type too memory-intensive.

Recovery:

1. Reduce batch size: `--batch_size 4`, then `--batch_size 1` if necessary.
2. Use a smaller model: `--model base` or `--model small`.
3. Use lighter compute: `--compute_type int8`.
4. Reduce VAD chunk length: `--chunk_size 15`.
5. Disable optional steps for diagnostics: `--no_align` and omit `--diarize`.

## `--no_align` with word-level subtitle flags

Symptoms:

- Parser error resembles `--highlight_words not possible with --no_align`, `--max_line_count not possible with --no_align`, or `--max_line_width not possible with --no_align`.
- The user asks for word highlighting while also disabling alignment.

Likely cause:

- Word-level subtitles need alignment timestamps. The CLI explicitly rejects these options when alignment is disabled. `--task translate` also disables alignment internally.

Recovery:

- If word-level SRT/VTT output is required, remove `--no_align`, use `--task transcribe`, and ensure the alignment model is available.
- If speed/offline/translation is more important, keep `--no_align` or `--task translate` and remove `--highlight_words`, `--max_line_width`, and `--max_line_count`.
- The safe builder catches this conflict before printing a command.

## Missing Hugging Face token with `--diarize`

Symptoms:

- CLI warns that no `--hf_token` was provided.
- Diarization model load fails with authentication, gated repository, or model-terms errors.

Likely cause:

- The default diarization model may require a Hugging Face access token and accepted model terms. Diarization runs after ASR/alignment, so a long command can fail late if credentials are missing.

Recovery:

1. Ask the user to set a token environment variable in their shell, for example `HF_TOKEN`, without sending the value to the agent.
2. Construct commands using `--hf_token $HF_TOKEN`, not a literal token.
3. Confirm the user has accepted the selected diarization model's terms.
4. If credentials cannot be provided, remove `--diarize` and route speaker-label needs to `diarization-speakers` for offline alternatives or post-processing constraints.

## Silero VAD network/cache behavior

Symptoms:

- `--vad_method silero` tries to contact Torch Hub.
- Errors mention `snakers4/silero-vad`, Torch Hub, trust/cache, or missing cached repository.

Likely cause:

- Silero VAD is loaded through Torch Hub. First use may require network access unless the model repository is already cached.

Recovery:

1. If network access is allowed, allow the first run to populate the Torch Hub cache.
2. If offline, either pre-populate the Torch Hub cache or switch to the default `--vad_method pyannote`.
3. Keep `--vad_onset` between 0 and 1 and reduce `--chunk_size` if segments become too long.

## Unsupported language or alignment model failure

Symptoms:

- `Unsupported language` errors.
- Alignment model cannot be found or downloaded.
- Word timestamps are missing for some languages or tokens.

Likely cause:

- The CLI accepts a defined set of language codes/names. Alignment requires a language-specific phoneme ASR model, and not every language/model/cache combination is available.

Recovery:

1. Use a known language code such as `en`, `de`, `fr`, `it`, `ja`, or another supported code.
2. If transcription is enough, add `--no_align`.
3. If word timestamps are required, route custom alignment model selection and limitations to `alignment-timestamps`.
