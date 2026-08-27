# Troubleshooting

Use this reference to triage OpenRLHF installation/runtime failures without overstating environment readiness. Prefer lightweight diagnostics first, then isolate the failing dependency or service.

## First Response Checklist

1. Ask what command failed and capture the exact error text.
2. Run the safe diagnostic if local access is available:

```bash
python skills/openrlhf/sub-skills/operations-and-utilities/scripts/check_openrlhf_runtime.py
```

3. Identify whether the failure is import-only, package installation, CUDA/toolkit, Ray environment propagation, model loading, service binding, LoRA merge, checkpoint conversion, or logger/auth.
4. Classify any next action: safe inspection, expensive model/GPU work, network download, long build, service start, or host mutation.

## flash-attn Fails During Install

Common symptoms include missing `torch`, missing CUDA toolkit/NVCC, compiler errors, build isolation metadata errors, or wheel/CUDA mismatch.

Evidence-backed guidance:

- Base requirements include `flash-attn==2.8.3`.
- The Dockerfile installs `vllm==0.22.1` first so its matching `torch` is present, then builds `flash-attn==2.8.3` with `--no-build-isolation`.
- The README recommends Docker and vLLM `0.22.1+` for best performance.

Triage steps:

```bash
python - <<'PY'
import importlib.util
for name in ['torch', 'flash_attn']:
    print(name, bool(importlib.util.find_spec(name)))
if importlib.util.find_spec('torch'):
    import torch
    print('torch', torch.__version__, 'cuda', torch.version.cuda, 'cuda_available', torch.cuda.is_available())
PY
```

If `flash-attn` fails before `torch` exists, install the intended GPU-compatible `torch` stack first, use the project Docker image approach, or choose wheels that match Python, CUDA, and torch. If a source build is required, ensure CUDA toolkit/NVCC and build tools are present. Do not treat a successful top-level `openrlhf` import as proof that `flash-attn` kernels are usable.

Temporary isolation option for diagnosis: use `--ds.attn_implementation eager` in utility/model-loading commands such as reward serving to determine whether the failure is specific to flash attention. This may be slower and is not the preferred performance path.

## CUDA Driver, Toolkit, and Wheel Mismatch

Different layers must agree:

- NVIDIA driver must support the CUDA runtime used by the installed wheels/container.
- `torch.version.cuda` indicates the CUDA runtime compiled into torch, not necessarily the local toolkit.
- Source builds such as `flash-attn` may need NVCC/toolkit headers even when PyTorch CUDA works.
- vLLM and flash-attn versions may imply specific torch/CUDA combinations.

Useful checks:

```bash
nvidia-smi
python - <<'PY'
import torch
print('torch', torch.__version__)
print('torch cuda runtime', torch.version.cuda)
print('cuda available', torch.cuda.is_available())
print('device count', torch.cuda.device_count())
PY
nvcc --version
```

`nvidia-smi` can work while `torch.cuda.is_available()` is false if the Python wheel stack is CPU-only or incompatible.

## Ray Env Var Is Ignored

OpenRLHF `train_ppo_ray` preserves user-provided `TOKENIZERS_PARALLELISM`, `NCCL_DEBUG`, and `RAY_ENABLE_ZERO_COPY_TORCH_TENSORS` when it calls `ray.init(runtime_env={"env_vars": ...})`. Defaults are `true`, `WARN`, and `1` respectively. `tests/test_ray_env_vars.py` asserts that user overrides such as `NCCL_DEBUG=INFO` survive.

If a user says `NCCL_DEBUG=INFO` is ignored:

1. Check whether Ray was already initialized. If so, OpenRLHF skips `ray.init()` and will not rebuild runtime env vars.
2. Check whether the variable was exported in the shell/container that launched the Python process or passed through `ray job submit --runtime-env-json`.
3. Check quoting of JSON submitted to Ray.
4. Check whether a cluster wrapper, Docker entrypoint, SLURM script, or job runtime environment overwrites it.
5. Use the native mock test as evidence for OpenRLHF behavior:

```bash
pytest tests/test_ray_env_vars.py
```

Example robust submission pattern:

```bash
ray job submit --address="http://127.0.0.1:8265" \
  --runtime-env-json='{"env_vars":{"NCCL_DEBUG":"INFO","TOKENIZERS_PARALLELISM":"false","RAY_ENABLE_ZERO_COPY_TORCH_TENSORS":"1"}}' \
  -- python3 -m openrlhf.cli.train_ppo_ray ...
```

For DeepSpeed GPU device index issues, the README suggests:

```bash
export RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES=1
```

## vLLM or DeepSpeed Optional Runtime Problems

- `openrlhf[vllm]` pins `vllm==0.22.1`; `openrlhf[vllm_latest]` allows newer versions and may introduce API drift.
- If vLLM is not importable, install the intended extra or disable vLLM where the CLI supports it. RL training examples generally expect vLLM for high-throughput generation.
- If DeepSpeed errors mention tensor parallel training, note that source checks require DeepSpeed `>=0.16.4` for that path; current requirements pin `deepspeed==0.19.1`.
- If RingAttention fails, verify the `ring` extra or `ring_flash_attn` is installed before using `--ds.ring_attn_size`.

## Reward Server Fails

Possible causes:

- Model id/path is wrong or requires authentication.
- Port is already in use.
- `flash_attention_2` cannot initialize in the current stack.
- GPU memory is insufficient for the reward model.
- `--ds.value_head_prefix` does not match the checkpoint.
- Batch size or `--data.max_len` is too large.

Triage:

```bash
python -m openrlhf.cli.serve_rm \
  --reward.model_name_or_path <model-or-path> \
  --port 5000 \
  --ds.attn_implementation eager \
  --ds.param_dtype bf16 \
  --data.max_len 2048 \
  --batch_size 1
```

If this works, reintroduce `flash_attention_2`, larger `--data.max_len`, and target batch size one at a time. If the port is busy, change `--port` and update training `--reward.remote_url` accordingly.

## LoRA Merge Fails or Produces Bad Model

Check:

- `--model_path` matches the base model used for adapter training.
- `--lora_path` is a PEFT adapter directory, not an unconverted DeepSpeed training checkpoint.
- Use `--is_rm` for reward model adapters so `AutoModelForSequenceClassification` is used.
- `--ds.param_dtype` matches intended deployment precision (`bf16` or `fp16`).
- Disk has enough space for a full merged model plus tokenizer files.

If the merge succeeds but downstream scoring fails, inspect reward model value head naming. OpenRLHF docs recommend `score` via `--value_prefix_head` for reward models that should load with `AutoModelForSequenceClassification`.

## Checkpoint Conversion Safety

The DeepSpeed universal checkpoint helper needs valid checkpoint trees and may create large output directories. It expects a `latest` file and handles PPO `_actor` / `_critic` subdirectories specially.

Before conversion:

```bash
find /path/to/ckpt -maxdepth 2 -name latest -print -exec cat {} \;
```

Do not run conversion on the only copy of important checkpoints without a backup. Ensure the active Python environment has `deepspeed` installed and the target storage can hold converted outputs.

## Logger and Credential Problems

OpenRLHF examples often include `--logger.wandb.key {wandb_token}`. Do not put real tokens in generated commands, shared logs, or skill content. If logging fails:

- Confirm whether the run should use W&B, TensorBoard, or no external logger.
- Export credentials through a secret manager or local environment, not command history, when possible.
- For smoke tests, disable external logging or use offline modes if the CLI supports them.

## Minimal Import vs Full Runtime Readiness

A successful `import openrlhf` proves only package visibility. It does not prove:

- CUDA devices are usable.
- `flash-attn` kernels build/import.
- vLLM can load the target model.
- DeepSpeed can initialize distributed training.
- Ray can propagate env vars across the actual cluster.
- HuggingFace/ModelScope credentials are available.

Escalate from import checks to dependency import checks, then CUDA checks, then small model/service checks, then full distributed runs.
