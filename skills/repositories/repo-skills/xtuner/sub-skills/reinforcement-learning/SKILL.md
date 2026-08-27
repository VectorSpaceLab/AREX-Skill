---
name: reinforcement-learning
description: "Plan and troubleshoot XTuner RL and GRPO workflows with Ray
  resource pools, rollout backends, agent loops, judgers, replay buffers,
  evaluation, tracing, and safe launch-command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# XTuner Reinforcement Learning

Use this sub-skill when a future Researcher needs to plan, review, or diagnose XTuner V1 reinforcement-learning runs, especially GRPO-style configs that combine Ray placement groups, rollout engines, agent loops, judgers, replay buffers, advantage/loss settings, evaluation, and trace/debug outputs.

This sub-skill is for operating guidance and safe command construction. It does not start Ray, launch training, download data, or require an XTuner source checkout.

## Route here when

- The task mentions XTuner RL, GRPO, DAPO-style examples, reward models, rollout generation, `RLColocateTrainerConfig`, or `RLDisaggregatedTrainerConfig`.
- The user needs a launch plan for an RL Python config using `--config`, `--work-dir`, and `--num-workers`.
- The user needs to choose colocated versus disaggregated resources, synchronous versus asynchronous rollout production, replay-buffer policy, or rollout staleness/partial-rollout settings.
- The user needs to select and configure LMDeploy, SGLang, or vLLM rollout services through XTuner environment flags.
- The user is diagnosing Ray initialization, missing backend packages, missing reward `ground_truth`, resource mismatch, stale rollouts, debug rollout files, evaluation intervals, or trace output.

## Route elsewhere

- JSONL schema validation, GSM8K conversion, media fields, tokenization, packing, and cache layout belong to `data-preparation`.
- Generic SFT/pretraining launch, direct SFT CLI arguments, torchrun planning, and training-log summaries belong to `training`.
- Model-family choice, FSDP/MoE/FP8/attention backend internals, tensor/expert parallel sizing, and optional acceleration kernels belong to `model-backends`.
- Legacy `xtuner` CLI tools, config-zoo search, old chat/eval commands, and model conversion belong to `cli-and-tools`.

## Fast operating procedure

1. **Confirm the topology.** Use [references/workflows.md](references/workflows.md) to choose colocated synchronous, colocated asynchronous, or disaggregated RL. Start with colocated + `SyncProduceStrategyConfig()` unless the user explicitly needs background rollout throughput or separate train/rollout resource pools.
2. **Confirm required paths and env vars.** Most XTuner RL example configs read `WORK_DIR`, `MODEL_PATH`, `DATA_PATH`, and `EVAL_DATA_PATH` from the environment. The CLI can override `cfg.trainer.work_dir` with `--work-dir` and can override `trainer.resources.num_workers` for colocated trainer configs that expose `resources`.
3. **Confirm the reward data contract.** GSM8K-style judgers expect each rollout sample to carry `reward_model.ground_truth`. If this field is absent, route schema conversion/validation to `data-preparation` before launching.
4. **Choose one rollout backend.** Set exactly one of `XTUNER_USE_LMDEPLOY=1`, `XTUNER_USE_SGLANG=1`, or `XTUNER_USE_VLLM=1`; see [references/cluster-and-backends.md](references/cluster-and-backends.md). Backend packages are optional and must be installed in the runtime environment before launch.
5. **Prepare Ray deliberately.** XTuner's RL CLI calls `ray.init(address="auto")` if Ray is not already initialized, so a Ray cluster or local Ray head must already be running. Check visible accelerator, CPU, and memory resources before training.
6. **Build a launch snippet safely.** Use [scripts/build_rl_command.py](scripts/build_rl_command.py) to emit shell exports plus the RL CLI command without starting Ray or training.
7. **Review trainer config fields.** Use [references/api-reference.md](references/api-reference.md) for `WorkerConfig`, `RolloutConfig`, `AgentLoopManagerConfig`, `SingleTurnAgentLoopConfig`, `GSM8KJudgerConfig`, `GRPOAdvantageConfig`, `GRPOLossConfig`, replay buffers, evaluator, resource, and trace configs.
8. **Diagnose by symptom.** Use [references/troubleshooting.md](references/troubleshooting.md) for Ray, backend, required-env, reward data, resource mismatch, stale rollout, async partial-rollout, debug, trace, and interval-validation failures.

## Minimal command-plan example

Generate a dry launch snippet for an async GSM8K GRPO config copy:

```bash
python sub-skills/reinforcement-learning/scripts/build_rl_command.py \
  --config /configs/rl_grpo_gsm8k_async.py \
  --backend lmdeploy \
  --model-path /models/qwen3-8b \
  --data-path /data/gsm8k_train.jsonl \
  --eval-data-path /data/gsm8k_val.jsonl \
  --work-dir /runs/qwen3-gsm8k-grpo \
  --num-workers 8
```

The helper emits the installed-package entry point `python -m xtuner.v1.train.cli.rl ...` so the generated skill does not require an XTuner source checkout.

## Difficult cases this sub-skill supports

- **Async GSM8K launch planning:** build a complete env-plus-command plan for a config patterned after `rl_grpo_gsm8k_async.py`, using local model, train data, eval data, work directory, backend, accelerator count, and `--num-workers` overrides.
- **Pre-launch diagnosis:** identify why a config fails before rollout when `reward_model.ground_truth` is missing and no inference backend flag/package is active, then route schema fixes and backend installation to the right owner.
