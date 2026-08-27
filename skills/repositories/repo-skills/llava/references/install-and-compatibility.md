# Install and Compatibility Reference

## When to read

Read this when setting up LLaVA, debugging imports, deciding whether CUDA is required, or explaining why an apparently successful install is not enough to validate generation, training, or benchmark inference.

## Package baseline

The package distribution is `llava` and the import root is `llava`. The baseline package metadata used for this skill declared:

- Python: `>=3.8`; Python 3.10 is a safe choice for the pinned ML stack.
- Core pins: `torch==2.1.2`, `torchvision==0.16.2`, `transformers==4.37.2`, `tokenizers==0.15.1`, `sentencepiece==0.1.99`, `accelerate==0.21.0`, `scikit-learn==1.2.2`, `gradio==4.16.0`, `gradio_client==0.8.1`, `httpx==0.24.0`, `einops==0.6.1`, `einops-exts==0.0.4`, `timm==0.6.13`, plus `peft`, `bitsandbytes`, `pydantic`, `markdown2[all]`, `numpy`, `requests`, `uvicorn`, and `fastapi`.
- Training extra: `.[train]` adds `deepspeed==0.12.6`, `ninja`, and `wandb`.
- Build extra: `.[build]` is only for package publishing tools and is not needed for operation.

## Installation sketches

Editable source checkout:

```bash
conda create -n llava python=3.10 -y
conda activate llava
pip install --upgrade pip
pip install -e .
```

Training-enabled checkout:

```bash
pip install -e ".[train]"
# Optional only when the host/compiler/CUDA stack supports it:
# pip install flash-attn --no-build-isolation
```

If installing from a package index or VCS archive, pin a revision/version that matches the provenance baseline before copying command flags from this skill.

## Backend coverage

| Workflow | Minimum safe check | Backend truth |
| --- | --- | --- |
| Import and CLI help | CPU is enough | Does not prove model generation or GPU memory |
| Single-image generation | CUDA or supported MPS/CPU fallback explicitly chosen | The baseline Linux workflow assumes CUDA; large checkpoints may require high VRAM |
| Model worker and Gradio UI | CPU can inspect parser; CUDA validates worker generation | The UI alone may start without a worker, but no model answer can be produced until a worker loads a checkpoint |
| Training/fine-tuning | CUDA import smoke plus DeepSpeed import | Full training requires GPU memory, datasets, checkpoints, and long runtime |
| Benchmark inference | CUDA plus benchmark data/checkpoint | CPU validation can only check JSONL schemas and converters |
| Submission conversion | CPU is enough | Does not validate model accuracy |

## Optional compatibility surfaces

- **Quantization**: `--load-4bit` and `--load-8bit` depend on bitsandbytes and are primarily Linux/CUDA workflows. macOS and Windows docs say quantization is not supported there.
- **MPS**: macOS supports limited 16-bit inference through `--device mps`; do not claim 4-bit/8-bit support on macOS.
- **Windows**: Windows support is limited; WSL2 is preferred for complete Linux-like workflows.
- **Intel**: Intel dGPU/CPU support is documented on a separate branch and uses Intel Extension for PyTorch; it was not part of the verified baseline.
- **SGLang**: SGLang serving is an optional high-throughput backend; install `sglang[all]` separately and use a running SGLang endpoint before launching the LLaVA SGLang worker.
- **OpenAI/GPT judging**: GPT-review scripts require an OpenAI-compatible package, credentials, and network access; treat them as credential-bound optional evaluation.

## Version conflict warning

The package metadata leaves `peft` unpinned while pinning `accelerate==0.21.0` and `transformers==4.37.2`. If a fresh resolver installs a much newer PEFT release, training imports can fail because newer PEFT expects newer Accelerate utilities. Prefer preserving the repo-pinned stack and choose a PEFT version compatible with it instead of blindly upgrading Accelerate, Transformers, or Torch.

## Quick diagnostic

Use the root diagnostic helper:

```bash
python scripts/check_install.py --require-cuda
```

A pass means imports, metadata, and optional CUDA visibility were checked. It does not download a model, start a server, run a benchmark, or perform training.
