# Installation and Runtime Preparation

Baichuan2 is not installed as a local Python package. Prepare a Python environment for the workflow you need, then use the bundled helpers or Hugging Face model-loading snippets.

## Prerequisites

- Python 3.10 or 3.11 is safest for the ML stack.
- A CUDA-capable PyTorch install is required for the primary Chat demos, quantization, and fine-tuning workflows.
- Hugging Face access or a local model directory is required to load Baichuan2 weights.
- Use `trust_remote_code=True` when loading official Baichuan2 checkpoints.

## Dependency sets by workflow

| Workflow | Required packages | Optional / conditional packages |
| --- | --- | --- |
| Inference, CLI, web, API | `torch`, `transformers`, `accelerate`, `sentencepiece`, `colorama`, `flask`, `streamlit` | none for the bundled helpers beyond the selected UI/server package. |
| Quantization / memory reduction | `torch`, `transformers`, `bitsandbytes` | CUDA-compatible BitsAndBytes is needed for GPU quantization. |
| Fine-tuning / LoRA / DeepSpeed | `torch`, `transformers`, `accelerate`, `sentencepiece`, `deepspeed`, `peft` | `xformers` only if the user wants that training acceleration path. |
| CPU deployment | `torch`, `transformers`, `sentencepiece` | No BitsAndBytes or DeepSpeed required. |

The repository's raw requirement files include additional packages such as `cpm_kernels`, `transformers_stream_generator`, and `xformers`. The distilled workflows do not require the first two directly, and `xformers` is optional training acceleration. Install them only when a chosen runtime path or user environment specifically needs them.

## Example all-workflow install

Choose the PyTorch command that matches the host driver and CUDA policy. A CUDA wheel command usually looks like this pattern:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
python -m pip install transformers accelerate sentencepiece colorama flask streamlit deepspeed peft bitsandbytes
```

For CPU-only deployment, use a CPU PyTorch wheel and omit CUDA-specific packages such as BitsAndBytes unless they are needed elsewhere.

## Check the environment without loading weights

```bash
python scripts/check_baichuan2_env.py --workflow inference
python scripts/check_baichuan2_env.py --workflow deployment --require-cuda --check-bitsandbytes-op
python scripts/check_baichuan2_env.py --workflow fine-tuning --require-cuda
```

These checks import packages, report versions, and optionally verify CUDA/BitsAndBytes, but they do not download 7B/13B model weights.

## Route-specific next checks

- Inference: run the helper `--dry-run` command in `sub-skills/inference/scripts/` before loading a model.
- Deployment: run `sub-skills/deployment/scripts/quantize_model.py --dry-run --validate-imports` before quantizing.
- Fine-tuning: run `sub-skills/fine-tuning/scripts/validate_training_data.py` and `sub-skills/fine-tuning/scripts/train_supervised.py --dry_run True` before launching DeepSpeed.
