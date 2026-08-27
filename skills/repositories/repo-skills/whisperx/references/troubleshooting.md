# WhisperX troubleshooting

## Purpose

Use this cross-cutting reference for install, import, ffmpeg, CUDA/cuDNN, cache-only, token, and other runtime failures that appear across WhisperX workflows.

## Fast triage

1. Reproduce with the smallest command or helper script that still fails.
2. Check the target environment's Python, `whisperx` import, and `python -m whisperx --help`.
3. Decide whether the failure is about CLI parsing, audio decoding, model caches, CUDA readiness, diarization credentials, alignment model selection, or output formatting.
4. If the issue is specific to one workflow, route to the matching sub-skill after resolving the generic environment problem.

## Import or install problems

Symptoms:
- `ModuleNotFoundError: whisperx`
- `ImportError` from `torch`, `torchaudio`, `faster_whisper`, or `pyannote`
- `python -m whisperx --help` fails before showing usage

Likely causes:
- The package is not installed in the active environment.
- The environment Python is not the one used to install WhisperX.
- A compiled dependency is missing or incompatible with the selected Python/backend.

Recovery:
- Re-run the bundled environment check script from the target environment.
- Confirm the package version and importability before running real inference.
- Recreate the environment if compiled dependencies are inconsistent.

## ffmpeg or audio decode problems

Symptoms:
- `Failed to load audio: ...`
- `ffmpeg` not found
- A specific MP3/WAV/M4A/other codec fails immediately

Likely cause:
- WhisperX loads file audio by calling `ffmpeg` and resampling to mono 16 kHz.

Recovery:
- Verify `ffmpeg -version` in the same environment.
- Try a tiny known-good WAV file.
- Convert unusual containers/codecs before calling WhisperX.
- Use `scripts/check_whisperx_environment.py` or the ASR helper script to isolate the issue.

## Model cache and download issues

Symptoms:
- Unexpected model downloads
- `local files only` / cache miss errors
- Alignment or diarization model not found

Likely causes:
- `--model_cache_only True` or `local_files_only=True` was used without a populated cache.
- The ASR model was cached but the alignment or diarization model was not.
- A model id or language-specific default is not available for the selected setup.

Recovery:
- If downloads are allowed, rerun without cache-only settings so the cache can populate.
- If offline is required, confirm the ASR, alignment, and diarization models are already cached.
- For raw transcription only, disable alignment when word timestamps are not required.

## CUDA / cuDNN / compute-type issues

Symptoms:
- CUDA initialization failure
- `compute_type` rejected
- cuDNN load/version mismatch
- A GPU command works in the CLI but fails in Python, or vice versa

Likely causes:
- The torch/CTranslate2/CUDA/cuDNN stack is inconsistent.
- A GPU runtime is unavailable or incompatible with the selected wheel.
- The user selected `float16` or a GPU device when only CPU is valid.

Recovery:
- Prefer a CPU fallback when the task does not require GPU verification.
- For a true GPU path, verify `torch.cuda.is_available()` and a tiny tensor allocation.
- Remove conflicting CUDA/cuDNN paths from the process environment if runtime libraries conflict.
- Keep generic CUDA stack repair outside the WhisperX repo skill if the problem is really a framework installation issue.

## Diarization token or model-access issues

Symptoms:
- `--diarize` warns that no token was provided
- Authentication, 401/403, or gated-model messages appear
- Diarization fails late after ASR/alignment already ran

Likely causes:
- The selected pyannote model needs a Hugging Face token and accepted model terms.
- The token exists but is not available to the command or Python process.

Recovery:
- Ask whether the user has a read token and has accepted the selected model terms.
- Use an environment-variable placeholder, not a pasted token value.
- If token access is unavailable, remove `--diarize` and route speaker-label work to the diarization sub-skill for offline post-processing.

## Alignment and timestamp failures

Symptoms:
- Missing word timestamps
- `Unsupported language`
- `No default align-model for language`
- NLTK `punkt_tab` download errors
- Digits, decimals, currency, or mixed-symbol words have no timestamps

Recovery:
- Route language/model selection to `alignment-timestamps`.
- Confirm the selected language has a default alignment model or choose a supported custom wav2vec2 model.
- Install the NLTK `punkt_tab` resource when real sentence splitting is required.
- Use the alignment regression helper script to distinguish a model issue from a timestamp-interpolation issue.

## Output and subtitle failures

Symptoms:
- JSON validation fails before writing files
- Word highlighting is missing
- Subtitle line wrapping behaves unexpectedly
- Speaker labels do not appear in rendered files

Recovery:
- Route result-shape and writer issues to `outputs-subtitles`.
- Validate the transcript JSON before writing.
- Remember that word-level subtitle highlighting needs alignment-derived `words[].start` and `words[].end`.
- `--max_line_count` only matters when `--max_line_width` is set.

## Safe helper scripts

- [`scripts/check_whisperx_environment.py`](../scripts/check_whisperx_environment.py) — baseline import, CLI, ffmpeg, and optional CUDA visibility checks.
- Sub-skill helpers — use the matching sub-skill scripts for command construction, API inspection, alignment regression, diarization CSV assignment, or subtitle rendering.
