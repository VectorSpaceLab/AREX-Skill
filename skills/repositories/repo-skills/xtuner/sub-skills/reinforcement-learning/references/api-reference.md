# XTuner RL API Reference

This reference summarizes the user-facing RL classes and fields a future agent is most likely to configure or diagnose. Import paths are stable operating hints for an installed XTuner package; they are not links to a source checkout.

## CLI entry point

Preferred installed-package command:

```bash
python -m xtuner.v1.train.cli.rl --config /path/to/config.py --work-dir /runs/exp --num-workers 8
```

| CLI option | Required | Effect |
| --- | --- | --- |
| `--config PATH` | yes | Loads a Python config through `Config.fromfile`; expects a top-level `trainer` config object. |
| `--work-dir PATH` | no | Overrides `cfg.trainer.work_dir` before `trainer.build()`. |
| `--num-workers INT` | no | If the trainer config has `resources`, overwrites `cfg.trainer.resources.num_workers`. This targets colocated trainers only. |

Runtime behavior to remember:

- Calls `ray.init(address="auto")` if Ray is not already initialized.
- Starts a background memory monitor only when `XTUNER_RL_MEM_DIR` is set.
- Builds `cfg.trainer` and calls `trainer.fit()`.
- Destroys a Torch distributed process group at shutdown if one was initialized.

## Trainer configs

### Shared `BaseRLTrainerConfig` fields

Both trainer layouts share these fields:

| Field | Purpose / common setting |
| --- | --- |
| `train_worker_cfg` | `WorkerConfig` for policy model, optimizer, RL loss, LR, FSDP, sequence parallelism, and pack length. |
| `rollout_config` | `RolloutConfig` for inference backend, model path, TP/EP/DP, context length, timeout, retry, and health checks. |
| `tokenizer_path` | Tokenizer loaded by the trainer and agent loop manager. Often the same as `MODEL_PATH`. |
| `replay_buffer_config` | `SyncReplayBufferConfig()` for on-demand production or `AsyncReplayBufferConfig()` for staleness-aware background/async production. |
| `agent_loop_manager_cfg` | Training rollout manager. Colocated uses `AgentLoopManagerConfig`; disaggregated uses `DisaggAgentLoopManagerConfig`. |
| `eval_agent_loop_manager_cfg` | Optional evaluation rollout manager. When evaluation is enabled, it must be present. |
| `evaluator_config` | Optional `EvaluatorConfig`; when evaluation is enabled, it must be present. |
| `load_from` | HF model path or model id. Current trainer initialization expects an HF-compatible source. |
| `total_train_steps` / `total_epochs` | One is required unless `debug_train=True`. |
| `train_batch_size` | Number of rollout samples/groups consumed per training step. |
| `advantage_estimator_config` | Defaults to `GRPOAdvantageConfig(eps=1e-8)`. |
| `sync_weights_interval` | Steps between synchronizing training weights to rollout workers. Must be positive. |
| `enable_evaluate`, `enable_initial_evaluate`, `evaluate_step` | Evaluation control. `evaluate_step` must be positive and a multiple of `sync_weights_interval` when evaluation is enabled. |
| `work_dir`, `log_dir` | Runtime output roots for checkpoints, logs, traces, replay buffer state, and debug artifacts. |
| `auto_resume`, `load_checkpoint_cfg` | Resume policy. Auto-resume resolves latest checkpoint from `work_dir`. |
| `checkpoint_interval`, `hf_interval` | Save/export intervals. Enabled intervals must be positive multiples of `sync_weights_interval`. Use `-1` or `None` to disable. |
| `checkpoint_no_save_optimizer`, `checkpoint_no_save_replay_buffer` | Skip optimizer or replay-buffer state in checkpoint saves. |
| `debug_rollout`, `debug_train`, `debug_rollout_dir` | Debug modes. Rollout and train debug cannot both be true; either debug mode requires `debug_rollout_dir`. |
| `exp_tracker` | `"tensorboard"` or `"jsonl"`; default is `"tensorboard"` for RL trainer configs. |
| `trace_config` | `TraceConfig` for OpenTelemetry and rollout trace export. |

### `RLColocateTrainerConfig`

Import path: `xtuner.v1.train.rl_trainer.RLColocateTrainerConfig`.

Adds:

| Field | Meaning |
| --- | --- |
| `resources` | Shared `AcceleratorResourcesConfig` used by both training and rollout workers. |

Use when training and rollout share the same accelerator pool and alternate by step. The CLI `--num-workers` override applies to `resources.num_workers`.

### `RLDisaggregatedTrainerConfig`

Import path: `xtuner.v1.train.rl_trainer.RLDisaggregatedTrainerConfig`.

Adds:

| Field | Meaning |
| --- | --- |
| `train_resources` | `AcceleratorResourcesConfig` for training workers. |
| `rollout_resources` | `AcceleratorResourcesConfig` for rollout workers. |

Use when rollout runs in the background on dedicated rollout resources while training consumes replay-buffer samples on training resources. The CLI `--num-workers` override does not rewrite these two pools.

## Resource configs

### `AcceleratorResourcesConfig`

Import path: `xtuner.v1.rl.utils.AcceleratorResourcesConfig`.

| Field | Default / rule |
| --- | --- |
| `accelerator` | `"GPU"` or `"NPU"`; default `"GPU"`. |
| `num_workers` | Required. Number of accelerator workers / placement-group bundles. |
| `num_cpus_per_worker` | Default `12`. |
| `cpu_memory_per_worker` | Default `16 * 1024**3` bytes. |
| `num_accelerators_per_node` | Default `8`; NPU post-init adjusts to `16`. |
| `num_accelerators_per_worker` | Default `1`. |
| `pg_pack_strategy` | Ray placement-group strategy, default `"PACK"`; must be a Ray-valid placement strategy. |

`validate_available_resources()` requires Ray to be initialized and asserts enough accelerator, CPU, and memory resources in the current Ray cluster.

### `CPUResourcesConfig`

Import path: `xtuner.v1.rl.utils.CPUResourcesConfig`.

| Field | Default / rule |
| --- | --- |
| `num_workers` | Default `1`, must be at least 1. |
| `num_cpus_per_worker` | Default `1`, must be positive. |
| `cpu_memory_per_worker` | Default `1 * 1024**3`, must be positive. |
| `pg_pack_strategy` | Default `"SPREAD"`; must be Ray-valid. |

Used for judgers and agent loops that should run in Ray CPU actors outside accelerator placement groups.

## Training worker config

Import path: `xtuner.v1.rl.trainer.WorkerConfig`.

| Field | Purpose |
| --- | --- |
| `model_cfg` | XTuner transformer/compose model config. Model family and MoE/FSDP details belong to `model-backends`. |
| `optim_cfg` | Optimizer config such as `AdamWConfig(lr=..., foreach=False, weight_decay=...)`. |
| `loss_cfg` | RL loss config such as `GRPOLossConfig`. |
| `lr_cfg` | LR scheduler config such as `LRConfig(lr_type="constant", warmup_ratio=0, lr_min=1e-6)`. |
| `fsdp_cfg` | FSDP config for training worker sharding. Route deep backend sizing to `model-backends`. |
| `load_from` | Initial model path. Usually set from `MODEL_PATH`. |
| `optimizer_steps` | Gradient/optimizer steps per RL step; default `1`. |
| `sp_size` | Sequence parallel size; default `1`. |
| `pack_max_length` | Required maximum packed sequence length. |
| `ref_load_from`, `ref_model_fsdp_cfg` | Reference model path/config for KL regularization when needed. |
| `update_weight_bucket_size_in_gb` | Weight-sync bucket size; default `0.5`. |
| `profile_step`, `profile_time`, `profile_memory` | Profiling knobs. |
| `sft_dataloader_cfg`, `sft_global_batch_size`, `rollout_steps_per_sft`, `sft_loss_cfg` | Optional mixed SFT/RL fields; generic SFT workflow belongs to `training`. |

## Rollout config

Import path: `xtuner.v1.rl.rollout.worker.RolloutConfig`.

Backend selection is environment-driven. The `rollout_backend` property checks, in order, `XTUNER_USE_SGLANG`, `XTUNER_USE_VLLM`, then `XTUNER_USE_LMDEPLOY`, and asserts that one backend is active.

| Field | Purpose |
| --- | --- |
| `env` | Logical rollout environment name used in worker/backend logs. |
| `device` | `"GPU"` or `"NPU"`, usually copied from resource config. |
| `model_path` | Model path passed to backend engine. |
| `model_name` | Optional serving/model name. If omitted, XTuner may infer from model config/name. |
| `tokenizer_path` | Optional tokenizer path. |
| `api_key` | Optional backend service key(s). |
| `gpus_per_node` | Cluster shape hint; default `8`. |
| `dtype` | Default `"bfloat16"`. |
| `gpu_memory_utilization` | Backend memory fraction; examples often use `0.8`. |
| `random_seed` | Rollout worker seed, default `1024`. |
| `rollout_cross_node_comm` | Cross-node rollout communication switch. |
| `dist_port_base`, `weight_update_host`, `weight_update_port` | Distributed and weight-update ports/host. |
| `rollout_max_batch_size_per_instance` | Max batch per inference instance. If `None`, XTuner chooses based on context length. |
| `allow_over_concurrency_ratio` | Deprecated compatibility field; setting it emits a warning and does not control runtime concurrency. |
| `tensor_parallel_size`, `data_parallel_size`, `expert_parallel_size` | Rollout engine parallelism. `num_gpus_per_engine` is `expert_parallel_size` when EP > 1, else TP. |
| `enable_chunked_prefill`, `chunked_prefill_size` | Chunked prefill control. |
| `skip_load_weights` | Used during resume to avoid duplicate rollout weight loading. |
| `enable_return_routed_experts` | Return routed-expert information for MoE/trace-aware workflows. |
| `launch_server_method` | `"ray"` or `"multiprocessing"`; default `"ray"`. |
| `rollout_timeout`, `session_server_timeout` | Generation/session HTTP timeout seconds. |
| `context_length` | Rollout context length; plan as prompt length + max response length. |
| `enable_float8` | Backend float8 switch; verify model/backend support before use. |
| `extra_rollout_config` | Backend-specific settings with backend prefixes, e.g. vLLM/LMDeploy/SGLang keys. |
| `max_retry_per_worker`, `max_retry_per_sample` | Retry policy. Sample retry default is `1`. |
| `max_prefill_token_num`, `router_n_groups`, `fp32_lm_head` | Advanced backend/model options. |
| `worker_log_dir` | Worker log directory; trainer normally sets this under runtime logs. |
| `health_check_interval_seconds`, `health_check_timeout_seconds`, `health_check_failure_threshold` | Backend health-check cadence and failure threshold. |
| `enable_proxy` | Register session servers to a routed API proxy. Enable only when the user provides appropriate proxy URLs and understands the deployment. |

## Agent loops and managers

### `SampleParams`

Import path: `xtuner.v1.data_proto.rl_data.SampleParams`.

Common fields: `n`, `top_k`, `top_p`, `temperature`, `repetition_penalty`, `presence_penalty`, `frequency_penalty`, `min_tokens`, `max_tokens`, `stops`, `stop_token_ids`, `skip_special_tokens`, `sampling_seed`, `stream`, `return_logprob`, `top_logprobs`, `return_token_ids`, `include_stop_str_in_output`, `no_stop_trim`, `spaces_between_special_tokens`, and `return_routed_experts`.

For training rollouts, examples commonly use `top_k=0`, `top_p=1.0`, `temperature=1.0`, and large `max_tokens`. Evaluation often uses `top_k=1` and `temperature=0.0`.

### `SingleTurnAgentLoopConfig`

Import path: `xtuner.v1.rl.agent_loop.SingleTurnAgentLoopConfig`.

Fields inherited from `AgentLoopConfig`:

| Field | Purpose |
| --- | --- |
| `hf_checkpoint` | Checkpoint/model identifier used by the agent loop. |
| `sample_params` | `SampleParams` for generation. |
| `cpu_resources` | Optional `CPUResourcesConfig`; if omitted, runs locally. |
| `enable_batch_judge` | Judge a generated group in one batch when the judger supports it. |
| `requires_rollout_proxy` | Internal/proxy-aware loops use this; ordinary single-turn loops keep false. |

`SingleTurnAgentLoopConfig` performs one model generation per prompt and optionally calls a judger on completed responses.

### `SamplerConfig`

Import path: `xtuner.v1.rl.agent_loop_manager.SamplerConfig`.

| Field | Purpose |
| --- | --- |
| `dataloader_cfg` | XTuner dataloader config yielding `RolloutState` prompts. |
| `prompt_repeat_k` | Number of rollout samples per prompt; this is the GRPO group size in common configs. |

### `TaskSpecConfig` and `AgentLoopManagerConfig`

Import path: `xtuner.v1.rl.agent_loop_manager`.

`TaskSpecConfig` fields:

| Field | Purpose |
| --- | --- |
| `task_name` | Unique task name for logs, replay-buffer routing, and checkpoints. |
| `weight` | Multi-task batch allocation weight; default `1.0`. |
| `agent_loop_config` | Agent loop config, often `SingleTurnAgentLoopConfig`. |
| `judger_config` | Optional judger config. |
| `produce_strategy_config` | `SyncProduceStrategyConfig()` by default; can be `AsyncProduceStrategyConfig(...)`. |
| `sampler_config` | `SamplerConfig`. |

`AgentLoopManagerConfig(tasks=...)` accepts one `TaskSpecConfig` or a list. Task names must be unique.

### Produce strategies

| Config | Use case | Key fields |
| --- | --- | --- |
| `SyncProduceStrategyConfig()` | On-demand rollout production, simplest colocated mode. | Optional custom `is_valid_sample_fn`, `should_continue_fn`. |
| `AsyncProduceStrategyConfig(...)` | Colocated async production with oversampling/staleness. | `over_sample_threshold`, `enable_partial_rollout`, `max_staleness`, `tail_batch_trigger_size`. |
| `DisaggAsyncProduceStrategyConfig(...)` | Disaggregated background production. | Same practical knobs as async colocated, under disaggregated manager. |

`max_staleness` is non-negative. Effective threshold is `(max_staleness + 1) * sync_weights_interval`.

## Judgers and reward model

### `GSM8KJudgerConfig`

Import path: `xtuner.v1.rl.judger.GSM8KJudgerConfig`.

| Field | Default / purpose |
| --- | --- |
| `judger_name` | Default `"openai/gsm8k"`; also used for composed-judger routing. |
| `reward_handler` | Defaults to the built-in GSM8K `compute_reward` callable. Can also be an HTTP endpoint string. |
| `request_timeout` | Default `30.0` seconds for HTTP reward handlers. |
| `extra_info` | Default `{"score": 1, "format_score": 0}`. |
| `cpu_resources` | Optional `CPUResourcesConfig` inherited from `JudgerConfig` for Ray CPU workers. |

The native judger preprocesses `RolloutState` into `response`, `label`, `message`, `status`, `data_source`, and `task_name`. `label` is `rollout_state.reward_model.get("ground_truth")`; missing ground truth is a hard assertion.

## Replay and evaluation

| Config | Purpose |
| --- | --- |
| `SyncReplayBufferConfig()` | FIFO in-memory replay for on-demand production. No user fields. |
| `AsyncReplayBufferConfig()` | Staleness-aware in-memory replay for async/background production. No user fields. |
| `EvaluatorConfig(eval_sample_ratio=0, eval_sample_num=0, compute_metric_func=None)` | Selects evaluation sample count and metric function. If fixed count is 0 and ratio is 0, evaluates all available samples. |

Default evaluator metrics include reward accuracy, optional tool-turn statistics, and grouped pass@k metrics when repeated attempts can be inferred.

## Advantage and loss configs

### Advantage estimators

| Config | Fields | Use |
| --- | --- | --- |
| `GRPOAdvantageConfig` | `eps=1e-8` | Default GRPO group-normalized advantages. |
| `DrGRPOAdvantageConfig` | `max_length=32768`, `eps=1e-8` | Duration/length-scaled GRPO variant. |
| `RLOOAdvantageConfig` | none | Leave-one-out estimator. |
| `OPOAdvantageConfig` | `eps=1e-8` | OPO estimator. |
| `PassKAdvantageConfig` | `k=4`, `eps=1e-6` | Pass@k-style estimator. |

### `GRPOLossConfig`

Import path: `xtuner.v1.rl.loss.GRPOLossConfig`.

Key fields inherited from `BaseRLLossConfig` and CE loss config:

| Field | Purpose |
| --- | --- |
| `policy_loss_cfg` | Required dict. Common keys include `loss_type`, `cliprange_low`, `cliprange_high`, `clip_ratio_c`, `log_prob_diff_min`, and `log_prob_diff_max`. |
| `use_kl_loss` | Whether to compute KL against a reference model. |
| `kl_loss_coef` | KL weight, default `0.001`. |
| `kl_loss_type` | One of `"kl"`, `"k1"`, `"abs"`, `"mse"`, `"k2"`, `"low_var_kl"`, `"k3"`, or `None`. |
| `rollout_is` | Rollout importance-sampling config. |
| `ignore_idx` | Token ignore index, commonly `-100`. |
| `mode`, `chunk_size` | Loss compute mode, often `"chunk"` with chunk size such as `512` or `1024`. |

When `use_kl_loss=True`, ensure `WorkerConfig` has appropriate reference-model loading (`ref_load_from` or equivalent same-model behavior) and enough resources.

## Trace config

Import path: `xtuner.v1.rl.trace.TraceConfig`.

| Field | Default / purpose |
| --- | --- |
| `enabled` | Default `False`; enables XTuner trace runtime. |
| `output_dir` | Optional trace output root; when `None`, runtime picks a work-dir-derived/default trace root. |
| `service_name` | Default `"xtuner-rollout"`. |
| `xtuner_viewer_enabled` | Start XTuner trace viewer when trace runtime is active. |
| `xtuner_viewer_host`, `xtuner_viewer_port` | Viewer bind host/port; default host `127.0.0.1`, port `18080`. |
| `xtuner_viewer_jaeger_query_url` | Optional Jaeger query URL for viewer integration. |
| `enable_rollout_trace` | Include rollout spans and carrier propagation. |

Trace runtime may require OpenTelemetry exporter packages and an `otelcol`/`otelcol-contrib` binary when collection/export is enabled. If missing, tracing can fail before training starts.
