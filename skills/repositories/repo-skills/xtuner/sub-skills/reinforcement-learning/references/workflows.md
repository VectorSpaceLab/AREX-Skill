# XTuner RL Workflows

Use this reference to plan XTuner RL/GRPO runs from a Python config and environment variables. It distills the RL CLI, trainer configs, rollout configs, native examples, and tests into a runtime checklist that does not require reopening the original repository.

## Core launch model

The XTuner V1 RL CLI is config-file driven:

```bash
python -m xtuner.v1.train.cli.rl --config /path/to/rl_config.py --work-dir /runs/exp --num-workers 8
```

CLI behavior:

- `--config` is required and must point to a Python config whose top-level `trainer` object is an `RLColocateTrainerConfig` or `RLDisaggregatedTrainerConfig`.
- `--work-dir` is optional. When supplied, the CLI overwrites `cfg.trainer.work_dir` before building the trainer.
- `--num-workers` is optional. The CLI only applies it when `cfg.trainer` has a colocated `resources` field; it does not rewrite disaggregated `train_resources` or `rollout_resources`.
- The CLI calls `ray.init(address="auto")` when Ray is not already initialized. Plan Ray startup outside the CLI command.
- If `XTUNER_RL_MEM_DIR` is set, the CLI starts a background memory-monitor thread that writes actor memory observations during training.

Use the bundled command builder for dry launch snippets:

```bash
python sub-skills/reinforcement-learning/scripts/build_rl_command.py \
  --config /configs/rl_grpo_gsm8k_async.py \
  --backend sglang \
  --model-path /models/qwen3-8b \
  --data-path /data/gsm8k_train.jsonl \
  --eval-data-path /data/gsm8k_val.jsonl \
  --work-dir /runs/qwen3-grpo \
  --num-workers 8
```

The builder prints exports and the command only; it never starts Ray, creates directories, or invokes training.

## Planning checklist

1. **Identify the config topology.** Confirm whether the config builds `RLColocateTrainerConfig` or `RLDisaggregatedTrainerConfig`.
2. **Identify required env vars.** Common example configs require `WORK_DIR`, `MODEL_PATH`, `DATA_PATH`, and `EVAL_DATA_PATH`. Disaggregated configs often also read `TRAIN_NUM_WORKERS`, `ROLLOUT_NUM_WORKERS`, `TRAIN_BATCH_SIZE`, `TOTAL_TRAIN_STEPS`, `SYNC_WEIGHTS_INTERVAL`, `OVER_SAMPLE_THRESHOLD`, `PARTIAL_ROLLOUT`, `TAIL_BATCH_TRIGGER_SIZE`, `MAX_STALENESS`, and `ENABLE_EVALUATE`.
3. **Confirm data ownership.** RL data schema/conversion belongs to `data-preparation`; this sub-skill only checks whether the config and judger will need fields such as `reward_model.ground_truth`.
4. **Confirm backend ownership.** Pick exactly one of LMDeploy, SGLang, or vLLM and ensure the runtime environment includes that package and its serving dependencies.
5. **Confirm Ray resources.** The trainer resources must fit `ray.available_resources()`: accelerator worker count, CPU worker count, and memory per worker.
6. **Confirm synchronization intervals.** If evaluation or checkpoint/HF export is enabled, `evaluate_step`, `checkpoint_interval`, and `hf_interval` must be positive multiples of `sync_weights_interval`.
7. **Confirm debug and trace outputs.** If `debug_rollout=True` or `debug_train=True`, set `debug_rollout_dir`. If `TraceConfig.enabled=True`, verify OpenTelemetry collector/exporter requirements and output directory policy.
8. **Only then launch.** Start Ray externally, then run the emitted CLI command in the environment containing XTuner, Ray, and the selected backend.

## Topology choices

### Colocated synchronous GRPO

Use `RLColocateTrainerConfig` with:

- one shared `AcceleratorResourcesConfig` in `resources`;
- `SyncReplayBufferConfig()`;
- `AgentLoopManagerConfig` with `TaskSpecConfig(..., produce_strategy_config=SyncProduceStrategyConfig())`;
- `sync_weights_interval=1` for strict on-policy behavior.

Choose this when the user has limited accelerators, is validating a first GRPO run, or wants the simplest mental model:

```text
rollout batch -> pause/release rollout side -> train step -> sync weights -> next rollout batch
```

Common fields to inspect:

- `resources.num_workers`: shared training/rollout worker count.
- `train_batch_size`: rollout groups consumed per train step.
- `prompt_repeat_k`: number of responses per prompt, configured in `SamplerConfig`.
- `total_train_steps` or `total_epochs`: one must be present unless debug train mode is used.
- `enable_evaluate`, `evaluate_step`, `eval_agent_loop_manager_cfg`, `evaluator_config`.

### Colocated asynchronous GRPO

Use `RLColocateTrainerConfig` with:

- `AsyncReplayBufferConfig()`;
- `AsyncProduceStrategyConfig(over_sample_threshold=..., enable_partial_rollout=..., max_staleness=..., tail_batch_trigger_size=...)`;
- a shared `resources` pool.

Choose this when rollout is the bottleneck but the run still uses a single accelerator pool. The async strategy may oversample, continue partial rollouts, and reuse samples subject to staleness policy.

Important staleness rule:

```text
stale_threshold = (max_staleness + 1) * sync_weights_interval
```

Practical guidance:

- `over_sample_threshold=0` behaves closer to synchronous production.
- `over_sample_threshold>0` lets rollout get ahead of the current train step.
- `max_staleness=0` still allows the natural lag inside the current synchronization interval.
- If `max_staleness>0`, prefer `enable_partial_rollout=True`; otherwise repeated abort/reset loops can hurt throughput because there is no retry-count-driven tail-batch escape.
- `tail_batch_trigger_size` helps recycle expired or long-tail samples into a final fill-up batch.

### Disaggregated RL

Use `RLDisaggregatedTrainerConfig` with:

- separate `train_resources` and `rollout_resources`;
- `DisaggAgentLoopManagerConfig` and `DisaggTaskSpecConfig` for the training producer;
- `DisaggAsyncProduceStrategyConfig` for training production;
- ordinary `AgentLoopManagerConfig` plus `SyncProduceStrategyConfig()` for evaluation;
- `AsyncReplayBufferConfig()`.

Choose this when rollout is significantly slower than training and the user has dedicated train and rollout accelerator pools. Runtime flow:

```text
background rollout producer -> replay buffer -> background rollout producer -> ...
foreground trainer: get batch -> train -> sync point -> pause producer -> sync weights/evaluate/save -> resume producer
```

Disaggregated caveats:

- `--num-workers` does not rewrite disaggregated `train_resources` or `rollout_resources`; use config env vars or edit the config copy.
- Train and rollout resource pools should be different pools in the Ray placement plan.
- Keep the default `should_continue_fn`; custom early-stopping logic can desynchronize background production and foreground consumption.
- `evaluate_step`, `checkpoint_interval`, and `hf_interval` still need to align with `sync_weights_interval`.

## Case 1: async GSM8K launch plan

For a config patterned after `rl_grpo_gsm8k_async.py`, expect these env-driven fields:

| Input | How the config uses it |
| --- | --- |
| `WORK_DIR` | Trainer runtime directory for logs, checkpoints, debug/trace outputs, and backend logs. |
| `MODEL_PATH` | HF model snapshot or model id used by `get_model_config_from_hf`, `RolloutConfig.model_path`, `WorkerConfig.load_from`, tokenizer path, and agent-loop checkpoint. |
| `DATA_PATH` | Training JSONL path used by `DatasetConfig(..., anno_path=data_path)`. |
| `EVAL_DATA_PATH` | Evaluation JSONL path used by eval `DatasetConfig`. |
| `WORLD_SIZE` | Multiplies the colocated `resources.num_workers` by nodes in some example configs. |
| `TRAIN_BATCH_SIZE` | Overrides the training batch size. |
| `LOSS_TYPE`, `LOSS_MODE`, `SP_SIZE` | Optional loss and sequence-parallel knobs. |
| `ENABLE_RETURN_ROUTED_EXPERTS` | Optional rollout routed-experts tracing for MoE workflows. |

Plan:

1. Use the command builder with local model/data/work paths and the selected backend.
2. Confirm the config uses `AsyncReplayBufferConfig()` and `AsyncProduceStrategyConfig(...)`.
3. Check `prompt_repeat_k`, `train_batch_size`, and `resources.num_workers` together. For GRPO, the batch should contain complete prompt groups.
4. Check `max_prompt_length + max_response_length == rollout_config.context_length` or equivalent context planning.
5. Start Ray with enough accelerators, CPUs, and memory before running the CLI.
6. Watch for rollout-controller progress, trajectory JSONL messages, trainer prepared-batch logs, evaluation logs, and checkpoint/HF-save intervals.

## Case 2: reward/backend diagnosis

When a run fails before useful rollout:

1. If the error says `reward_model` or `ground_truth` is missing, inspect one data record. GSM8K-style `NativeJudger` extracts `rollout_state.reward_model.get("ground_truth")`; without it, judging asserts before a reward is produced. Route conversion or schema repair to `data-preparation`.
2. If the error says no rollout backend is supported, verify exactly one backend flag is active and that the corresponding package imports in the runtime environment.
3. If Ray resource assertions fire, check Ray status before changing trainer config; the config may be valid but the Ray head may have been started with too few visible accelerators or CPUs.
4. If async production stalls with expired or aborted samples, review `over_sample_threshold`, `max_staleness`, `enable_partial_rollout`, `tail_batch_trigger_size`, and `sync_weights_interval` together rather than changing only one knob.

## Evaluation and outputs

- `EvaluatorConfig` defaults to accuracy-like reward metrics when `compute_metric_func=None`.
- Evaluation runs at weight synchronization points. `evaluate_step` must be a multiple of `sync_weights_interval` when evaluation is enabled.
- `debug_rollout=True` saves rollout debug tensors under `debug_rollout_dir`; `debug_train=True` reads those files for training-side debugging. They are mutually exclusive.
- `TraceConfig(enabled=True, enable_rollout_trace=True)` writes OpenTelemetry traces under the configured trace output directory or under the trainer work directory default chosen at runtime.
- Some agent-loop variants write per-sample traces under `$WORK_DIR/trace/`; if `WORK_DIR` is unset, those trace writers degrade to disabled mode.
