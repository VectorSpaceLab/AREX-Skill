# Scaling and Backend Troubleshooting

Use this reference to distinguish missing optional packages, unsupported hardware, server connectivity, and real memory/config failures before proposing expensive commands.

## First Safe Check

Run the bundled no-side-effect diagnostic:

```bash
python scripts/check_optional_backends.py
python scripts/check_optional_backends.py --json
```

It checks imports, versions where available, `torch` accelerator visibility, and whether the installed `trl` CLI exposes `vllm-serve --help`. It does not train, start a server, download a model, or allocate large tensors.

## Missing Optional Extras

Symptoms:

- `ImportError: vLLM is not installed. Please install it with pip install trl[vllm]`.
- `No module named 'peft'`, `No module named 'bitsandbytes'`, `No module named 'deepspeed'`, `No module named 'liger_kernel'`, `No module named 'kernels'`, or `No module named 'unsloth'`.
- `trl vllm-serve --help` works in a base install, but actual serving fails when vLLM/FastAPI/Uvicorn/Pydantic are absent.

Resolution:

- Recommend only the extras needed for the chosen backend.
- For vLLM serving, verify `vllm`, `fastapi`, `pydantic`, and `uvicorn` imports.
- For LoRA, verify `peft`; for QLoRA, verify `bitsandbytes` too.
- For DeepSpeed launch configs, verify `deepspeed` and `accelerate` compatibility.
- For Liger or Kernels Hub attention, verify `liger-kernel` or `kernels` plus compatible CUDA/PyTorch stack.

## CUDA or Hardware Unavailable

Symptoms:

- `torch.cuda.is_available()` is false.
- vLLM import may exist but server cannot initialize a GPU backend.
- bitsandbytes quantization errors mention CUDA, unsupported platform, or missing shared libraries.
- Kernel packages import but optimized attention fails at runtime.

Resolution:

- Treat CPU-only checks as inspection only; do not claim real vLLM/quantized training will work.
- Recommend smaller CPU-safe smoke tests only if the user wants functional code validation, not performance validation.
- Ask before suggesting Docker, driver changes, CUDA toolkit changes, or cloud/GPU migration.
- For older GPUs, prefer `fp16=True`; for Ampere/newer, prefer `bf16=True` when supported.

## vLLM Server Timeout or URL Failure

Symptoms:

- `The vLLM server can't be reached at ... after ... seconds`.
- Trainer waits on `/health/` and then raises a connection error.
- Requests fail with connection refused, DNS failures, 404 due to wrong base path, or reverse-proxy issues.

Resolution checklist:

1. Confirm the server was intentionally started and is still running.
2. Confirm trainer `vllm_server_base_url` exactly matches the reachable URL, including scheme, host, port, and any path prefix.
3. If using host/port fields, remember `vllm_server_base_url` overrides them.
4. Check firewalls, container port mapping, SSH tunnels, and service host binding.
5. Increase `vllm_server_timeout` only when the server is legitimately still loading a large model; do not use it to mask wrong URLs.
6. If weight sync fails after health succeeds, check `vllm_group_port` and device separation.

## vLLM CUDA Device Conflict

Symptoms:

- Error text about attempting to use the same CUDA device for multiple distinct roles/ranks within the same communicator.
- Hangs around weight synchronization or NCCL initialization.

Resolution:

- In server mode, use disjoint `CUDA_VISIBLE_DEVICES` masks for the vLLM server and trainer.
- Do not let Accelerate training see all GPUs if some are reserved for vLLM.
- Keep `vllm_group_port` unique if multiple jobs run on one host.
- For single-GPU systems, use colocate only if memory allows; otherwise disable vLLM or use more hardware.

## OOM During Training or Serving

Symptoms:

- CUDA out-of-memory during model load, generation warmup, first backward pass, or vLLM KV-cache allocation.
- vLLM initialization fails when `gpu_memory_utilization` is high or model context is large.

Resolution order:

1. Reduce `per_device_train_batch_size`, `max_length`, `max_completion_length`, number of generations, or prompt length.
2. Increase `gradient_accumulation_steps` to preserve effective batch size if needed.
3. Use `bf16`/`fp16`, PEFT/LoRA, QLoRA, activation checkpointing, or offloading if compatible.
4. For vLLM, lower `gpu_memory_utilization`, set a realistic `max_model_len`, reduce concurrency, or move from colocate to server mode on separate GPUs.
5. For large full fine-tunes, move to FSDP2 or DeepSpeed ZeRO rather than piling on unrelated kernel flags.

## Tensor/Data Parallel Mismatch

Symptoms:

- `tensor_parallel_size` exceeds available local GPUs without a distributed executor.
- Dense model serving rejects `data_parallel_size > 1` on newer vLLM versions.
- NCCL/Ray errors appear at server startup.

Resolution:

- Set `tensor_parallel_size` equal to the number of generation GPUs used to shard one model.
- Keep `data_parallel_size=1` for dense models unless the user has a confirmed supported vLLM setup.
- Use Ray only for explicit multi-node tensor-parallel serving; confirm cluster and networking first.
- In colocate mode, set trainer-side `vllm_tensor_parallel_size`; in server mode, set server-side `--tensor-parallel-size`.

## DeepSpeed vs FSDP Config Confusion

Symptoms:

- Launch command mixes FSDP and DeepSpeed settings.
- Accelerate config says `distributed_type: FSDP` but command/docs refer to DeepSpeed ZeRO, or vice versa.
- Long-context settings use the wrong parallelism key for the backend.

Resolution:

- Use one distributed backend family per run.
- FSDP2 context parallelism uses `cp_size`/Ring Attention-style config.
- DeepSpeed ALST/Ulysses uses `sp_size` and DeepSpeed ZeRO config.
- If the model fits per GPU and the user only wants faster throughput, use ordinary multi-GPU data parallel first.

## PEFT and Quantization Failures

Symptoms:

- LoRA target module names do not match model architecture.
- `bitsandbytes` import or CUDA setup errors.
- Quantized model loading conflicts with full fine-tuning expectations.

Resolution:

- Verify `peft` import for LoRA and `bitsandbytes` import for 4-bit/8-bit paths.
- Keep adapter training expectations explicit: fewer trainable parameters, not a universal activation-memory fix.
- Use model-specific target modules rather than assuming every model uses `q_proj`/`v_proj`.
- Avoid QLoRA on unsupported CPU-only or incompatible CUDA environments.

## Kernel and Liger Failures

Symptoms:

- FlashAttention or kernels import succeeds but attention implementation fails during model load.
- `use_liger_kernel=True` conflicts with a trainer/loss/model path.
- Manual FlashAttention build errors dominate the task.

Resolution:

- Prefer Kernels Hub attention implementations over manual compilation when supported.
- Check whether the trainer supports `use_liger_kernel=True`.
- Do not combine Liger with `SFTTrainer` chunked NLL, PEFT, or VLM paths where the docs mark incompatibility.
- Fall back to SDPA/default attention if optimized kernels block progress.

## Docker, Services, and Hardware Mutations

Do not perform these without explicit user approval:

- Starting `trl vllm-serve` or any long-lived service.
- Running `accelerate launch` for real training.
- Pulling Docker images or changing CUDA/driver/toolkit packages.
- Downloading large models/datasets.
- Starting RapidFire, vLLM, Ray, or dashboard services.

When approval is absent, provide a dry-run plan, safe diagnostics, and concrete commands labeled as templates.
