# WhisperX backend and environment notes

## Purpose

Read this before choosing CPU/GPU options, installing PyTorch-backed dependencies, or diagnosing runtime prerequisites. WhisperX has a broad CPU-capable API surface, but optional CUDA, pyannote, and Torch Hub paths change the environment needed for real execution.

## Package baseline

- Distribution: `whisperx`
- Import name: `whisperx`
- Project Python range: `>=3.10,<3.14`
- Covered version snapshot: `3.8.7rc1`
- CLI entry point: `whisperx = whisperx.__main__:cli`

## Install guidance

The documented install path is the PyPI package:

```bash
pip install whisperx
```

For editable local inspection while developing against a checkout, use a normal editable install only in a private environment you control:

```bash
python -m pip install -e .
```

Do not install every extra or every requirements file by default. Choose only what the selected workflow needs.

## Backend and prerequisite summary

| Surface | Typical requirement | Notes |
| --- | --- | --- |
| Package import and CLI help | CPU-capable Python environment | Enough for parser/help and static API inspection. |
| ASR transcription | Torch/CTranslate2-backed runtime; CPU or CUDA | CPU works with lower throughput; CUDA uses the installed PyTorch/CTranslate2 stack. |
| `--device cuda` or CUDA Python API paths | Compatible NVIDIA GPU, driver, CUDA-capable torch build, and matching compiled dependencies | Use the selected environment's `torch.cuda.is_available()` and a tiny tensor allocation to verify readiness. |
| `whisperx.load_audio` path loading | `ffmpeg` executable | WhisperX shells out to ffmpeg to decode and resample. |
| Alignment | ASR segments plus wav2vec2 alignment model and NLTK `punkt_tab` data | Some languages use torchaudio defaults, others use Hugging Face model ids. |
| Diarization | pyannote-audio stack and often a Hugging Face read token plus accepted model terms | Speaker assignment itself can run offline once diarization intervals already exist. |
| Silero VAD | Torch Hub cache/network access on first use | The bundled runtime may already favor `pyannote` as the default VAD method. |

## Device and compute defaults

The CLI and ASR loader use the following behavior:

- `--device` defaults to `cuda` only when PyTorch reports CUDA availability; otherwise `cpu`.
- `--compute_type default` becomes `float16` on CUDA and `float32` on CPU.
- `--device cpu --compute_type int8` is the conservative portable CLI fallback.

## Practical checks

- Confirm `ffmpeg -version` works in the same environment as WhisperX.
- Confirm the package imports from the target Python before asking for expensive inference.
- Use the environment's `torch.cuda.is_available()` and a tiny CUDA tensor allocation only when you need to verify a GPU path.
- For cache-only workflows, confirm the selected model snapshots already exist before disabling downloads.

## When to read this reference again

- A user asks whether CPU or GPU is appropriate.
- A transcription or alignment command fails before model inference.
- A model download unexpectedly occurs.
- A GPU command fails due to a PyTorch, CTranslate2, cuDNN, or driver mismatch.
- A diarization request needs a decision about token/model access or a Torch Hub cache policy.
