# vLLM Reference

Use vLLM in TRL when generation is the bottleneck in online methods. It is not a general replacement for training, and the server only performs generation/scoring-style requests while the trainer owns optimization and weight updates.

## Supported Use Cases

TRL docs identify vLLM support for online trainers including:

- `GRPOTrainer`
- `RLOOTrainer`
- `OnlineDPOTrainer` under experimental modules
- `NashMDTrainer` under experimental modules
- `XPOTrainer` under experimental modules

Some newer experimental distillation/async trainers also have server-oriented generation paths. Route experimental trainer semantics to the appropriate experimental/environment skill; keep this reference focused on backend behavior.

## Server vs Colocate

| Mode | Choose when | Avoid when |
| --- | --- | --- |
| `vllm_mode="server"` | Separate generation GPUs or a managed service are available; user can run a long-lived `trl vllm-serve`; stable weight-sync networking/ports are available | Only one small GPU is available; the user cannot manage a side service; server URL/port access is blocked |
| `vllm_mode="colocate"` | GPU count is limited and the user accepts training/generation contention; no separate server should be managed | The model barely fits for training; vLLM KV cache causes OOM; strict throughput isolation is needed |

Practical rule: server mode is safer for serious GRPO/RLOO-style runs because it avoids training and generation fighting for the same CUDA devices. Colocate mode is a convenience path, not a guaranteed memory saver.

## Server Responsibilities

`trl vllm-serve` starts a FastAPI/Uvicorn-backed vLLM service with TRL weight synchronization endpoints. It supports generation requests, health checks, and model weight updates from the trainer. It does not perform optimizer steps.

Key server arguments distilled from TRL:

- `--model`: model id/path to load.
- `--revision`: model revision.
- `--tensor-parallel-size`: number of tensor-parallel workers.
- `--data-parallel-size`: number of data-parallel workers. For dense models, keep this at `1`; newer vLLM versions may reject higher values for dense models.
- `--host`, `--port`: service bind host/port; default port is `8000`.
- `--gpu-memory-utilization`: fraction of GPU memory reserved for vLLM weights/activations/KV cache; high values improve cache capacity but can trigger OOM.
- `--dtype`: vLLM dtype, commonly `auto`.
- `--max-model-len`: cap context length to match prompt plus completion needs and reduce KV cache pressure.
- `--enable-prefix-caching`, `--enforce-eager`, `--kv-cache-dtype`, `--trust-remote-code`, `--log-level`, `--vllm-model-impl`: advanced server controls.
- `--distributed-executor-backend ray`: needed when tensor parallel workers span multiple nodes rather than a single node.
- `--speculative-config`: JSON string for vLLM speculative decoding when the environment and model support it.

Do not start the server automatically from a skill-driven answer. Present commands as templates and ask for approval before running them.

## Trainer-Side Settings

Common trainer config fields for vLLM-backed generation include:

- `use_vllm=True`: switch generation from local `model.generate()` to vLLM.
- `vllm_mode="server"` or `"colocate"`: choose service vs same-process generation.
- `vllm_server_base_url`: full base URL such as `http://host:8000`; overrides host/port fields.
- `vllm_server_host`, `vllm_server_port`: host/port when not using `base_url`.
- `vllm_server_timeout`: total seconds to wait for `/health/` before raising a connection error; default behavior waits and retries.
- `vllm_group_port`: weight update communication port; usually leave unchanged unless occupied.
- `vllm_tensor_parallel_size`: colocate-only tensor parallel size. In server mode, tensor parallel size belongs to the server launch command.
- `vllm_gpu_memory_utilization`: colocate-only memory fraction. In server mode, set `--gpu-memory-utilization` on the server.
- `vllm_max_model_length`: context cap for colocate mode.
- `vllm_enable_sleep_mode`: offload/sleep vLLM engine during optimizer steps; saves memory but adds wake-up latency.
- `vllm_model_impl`: can select vLLM or Transformers implementation where supported.

## GRPO With Limited GPUs

For a user asking whether to choose server or colocate for GRPO with limited GPUs:

1. Count visible GPUs and model memory pressure.
2. If there are enough GPUs to reserve at least one for generation and at least one for training, recommend server mode with disjoint `CUDA_VISIBLE_DEVICES` masks.
3. If every GPU is needed for training or only one GPU exists, recommend colocate only after reducing batch/context/KV cache settings and warning about OOM/resource contention.
4. If neither mode fits, recommend disabling vLLM and using smaller model, PEFT/QLoRA, shorter completions, or more hardware.

Safe command templates:

```bash
# Generation service on dedicated devices; do not run without user approval.
CUDA_VISIBLE_DEVICES=0 trl vllm-serve --model MODEL_ID --tensor-parallel-size 1 --gpu-memory-utilization 0.8 --max-model-len 4096
```

```bash
# Trainer on separate devices; do not overlap with server devices.
CUDA_VISIBLE_DEVICES=1,2,3 accelerate launch train.py
```

```python
from trl import GRPOConfig

training_args = GRPOConfig(
    use_vllm=True,
    vllm_mode="server",
    vllm_server_base_url="http://localhost:8000",
    vllm_server_timeout=240.0,
)
```

Colocate template:

```python
from trl import GRPOConfig

training_args = GRPOConfig(
    use_vllm=True,
    vllm_mode="colocate",
    vllm_tensor_parallel_size=1,
    vllm_gpu_memory_utilization=0.3,
    vllm_max_model_length=4096,
)
```

## Parallelism and GPU Allocation

Server mode requires the trainer and vLLM workers to use different CUDA devices. TRL's weight sync path can raise an error when the same CUDA device participates in multiple roles in the communicator. A typical allocation uses generation GPUs in one `CUDA_VISIBLE_DEVICES` mask and training GPUs in another.

Tensor parallelism shards one model across workers. Data parallel workers process different requests. In recent vLLM dense-model setups, keep `data_parallel_size=1` unless the user has a specific supported use case.

If `tensor_parallel_size` is greater than local GPU count, the user may need a Ray distributed executor and multi-node networking. Do not suggest this as a casual fix.

## Continuous Batching and Weight Sync Implications

vLLM improves throughput by batching and scheduling generation requests efficiently with a KV cache. In TRL online training, the trainer periodically synchronizes updated weights to the server so completions reflect the current policy. This means:

- Server health and URL correctness matter before training begins.
- Weight update ports must be reachable and not occupied.
- Server GPUs need enough memory for model weights and KV cache.
- Larger `max_model_len`, more generations per prompt, and higher batch concurrency increase KV-cache pressure.
- Sleep/offload mode can reduce colocated memory pressure at the cost of latency.

## Safe Diagnostic Steps

Use these checks before recommending server launch:

1. Run `python scripts/check_optional_backends.py --json` from this sub-skill directory or with the script path.
2. Confirm `vllm`, `fastapi`, `pydantic`, and `uvicorn` imports are available for actual serving.
3. Confirm CUDA or another supported accelerator is visible for real serving; CPU-only inspection can validate CLI/help but is not enough for production vLLM training.
4. Confirm model context, requested completions, and GPU memory budget before setting `--max-model-len` and `--gpu-memory-utilization`.
5. Confirm server URL and port if connecting to an existing service.

Do not use the diagnostic script as proof that a large model will fit; it deliberately does not allocate model memory.
