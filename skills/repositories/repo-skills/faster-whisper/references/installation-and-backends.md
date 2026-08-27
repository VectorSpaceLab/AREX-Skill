# Installation and Backends

## Purpose

Read this when installing `faster-whisper`, choosing a supported Python
version, or deciding whether CPU-only or CUDA-backed transcription is the right
runtime for a task.

## Verified package facts

- Distribution name: `faster-whisper`
- Import name: `faster_whisper`
- Verified package version: `1.2.1`
- Supported Python from metadata: `>=3.9`
- Runtime dependencies from packaging metadata:
  - `ctranslate2>=4.0,<5`
  - `huggingface_hub>=0.23`
  - `tokenizers>=0.13,<1`
  - `onnxruntime>=1.14,<2`
  - `av>=11`
  - `tqdm`
- Optional extras in the source checkout:
  - `conversion`: `transformers[torch]>=4.23`
  - `dev`: black, flake8, isort, pytest pins used by CI

## Installation

Public install command:

```bash
pip install faster-whisper
```

Editable install from a checkout:

```bash
pip install -e .
```

If a future task needs the local package for development, editable mode is fine.
For a normal user workflow, prefer the public wheel install above.

## Environment setup guidance

- Python 3.11 is a safe inspection default and is compatible with the verified
  package metadata.
- `conda` is a good choice for compiled dependencies and CUDA-adjacent
  inspection because the package depends on `ctranslate2`, `tokenizers`, PyAV,
  and ONNX Runtime.
- Do not treat a CPU import check as evidence for CUDA. CUDA support is optional
  acceleration, not a guarantee of the package install itself.
- The package does not require a system `ffmpeg` binary for normal audio decode;
  `decode_audio` uses PyAV, which bundles FFmpeg libraries in the wheel.

## Backend choices

### CPU

Recommended baseline when you only need ordinary transcription or when GPU
libraries are unavailable.

Typical runtime shape:

```python
WhisperModel("tiny", device="cpu", compute_type="int8")
```

Useful CPU `compute_type` values observed from CTranslate2 support in the
inspection environment include `float32`, `int8`, and `int8_float32`.

### CUDA

Use CUDA only when the host has compatible NVIDIA hardware and runtime
libraries.

The repository README documents NVIDIA cuBLAS and cuDNN requirements for CUDA
execution. The inspection environment confirmed that the host has NVIDIA A100
GPUs and that installed CTranslate2 reports CUDA compute types, but a full GPU
transcription run was intentionally deferred.

Typical runtime shape:

```python
WhisperModel("tiny", device="cuda", compute_type="float16")
```

CUDA compute types reported by the inspected `ctranslate2` build included:
`bfloat16`, `float16`, `float32`, `int8`, `int8_bfloat16`, `int8_float16`, and
`int8_float32`.

### ONNX Runtime for VAD

VAD uses the bundled Silero ONNX asset and `onnxruntime` on CPU. If the VAD path
fails, check `onnxruntime` first rather than CUDA.

## Minimal environment check

Run the bundled helper in the generated skill tree:

```bash
python scripts/check_install.py
```

That helper verifies importability, version, model aliases, CTranslate2 compute
support, and VAD availability from the active environment.

## What this reference does not claim

- It does not prove full GPU inference from installation alone.
- It does not cover benchmark packages or the conversion extra as a required
  runtime dependency.
- It does not replace root or sub-skill troubleshooting for transcription or
  model-management errors.
