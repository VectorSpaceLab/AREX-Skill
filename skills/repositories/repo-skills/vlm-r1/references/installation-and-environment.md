# Installation and environment guidance

VLM-R1 is a source-oriented repository with a nested Python distribution named `open-r1`. Most operating tasks require a user-controlled Python environment, model checkpoints, datasets/images, and backend hardware selected for the task.

## Package facts

- Distribution name: `open-r1`
- Import package: `open_r1`
- Metadata version observed: `0.1.0.dev0`
- Python requirement in package metadata: `>=3.10.9`
- Core pinned runtime: `transformers==4.49.0`, `trl==0.17.0`, `deepspeed==0.15.4`, CUDA-capable `torch`, `datasets`, `accelerate`, `bitsandbytes`, `liger_kernel`, `safetensors`, and `sentencepiece`.

The repository's broad setup also uses additional task dependencies such as `wandb`, `tensorboardx`, `qwen_vl_utils`, `torchvision`, `flash-attn`, `babel`, `python-Levenshtein`, `matplotlib`, `pycocotools`, `openai`, and `httpx[socks]`. Do not install all optional packages unless the selected workflow needs them.

## Minimal checks

Run these in the user's target environment, not inside this skill directory:

```bash
python -m pip check
python -c "import open_r1; import open_r1.configs; print('open_r1 import ok')"
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
```

For DeepSpeed/CUDA workflows, also probe compiler/toolkit visibility:

```bash
python -c "import deepspeed; print(deepspeed.__version__)"
python -c "import torch; x=torch.tensor([1.0], device='cuda'); print(x.item())"
```

If DeepSpeed import tries to compile CUDA ops and fails, ensure a compatible `CUDA_HOME` exposes `bin/nvcc` for that environment. The inspected host needed an environment-local NVIDIA CUDA nvcc package even though GPUs were visible.

## Known source compatibility hazards

1. **`grpo_jsonl.py` import path:** it imports `compute_score` as `from utils.math import compute_score`. That works when the script is executed from a layout where `open_r1/utils` is on `PYTHONPATH`, but it can fail for package-style imports. If `python -m open_r1.grpo_jsonl` fails with `No module named 'utils'`, run from the package source layout, add the package's `open_r1` source directory to `PYTHONPATH`, or patch the source to use `from open_r1.utils.math import compute_score` before relying on module execution.
2. **GLM import mismatch:** `glm_module.py` imports `Glm4vForConditionalGeneration`, but the pinned `transformers==4.49.0` environment inspected for this skill did not provide that class. Avoid selecting GLM unless the user has a verified compatible Transformers/model stack. Qwen and InternVL module sources are still usable.
3. **FlashAttention:** launch templates default to `flash_attention_2` because the repo scripts do. If FlashAttention is missing or ABI-incompatible, either install the matching build for the user's torch/CUDA/Python stack or switch to another attention implementation when the selected model supports it.

## Backend expectations

- **CPU/static:** data validators, command renderers, module contract checks, and offline bbox scoring can run without model downloads or GPUs.
- **CUDA:** full GRPO training, Qwen/InternVL model loading, distributed REC/OVD evaluation, LoRA/freeze-vision training, and vLLM generation require compatible GPUs and package variants. CPU checks are not proof of these workflows.
- **Ascend NPU:** vllm-ascend and XLLM recipes require Ascend device nodes, drivers/CANN runtime, container or build prerequisites, and checkpoint availability. Use the Ascend sub-skill templates as recipes unless running on actual Ascend hardware.

## Installation decision rules

- Prefer Python 3.10 or 3.11 for this repository because of compiled ML dependencies.
- Install only dependencies needed for the user's selected workflow. For example, data validation and offline scoring do not need `flash-attn`, `wandb`, or `vllm`.
- For full training, install and verify torch/CUDA, then DeepSpeed/FlashAttention, then the editable package and task-specific extras.
- Do not treat a successful root import as proof that full training will run; always run CUDA, DeepSpeed, data, model-path, and script dry-run checks first.
