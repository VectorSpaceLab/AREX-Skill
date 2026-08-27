# Installation and Runtime

The web UI demo is a modified text-generation web UI with Nesa-specific model
handlers and settings. The source one-click scripts create a contained Conda
layout, install dependencies, and then launch the UI. Treat those scripts as
mutating installers, not read-only checks.

## Platform flow

| Platform | Source behavior distilled | Guidance |
|---|---|---|
| Linux | Uses a local Miniconda installer if needed, creates an `installer_files/env` Python 3.11 environment, then runs the one-click installer. | Prefer a clean environment. Ask before downloading Miniconda or writing installer directories. |
| macOS | Similar contained Miniconda flow with architecture detection. | Confirm Intel vs Apple Silicon before dependency selection. |
| Windows | Batch wrapper handles contained installer setup. | Use Windows paths and avoid Unix shell assumptions. |

## Backend/vendor choices

The one-click installer asks for a GPU target or reads environment variables:

- NVIDIA: installs a CUDA PyTorch wheel, usually CUDA 12.1 unless an older CUDA
  11.8 path is explicitly chosen.
- AMD: ROCm path on supported Linux/macOS-like setups.
- Apple M-series: Apple-specific requirements.
- Intel Arc: Intel extension/runtime path.
- None: CPU mode and command flags include `--cpu`.

Do not install every backend variant. Choose exactly one backend that matches
the user's hardware and task, or CPU for small demos and documentation work.

## Minimal local web UI import set

For import and settings checks, the prepared inspection environment verified a
CPU stack with packages equivalent to:

```bash
python -m pip install msgspec pydantic-settings python-dotenv nats-py httpx \
  requests tqdm pyyaml safetensors transformers torch gradio accelerate \
  psutil matplotlib markdown numba numpy==1.26.*
```

Full runtime may require additional packages from the platform-specific
requirements files, especially for GPU acceleration or optional loaders. Install
only the selected variant.

## Launch guidance

Before launching:

1. Ensure the environment contains the selected package set.
2. Validate settings and flags with the bundled validator.
3. Confirm model assets are present or network download is approved.
4. Confirm listening host/port and authentication.

If the user wants only a local browser, prefer a localhost binding. If they ask
for LAN or public exposure, require authentication such as a Gradio auth flag or
an auth file.

## Model assets

The web UI supports two key Nesa model workflows:

- encrypted DistilBERT local classification: local model/tokenizer files are
  loaded by a Nesa Hugging Face handler;
- encrypted Llama chat: local tokenizer plus remote Nesa stream endpoint.

For DistilBERT, route to the encrypted-distilbert sub-skill to validate the
local model directory and interpret classification output.

## What not to run by default

Do not run these automatically in an agent session:

- one-click installers that create/download Conda environments;
- full model downloads;
- web UI service launch;
- public Gradio share links or `0.0.0.0` binds without auth;
- GPU stack installs unrelated to the selected backend.

Ask the user first, then run the smallest command that proves the requested
runtime surface.
