# Installation and Commands

## Package facts

- Public package name: `llamafactory`.
- Version in source metadata: `0.9.6.dev0`.
- Python requirement: Python `>=3.11` from project metadata.
- CLI entry points: `llamafactory-cli` and `lmf`, both mapped to `llamafactory.cli:main`.
- Default architecture: v0. Set `USE_V1=1` only when intentionally using experimental v1 routes.

## Install modes

For source installs, use an isolated Python environment and install the package from the repository root:

```bash
pip install -e .
```

The core project metadata includes web/API operational dependencies such as `gradio`, `fastapi`, `uvicorn`, `sse-starlette`, `matplotlib`, `torch`, `transformers`, `datasets`, `accelerate`, `peft`, and `trl`. Metrics and distributed/backend extras may still require separate requirements files or backend-specific installs.

For `uv` users, `uv run llamafactory-cli webui` can create/use an isolated runtime from the project context. If dependency resolution is slow or platform-specific packages fail, install PyTorch first using the wheel index for the target accelerator, then install LLaMA Factory.

Docker images are useful when local accelerator stacks are hard to reproduce. CUDA Docker operation typically needs Docker, Docker Compose if using compose, NVIDIA Container Toolkit, compatible host drivers, `--gpus all`, and `--ipc=host`. Expose `7860` for Gradio Web UI and `8000` for API workflows when needed.

## CLI route map

`llamafactory-cli help` prints the user-facing route summary. `lmf` is a shortcut for the same CLI.

| Route | Purpose | Notes |
| --- | --- | --- |
| `llamafactory-cli webui` | Launch full LlamaBoard | Training, eval/predict, chat, export tabs. Requires `gradio`. |
| `llamafactory-cli webchat` | Launch pure web chat UI | Uses the Web UI chat engine only. Requires `gradio`. |
| `llamafactory-cli env` | Print environment facts | Imports core packages and prints package versions, accelerator info, git commit when available, and whether `data/` exists in the current directory. |
| `llamafactory-cli version` | Print welcome/version banner | Uses source version `0.9.6.dev0` for this checkout. |
| `llamafactory-cli help` | Print usage | Safe static route discovery. |
| `llamafactory-cli api` | Launch OpenAI-style API server | Route details belong to `inference-and-serving`. |
| `llamafactory-cli chat` | Launch CLI chat | Route details belong to `inference-and-serving`. |
| `llamafactory-cli train` | Run training | Route details belong to `training-and-configs`. |
| `llamafactory-cli export` | Merge/export model | Route details belong to `model-loading-and-export`. |

`eval` exists in the v0 launcher but raises `NotImplementedError` because evaluation is being deprecated as a direct CLI route.

## Safe sanity checks

Run the bundled script before trying heavyweight UI/model commands:

```bash
python sub-skills/webui-and-ops/scripts/llamafactory_sanity_check.py
```

The script checks the Python version, installed package metadata, importability, CLI binaries, and optional web/API dependencies. It does not import model weights, start servers, install packages, or read private environment paths.

If dependencies are complete, follow with:

```bash
llamafactory-cli help
llamafactory-cli version
llamafactory-cli env
```

`env` imports several ML packages, so use `help` or the sanity script first when diagnosing partial installs.
