# Runtime Setup

Read this when installing, launching, or diagnosing H2O LLM Studio before choosing a sub-skill-specific workflow.

## Runtime model

H2O LLM Studio is a GPU-oriented application plus CLI trainer. The most reliable runtime is either:

1. A source-layout H2O LLM Studio runtime root containing the package and runtime assets (`llm_studio/`, `prompts/`, `model_cards/`, `static/`, `pyproject.toml`), installed with the repo's Python 3.10 dependency set; or
2. The published Docker image, with NVIDIA container runtime and a mounted workdir.

Treat it as more than a pure importable library. Some config/app paths discover prompt templates, model-card templates, icons, and package metadata from files relative to the process working directory.

## Python and dependencies

From a source-layout runtime root, the documented setup command is:

```bash
make setup
```

This uses `uv sync --frozen --no-dev` and then applies repo-maintained patches. Install optional `flash-attn` only when that backend is intentionally selected and compatible.

- Package metadata pins Python `==3.10.*`.
- The base dependency set includes PyTorch/Transformers, PEFT, bitsandbytes, DeepSpeed, H2O Wave, datasets, pyarrow, pandas, scikit-learn, OpenAI, W&B, H2O Drive, S3/Azure connectors, and Hugging Face tooling.
- Optional `flash-attn` is behind the `flash` extra and should not be installed unless the user intentionally needs that attention backend and has compatible CUDA/toolchain resources.
- The repo's `uv.lock` and `Makefile` define the documented source-layout install path. Avoid broad dev/browser dependencies unless tests or UI automation are explicitly requested.

## GUI launch options

Use the app sub-skill for full detail, but the documented commands are:

```bash
make llmstudio
```

or a direct Wave launch from the runtime root:

```bash
H2O_WAVE_MAX_REQUEST_SIZE=25MB \
H2O_WAVE_NO_LOG=true \
H2O_WAVE_PRIVATE_DIR="/download/@output/download" \
wave run llm_studio.app
```

`make llmstudio` probes `nvidia-smi` first and is intended for GPU-capable hosts. The direct Wave command is useful for app import and server routing checks, but it does not prove training readiness.

## CLI launch options

Use `configuration-and-data` to prepare a YAML config, then `training-and-experiments` to run or debug it. The trainer accepts `-Y/--yaml` and a deprecated `-C/--config`. Dynamic overrides use config sections and fields, for example `--training.epochs 1`.

For multi-GPU runs, prefer the bundled distributed wrapper in the training sub-skill to construct a validated dry-run command before execution.

## Docker launch shape

The documented Docker flow uses NVIDIA runtime, a large shared-memory segment, port `10101`, and a mounted workdir:

```bash
docker run --runtime=nvidia --shm-size=64g --init --rm -it \
  -p 10101:10101 \
  -v "$PWD/llmstudio_mnt:/mount" \
  h2oairelease/h2oai-llmstudio-app:latest
```

Do not recommend Docker host changes, NVIDIA container runtime installation, or public port exposure without user approval.

## Backend expectations

- Real fine-tuning is NVIDIA-GPU oriented; 24GB+ GPU memory is recommended for larger models.
- CPU tiny configs can validate mechanics but are not proof of production training performance.
- PyTorch CUDA availability and DeepSpeed toolkit readiness are separate. DeepSpeed may need `CUDA_HOME` pointing to a CUDA toolkit with `nvcc` even when `torch.cuda.is_available()` is true.
- DeepSpeed, bitsandbytes, int4/int8, flash attention, and large-model downloads are backend-specific. Verify each before claiming support.

## Safe preflight

Use the root checker first:

```bash
python scripts/check_environment.py --runtime-root . --check-cuda --check-config-assets
```

The checker imports modules, checks runtime assets, optionally probes CUDA, and reports likely next steps. It does not start Wave, train, download, upload, or mutate datasets.
