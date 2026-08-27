# MiniMind-V Installation and Environment

## Purpose

Use this reference before installing dependencies, checking hardware, or deciding whether a MiniMind-V workflow can run. It summarizes environment facts without relying on the source checkout used to create this skill.

## Repository shape

MiniMind-V is a script-style Python repository. It does not expose `pyproject.toml`, `setup.py`, console entry points, or an installable distribution name. Future agents usually work from a MiniMind-V checkout and run project scripts directly.

Important import packages and script areas:

- `model/`: MiniMind language model, VLM wrapper, tokenizer assets, and SigLIP2 placement notes.
- `dataset/`: ALLaVA-style parquet dataset loader and optional eval images.
- `trainer/`: Pretrain/SFT scripts and checkpoint utilities.
- `eval_vlm.py`: command-line image QA generation.
- `scripts/`: conversion and optional WebUI scripts.

## Dependency policy

The repository requirements include many data, web, and experiment packages. Install only what the selected workflow needs:

- Data validation and dataset loading: `datasets`, `pyarrow`, `Pillow`, `numpy`.
- Model/API/inference/training: `torch`, `transformers`, `Pillow`, tokenizer resources, SigLIP2 resources.
- WebUI: `gradio` and related web packages in addition to model/inference dependencies.
- Experiment logging: `swanlab`/W&B-compatible tooling only when the user enables logging.

`torch` and `torchvision` are commented in the requirements file. Choose backend wheels separately for the host CPU/CUDA/ROCm/MPS environment. Do not blindly install all optional web/training/logging dependencies when the task is only static inspection or parquet validation.

## Backend expectations

- Training and practical inference are GPU-oriented. A CPU-only environment can inspect APIs, validate parquet, and sometimes run tiny slow checks, but it is not proof of performance or training feasibility.
- The documented quick reproduction assumes a CUDA-capable PyTorch stack, with training examples written for CUDA/DDP and bfloat16/float16 autocast on CUDA.
- WebUI and command-line generation can be planned without a GPU, but full model loading may be slow or memory-heavy on CPU.
- Full training should be treated as expensive and requires explicit user approval.

## Required resources by workflow

| Workflow | Required local resources |
| --- | --- |
| Static API inspection | A MiniMind-V checkout and Python deps sufficient to import `model.model_vlm` and `model.model_minimind`; no weights required. |
| Parquet validation | A parquet file with `conversations` and `image_bytes`; `pyarrow`; Pillow for image-byte decode checks. |
| Native `.pth` inference | tokenizer files under `model/`, SigLIP2 under `model/siglip2-base-p32-256-ve/`, an `out/*_768[_moe].pth` checkpoint, image files, torch/transformers/Pillow. |
| Transformers inference/WebUI | a Transformers-format checkpoint directory, tokenizer/config/weights, trusted custom code or `auto_map`, SigLIP2 resource, torch/transformers/Pillow; Gradio for WebUI. |
| Pretrain/SFT | tokenizer files, SigLIP2, base or previous-stage `out/*.pth` weight, parquet data, CUDA-capable torch recommended, sufficient GPU memory/storage. |
| Export conversion | source model classes, tokenizer files, native `.pth` checkpoint, SigLIP2 path for initialization, torch/transformers. |

## Safe preflight helper

Run the repo-level helper from any current working directory:

```bash
python path/to/check_minimind_v_environment.py --repo-root . --workflow data
python path/to/check_minimind_v_environment.py --repo-root . --workflow inference-native --weight sft_vlm --hidden-size 768
python path/to/check_minimind_v_environment.py --repo-root . --workflow training-sft --use-moe 0
```

The helper checks relative files/directories and import availability. It does not download resources, load model weights, train, serve, or run generation.

## Environment troubleshooting pattern

1. Classify the user's workflow and install only the relevant dependency subset.
2. Check resource paths before importing/loading heavy models.
3. If torch backend is missing or incompatible, fix the torch installation separately from MiniMind-V requirements.
4. If a command would download models/data, ask for explicit approval and name the target relative directory.
5. If a command would launch training or a server, ask for explicit approval and state device/listener implications.
