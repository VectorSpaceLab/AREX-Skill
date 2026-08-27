# Install And Backend Notes

Use this reference before advising installation or environment changes for Unsloth Core, the `unsloth` CLI, or Unsloth Studio.

## Interfaces

- **Unsloth Core** is the code-first Python API exposed by `unsloth`, including `FastLanguageModel`, `FastModel`, `FastVisionModel`, `FastSentenceTransformer`, trainer classes, chat templates, and save helpers.
- **Unsloth CLI** is the `unsloth` console script from package metadata. It wraps training, inference, chat, export/list-checkpoints, Studio commands, and connect subcommands.
- **Unsloth Studio** is the local web/API runtime packaged under `studio` and controlled by `unsloth studio` / `unsloth run`.

## Public Install Choices

- For code-first Core usage, prefer public package install guidance from the current Unsloth docs and choose a backend-compatible install variant for the user's OS/GPU/Python.
- For Studio users, the README documents public installer commands for macOS/Linux/WSL and Windows plus `unsloth studio -p 8888` launch.
- Use a virtual environment or isolated package manager environment. Do not install or upgrade heavy ML packages in a user's base environment without explicit approval.
- Treat editable installs from the repository as maintainer/developer workflows, not as the default advice for ordinary users.

## Backend Decision Points

- `torch` is required for the GPU Core path. Missing torch raises an import-time Unsloth error before model loading.
- `unsloth_zoo` is required by the GPU path and supplies many compatibility patches and backend utilities.
- `bitsandbytes` enables 4-bit QLoRA workflows; without it, 4-bit paths can fail or be unavailable even when 16-bit/full finetuning remains possible.
- `triton`, `xformers`, `flash-attn`, and backend-specific extras are optional acceleration surfaces. Install only when the chosen workflow and hardware need them.
- MLX behavior is selected on Apple Silicon when MLX and compatible `unsloth_zoo` modules are available; non-Apple or forced GPU paths use the GPU initialization branch.
- Studio can run CPU/GGUF/chat/data-recipe paths in cases where Core training requires a stronger GPU stack.

## Safe Import Checks

- `import unsloth` has side effects: it patches training libraries and may probe CUDA, `bitsandbytes`, `vllm`, `torchvision`, cache paths, and compatibility shims.
- Import Unsloth before `transformers`, `trl`, or `peft` in scripts to avoid the import-order warning and ensure Unsloth optimizations apply.
- For a non-invasive preflight, run the root `scripts/check_unsloth_environment.py` helper or the relevant sub-skill checker before importing model loaders in user code.
- A successful package install is not enough. Verify `pip check`, package metadata, root import, CLI help, and backend availability for the selected workflow.

## Hardware Notes

- NVIDIA CUDA users should match PyTorch/CUDA wheels to driver support and GPU architecture. `nvidia-smi` showing a CUDA version means the driver can support that runtime level; it does not mean a toolkit is installed.
- Newer GPUs and compiled extensions often require newer wheels. Avoid source builds such as `flash-attn` unless the user explicitly accepts compiler/time/RAM risk.
- macOS Apple Silicon users should distinguish Studio/MLX-supported paths from CUDA-specific Core examples.
- AMD/ROCm and Intel paths require their documented backend variants; do not suggest generic CUDA wheels for those machines.

## Studio-Specific Install Notes

- `UNSLOTH_STUDIO_HOME` selects an isolated Studio root for venv, auth/database, cache, outputs, exports, and local llama.cpp state. Keep it consistent between setup and launch.
- Installer and uninstaller scripts mutate the user's machine and can fetch network resources. Ask before running them.
- `unsloth studio --secure` is safer for remote access than raw host binding because the raw server remains on loopback and the Cloudflare tunnel fails closed.
- `unsloth studio -H 0.0.0.0` exposes the raw server to the network; warn about API keys and server-side tools.
