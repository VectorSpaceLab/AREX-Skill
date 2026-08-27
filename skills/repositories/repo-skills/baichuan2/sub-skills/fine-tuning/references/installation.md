# Fine-Tuning Installation and Environment Checks

Baichuan2 supervised fine-tuning needs the Transformers training stack, DeepSpeed, SentencePiece, CUDA-capable PyTorch for practical GPU training, and PEFT when `--use_lora True` is used.

## Core packages

Install a CUDA-compatible PyTorch build first, then the model/training dependencies:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
python -m pip install transformers accelerate sentencepiece tokenizers numpy deepspeed
```

For LoRA:

```bash
python -m pip install peft
```

Optional training accelerators such as xFormers are not required by the bundled trainer. Install them only if you have a tested reason and compatible wheels for the host.

## Verified package facts

A verified drafting environment for this skill had:

- `torch 2.5.1+cu121`
- `deepspeed 0.19.5` import and CLI help passing
- `peft 0.20.0` import passing
- `accelerate 1.14.0`
- `sentencepiece 0.2.2`
- CUDA tensor smoke passing on an NVIDIA A100

These facts prove that the training stack can import and see CUDA in that class of environment. They do not prove that a full model fine-tune will fit a particular GPU allocation or finish within a given budget.

## Minimum smoke checks

Run these before launching a distributed job:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__, 'cuda', torch.version.cuda)
print('cuda_available', torch.cuda.is_available())
print('cuda_count', torch.cuda.device_count())
if torch.cuda.is_available():
    x = torch.empty((1,), device='cuda')
    print('tensor_device', x.device)
    print('device_name', torch.cuda.get_device_name(0))
PY

python - <<'PY'
import transformers, accelerate, sentencepiece, deepspeed
print('transformers', transformers.__version__)
print('accelerate', accelerate.__version__)
print('deepspeed import ok')
PY

deepspeed --help | head -n 20
```

For LoRA:

```bash
python - <<'PY'
import peft
print('peft', peft.__version__)
PY
```

## Version cautions

- The repository training example originally pinned an older torch line, but modern Transformers/Accelerate stacks may require newer torch. Prefer a consistent environment that passes `pip check`, imports, and a CUDA smoke test.
- DeepSpeed may emit warnings about optional compiled ops or `CUDA_HOME`. Warnings are non-blocking only if imports, CLI help, CUDA tensor allocation, and the actual launch path still pass.
- `trust_remote_code=True` is required for Baichuan model/tokenizer loading.
- Use `use_fast=False` for the tokenizer to match the documented training behavior.

## Multi-node environment requirements

Every node in the hostfile should have:

- the same Python package versions;
- compatible CUDA driver/runtime access;
- SSH connectivity from the launch node if using the standard DeepSpeed launcher;
- the model cache available locally or downloadable from each node;
- the training data path readable from each node, preferably through a shared filesystem or identical local path;
- a writable output path strategy that does not corrupt checkpoint writes.

## Pre-flight sequence

1. Install core packages and optional PEFT if LoRA will be used.
2. Run package import, `pip check`, `deepspeed --help`, and CUDA smoke checks.
3. Validate training JSON with the bundled validator.
4. Generate or inspect the DeepSpeed config.
5. Run the trainer in `--dry_run True` mode.
6. Start a short one-step or tiny-fixture run before a long production run when budget allows.
