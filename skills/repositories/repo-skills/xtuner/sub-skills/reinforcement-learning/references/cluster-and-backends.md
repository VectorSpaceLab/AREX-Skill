# XTuner RL Cluster and Backend Planning

XTuner RL combines a Ray resource layer, an accelerator placement plan, and one optional rollout inference backend. This reference focuses on pre-launch planning and diagnosis. It does not replace backend installation guides or start any services.

## Runtime dependency layers

| Layer | Needed for | Notes |
| --- | --- | --- |
| XTuner base package | Config loading, trainer configs, model/dataset objects. | Keep package/version consistent with the config copy. |
| RL Python deps | RL CLI import and Ray actors. | RL requirements include `ray[default]` and `httpx`; some configs also need package extras already required by training/data/model workflows. |
| Inference backend | Actual rollout generation. | Install exactly one selected backend family at runtime: LMDeploy, SGLang, or vLLM. |
| Accelerator stack | Training/rollout workers. | CUDA GPU or supported NPU stack must match Ray visible resources and backend wheels. |
| Optional tracing | OpenTelemetry traces/viewer. | Enabling trace may require OTel Python packages and an `otelcol`/`otelcol-contrib` binary. |

A missing inference backend should be treated as an optional-backend problem, not as a data or trainer-config problem.

## Ray lifecycle

The RL CLI itself does not start a Ray head. If Ray is not initialized in the process, it executes:

```python
ray.init(address="auto")
```

Therefore, before running the CLI, make sure one of these is true:

- a local Ray head is already running and discoverable;
- a multi-node Ray cluster has been started and workers have joined;
- the runtime wrapper initializes Ray before calling XTuner APIs directly.

Preflight checks:

```bash
python - <<'PY'
import ray
try:
    ray.init(address="auto")
    print("Ray connected")
    print(ray.available_resources())
finally:
    if ray.is_initialized():
        ray.shutdown()
PY
```

If this fails with no cluster found, start Ray externally and rerun the check. Do not patch the XTuner config first; the config cannot compensate for an absent Ray cluster.

## Resource-count planning

### Colocated trainer

`RLColocateTrainerConfig` uses a single `AcceleratorResourcesConfig(resources=...)` pool. Common pattern:

```python
resources = AcceleratorResourcesConfig(
    accelerator="GPU",
    num_workers=8 * NNODE,
    num_cpus_per_worker=12,
    cpu_memory_per_worker=16 * 1024**3,
)
```

CLI `--num-workers N` overwrites `trainer.resources.num_workers` if the config has `resources`.

### Disaggregated trainer

`RLDisaggregatedTrainerConfig` uses two pools:

```python
train_resources = AcceleratorResourcesConfig(accelerator="GPU", num_workers=4)
rollout_resources = AcceleratorResourcesConfig(accelerator="GPU", num_workers=4)
```

CLI `--num-workers` does not rewrite these fields. Change the config copy or its env-driven resource variables instead.

### GPU/NPU accounting

- `accelerator="GPU"` checks `ray.available_resources()["GPU"]`.
- `accelerator="NPU"` checks `ray.available_resources()["NPU"]` and adjusts `num_accelerators_per_node` to 16 by default.
- CPU demand is roughly `num_cpus_per_worker * num_workers + 10` per checked resource pool.
- Memory demand is roughly `cpu_memory_per_worker * num_workers + 10 GiB` per checked resource pool.
- On GPU, if `CUDA_VISIBLE_DEVICES` is set, native shell helpers commonly count visible IDs as accelerators per node. Preserve that accounting in launch plans.

## Backend selection flags

`RolloutConfig.rollout_backend` is selected by environment variables, not by a `backend=` field:

| Backend | Required env | Typical extra env |
| --- | --- | --- |
| SGLang | `XTUNER_USE_SGLANG=1` | `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`, `SGLANG_ENABLE_HEALTH_ENDPOINT_GENERATION=False`, often unset `PYTORCH_CUDA_ALLOC_CONF`. |
| vLLM | `XTUNER_USE_VLLM=1` | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in many launch wrappers. |
| LMDeploy | `XTUNER_USE_LMDEPLOY=1` | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, optional `LMDEPLOY_LOG_FILE`, backend-specific path/env if the user's installation requires it. |

Set the two unselected backend flags to `0` or leave them unset. Do not set multiple backend flags to `1`; the source checks SGLang first, then vLLM, then LMDeploy, which can mask the user's intended backend.

Common XTuner env vars:

| Env var | Purpose |
| --- | --- |
| `WORK_DIR` | Runtime directory consumed by many example configs and trace/debug helpers. |
| `MODEL_PATH` | HF model snapshot/model id used by worker, rollout, tokenizer, and load source. |
| `DATA_PATH` | Training JSONL path. |
| `EVAL_DATA_PATH` | Evaluation JSONL path. |
| `XTUNER_USE_FA3` | FlashAttention v3 switch. If `1`, missing FA3 can raise a runtime error; use `0` for deterministic/SGLang or fallback workflows. |
| `XTUNER_LOG_LEVEL` | Logging verbosity, commonly `INFO`. |
| `PYTHONUNBUFFERED` | Set to `1` for live log streaming. |
| `XTUNER_RL_MEM_DIR` | Enables RL actor memory monitoring during CLI execution. |
| `XTUNER_RL_MEM_INTERVAL` | Memory monitor interval seconds; default is 60 when monitor is enabled. |
| `XTUNER_RL_NUM_WORKERS` | Native shell wrappers use this as the value passed to `--num-workers`. |
| `WORLD_SIZE`, `RANK` | Multi-node config inputs used by examples and Ray startup wrappers. |
| `RAY_MASTER_ADDR`, `RAY_HEAD_PORT`, `RAY_DASHBOARD_PORT` | Ray cluster connection and dashboard settings in native wrappers. |

## Dry command generation

Use the bundled helper to produce a reviewable launch snippet:

```bash
python sub-skills/reinforcement-learning/scripts/build_rl_command.py \
  --config /configs/rl_grpo_gsm8k_async.py \
  --backend lmdeploy \
  --model-path /models/qwen3-8b \
  --data-path /data/gsm8k_train.jsonl \
  --eval-data-path /data/gsm8k_val.jsonl \
  --work-dir /runs/qwen3-grpo \
  --num-workers 8 \
  --enable-mem-monitor
```

The helper always emits the installed-package entry point `python -m xtuner.v1.train.cli.rl ...` and never relies on a source-tree script path.

## Multi-node launch shape

A safe cluster plan usually has two layers:

1. **Ray startup layer**, external to XTuner:
   - head node starts Ray with `--head`, node IP, head port, dashboard port, visible GPU/NPU count, and a temp/log directory;
   - worker nodes wait for the head dashboard or GCS port, then join with `ray start --address=...`;
   - all nodes agree on accelerator visibility and backend installation.
2. **XTuner CLI layer**, run once from the driver/head context:
   - exports `WORK_DIR`, `MODEL_PATH`, `DATA_PATH`, `EVAL_DATA_PATH`, backend flags, and config-specific env vars;
   - runs `python -m xtuner.v1.train.cli.rl --config ...`;
   - optionally passes `--work-dir` and `--num-workers`.

Do not conflate the layers. A successful command builder output is not proof that Ray has the requested accelerators.

## Rollout concurrency tuning

Main knobs:

| Knob | Scope | Guidance |
| --- | --- | --- |
| `RolloutConfig.rollout_max_batch_size_per_instance` | Per inference instance. | Larger values improve utilization but can OOM; if unset, XTuner selects based on `context_length`. |
| `SamplerConfig.prompt_repeat_k` | Prompt group size. | GRPO group size; affects how many generations are made per prompt. |
| `AsyncProduceStrategyConfig.over_sample_threshold` | Async production. | Extra completed-sample ratio; higher values improve throughput but can increase staleness. |
| `AsyncProduceStrategyConfig.max_staleness` | Async replay. | Additional sync cycles samples may lag. Effective threshold is `(max_staleness + 1) * sync_weights_interval`. |
| `AsyncProduceStrategyConfig.enable_partial_rollout` | Async rollout continuation. | Prefer true when `max_staleness>0` and long responses/tool calls can be interrupted by weight sync. |
| `Dataflow max_concurrent`-style config fields where present | Controller concurrency. | Start from backend capacity divided by `prompt_repeat_k`, then tune from queue length, utilization, and latency. |

`RolloutConfig.allow_over_concurrency_ratio` is deprecated and ignored for runtime concurrency.

## Backend-specific cautions

### LMDeploy

- Use `XTUNER_USE_LMDEPLOY=1` and ensure LMDeploy imports in the runtime env.
- Native shell wrappers set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` and often write `LMDEPLOY_LOG_FILE` under `WORK_DIR`.
- Some LMDeploy environments need additional package path/env settings; keep those user-provided and do not bake private paths into the skill.

### SGLang

- Use `XTUNER_USE_SGLANG=1` and ensure SGLang imports in the runtime env.
- Native deterministic wrappers use SGLang, `XTUNER_DETERMINISTIC=true`, `XTUNER_USE_FA3=0`, and `TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=0`.
- `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1` appears in native launch wrappers for long context runs.

### vLLM

- Use `XTUNER_USE_VLLM=1` and ensure vLLM imports in the runtime env.
- XTuner rollout code has limitations around `return_token_ids` or generating with `input_ids` for vLLM in some paths. If a config requires token-in-token-out traces or routed proxy behavior, verify vLLM support before choosing it.

## Reference-only native scripts

Native cluster submission shell scripts are not bundled as executable helpers because they can start Ray, block on workers, assume scheduler/NPU conventions, mutate temp log symlinks, or require private cluster layout. Distill their useful behavior into:

- explicit env export plans;
- external Ray startup instructions;
- one dry XTuner CLI command;
- troubleshooting checks for missing resources and backend flags.
