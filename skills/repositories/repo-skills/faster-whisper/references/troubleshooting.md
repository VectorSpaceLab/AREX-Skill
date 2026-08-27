# Cross-cutting Troubleshooting

## Purpose

Use this reference for issues that affect installation, importability, model
resolution, or package-level backend setup before you narrow down to the
transcription sub-skill.

## Install or import failures

Symptoms:

- `ImportError` or `ModuleNotFoundError` for `faster_whisper`.
- Broken dependency resolution during `pip install`.
- `pip check` reports conflicts.

Likely causes:

- The package was not installed in the current environment.
- A different Python interpreter is being used.
- One of the runtime dependencies (`ctranslate2`, `tokenizers`, `onnxruntime`,
  `av`, `huggingface_hub`, `tqdm`) is missing or mismatched.

Recovery:

- Re-run the install command from the current environment.
- Check the active Python and `pip check` in the same environment.
- Use the bundled helper `scripts/check_install.py` to inspect version and model
  alias health.

## CPU vs CUDA confusion

Symptoms:

- A CPU import works, but CUDA transcription still fails.
- A GPU host appears available but `compute_type` or device setup errors occur.

Likely causes:

- The environment has only a CPU wheel or CPU-capable dependencies.
- CUDA libraries, driver/runtime compatibility, or supported CTranslate2 CUDA
  compute types are missing.
- The requested workflow is actually CPU-only, but the command set `device="cuda"`
  or a GPU-only `compute_type`.

Recovery:

- Read [installation-and-backends.md](installation-and-backends.md) first.
- Confirm the package install independently from GPU support.
- Route transcription-specific CUDA troubleshooting to the transcription
  sub-skill's troubleshooting reference.

## Model resolution issues

Symptoms:

- A model alias is unknown.
- `download_model` cannot reach the network or authenticate.
- A local model path is missing required CTranslate2 files.

Likely causes:

- A typo in the model alias.
- The alias has not been cached and the environment is offline.
- A converted model directory is incomplete.

Recovery:

- Read [model-management.md](model-management.md) for supported aliases,
  download behavior, and local path expectations.
- Use `local_files_only=True` only if the model snapshot is already present.
- For conversion workflows, ensure the expected CTranslate2 files are present
  before loading the directory.

## Audio and VAD issues

Symptoms:

- Audio decode fails or returns unexpected results.
- VAD-related errors mention `onnxruntime`.

Likely causes:

- The audio file cannot be decoded by the installed PyAV wheel.
- The package dependencies are incomplete.
- The task actually needs the transcription sub-skill's VAD tuning guidance.

Recovery:

- Verify audio decode with a minimal Python snippet.
- Install the full runtime dependencies from the package metadata.
- If the problem is within transcription logic rather than installation, read the
  transcription sub-skill troubleshooting file.

## When to escalate to the transcription sub-skill

Escalate when the package imports, but the user needs one of these runtime
answers:

- exact transcription code,
- batched inference,
- word timestamps,
- VAD tuning,
- hotwords or prompts,
- clip timestamp behavior,
- stereo channel handling,
- or generator-consumption debugging.

At that point, use
[sub-skills/transcription/SKILL.md](../sub-skills/transcription/SKILL.md) and
its bundled references/scripts.
