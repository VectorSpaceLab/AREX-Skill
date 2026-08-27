# Installation and Extras

## When to read

Read this before installing or diagnosing Ludwig dependencies, optional integrations, GPU support, or service backends.

## Baseline install

Current Ludwig releases require Python 3.12+. Start with the smallest install that matches the workflow:

```bash
pip install ludwig
python -c "import ludwig; print(ludwig.__version__)"
ludwig --help
```

For a local checkout, use an isolated environment and install editable only when developing or inspecting that checkout:

```bash
python -m pip install -e .
```

Do not install every optional extra by default. Select extras by workflow.

## Optional dependency groups

| Need | Install direction | Notes |
| --- | --- | --- |
| FastAPI local server | `ludwig[serve]` | Adds FastAPI/uvicorn/httpx/python-multipart/prometheus metrics support. |
| Ray backend, Ray Data, Ray Serve, distributed HPO | `ludwig[distributed]` | Requires Ray-compatible Python/platform and often more memory. |
| Hyperopt executors/search libraries | `ludwig[hyperopt]` or focused libraries | The CLI help can load without every executor, but actual searches need their executor packages. |
| LLM/PEFT workflows | `ludwig[llm]` plus compatible torch/CUDA as needed | Large models may also need Hugging Face credentials, local cache space, GPU VRAM, and quantization backends. |
| Visualization | `ludwig[viz]` | Adds plotting libraries for visualizations. |
| Explainability | `ludwig[explain]` | Adds Captum-dependent explanations. |
| Benchmarking | `ludwig[benchmarking]` | S3 and benchmark helpers; avoid for ordinary use. |
| Everything | `ludwig[full]` | Convenient but heavy; prefer narrower extras for agents. |

## Backend decisions

- CPU is enough for config validation, schema export, CLI help, tiny synthetic data creation, small tabular smoke checks, and most API signature inspection.
- CUDA/GPU is practically required for many LLM/VLM fine-tuning, quantized generation, and vLLM-style serving tasks. Verify `torch.cuda.is_available()` and memory before planning these.
- Ray/distributed backends are separate from GPU availability. A visible GPU does not prove Ray, Dask, KServe, vLLM, MLflow, or Hub upload workflows are installed.
- External datasets and Hub/model provider operations may require network and credentials. Do not silently run them.

## Minimal verification checklist

```bash
python scripts/check_env.py --check-cli
python scripts/check_env.py --check-optional
```

If a task needs GPU evidence:

```bash
python scripts/check_env.py --check-cuda
```

A passing import/help check does not prove large training, Ray cluster operation, provider APIs, dataset downloads, server listeners, or model uploads. Run those only when the user asks and prerequisites are explicit.
