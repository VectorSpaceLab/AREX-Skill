# Metrics, logging, checkpoints, and resume

Use this reference when inspecting RLinf output directories, explaining metric keys, configuring loggers, or planning a checkpoint resume. It distills the logger, metric aggregation, checkpoint, and runner behavior into a self-contained checklist.

## Logger backends

RLinf's `MetricLogger` supports three backend names:

- `tensorboard`
- `wandb`
- `swanlab`

`runner.logger.logger_backends` may be a string, list, empty list, or `null`. The default is TensorBoard when no backend is specified. Multiple backends run in parallel.

Core logger fields:

```yaml
runner:
  logger:
    log_path: <run-output-root>
    project_name: rlinf
    experiment_name: <experiment-name>
    logger_backends: [tensorboard, wandb, swanlab]
```

Backend directories are created under `log_path`:

```text
<log_path>/
├── tensorboard/
├── wandb/
├── swanlab/
└── worker_logs/        # only when per-worker logging is enabled
```

Important operational details:

- TensorBoard writes scalar events and a resolved `config.yaml` below its backend directory.
- W&B may require `wandb login`, `wandb_entity`, and optionally `wandb_proxy`.
- SwanLab may require `swanlab login`; `swanlab_mode` defaults to `cloud`.
- `runner.per_worker_log: true` creates scoped loggers under `runner.per_worker_log_path` or `<log_path>/worker_logs`, grouped by worker group and rank.
- `MetricLogger.finish()` closes all active backends; abrupt process death can leave cloud runs open or partially synced.

## Metric namespaces

RLinf prints and logs metrics using slash-prefixed namespaces. Common keys:

| Namespace | Examples | Meaning and first checks |
| --- | --- | --- |
| `train/` | `train/actor/policy_loss`, `train/actor/approx_kl`, `train/actor/clip_fraction`, `train/actor/grad_norm`, `train/actor/lr`, `train/critic/value_loss`, `train/critic/explained_variance`, `train/loss` | Actor/critic optimization health. Large KL, exploding grad norm, or NaN/inf loss points to learning-rate, batch, mask, precision, or reward-scale issues. |
| `rollout/` | `rollout/rewards`, `rollout/advantages_mean`, `rollout/advantages_min`, `rollout/advantages_max`, `rollout/returns_mean` | Advantage/reward distribution collected from rollout. Flat rewards or NaNs point to reward/env/model mismatch before blaming optimizer. |
| `env/` | `env/success_once`, `env/return`, `env/reward`, `env/episode_len`, `env/num_trajectories` | Simulator task metrics during training. For embodied sparse rewards, `env/success_once` is the clearest success-rate signal. |
| `eval/` | `eval/success_once`, `eval/return`, `eval/num_trajectories` | Evaluation-only metrics. A final eval run logs once at step 0; training runners log eval metrics at validation intervals. |
| `time/` | `time/step`, `time/env/*`, `time/rollout/*`, `time/actor/*`, `time/reward/*` | Critical-path timing. Use with tracing/profile output when diagnosing throughput. |
| `replay/` or replay-buffer subkeys | `replay/intervention_rate`, `replay/record_transition_rate`, `train/replay_buffer/*` | Replay/intervention diagnostics for data-collection or RLPD-style flows. |

The printed metric table groups keys into Time, Environment, Rollout, Evaluation, Replay Buffer, Training/Actor, Training/Critic, and Training/Other sections and is appended to `<log_path>/metrics.log` when the runner supplies a log path.

## Reading run logs

When diagnosing a run:

1. Find the earliest log file with a Python traceback, Ray task error, `RuntimeError`, `Error:`, `Exception:`, `Killed`, `OOM`, `CUDA out of memory`, `Segmentation fault`, or `Aborted`.
2. Check the last complete metric table. Record the highest `Global Step`, `success_once`, and whether time metrics were still moving.
3. Distinguish primary and secondary failures. SGLang, CUDA OOM, asset, or model-load failures often happen before Gloo/NCCL timeouts.
4. Use [`../scripts/check_run_artifacts.py`](../scripts/check_run_artifacts.py) to list log/checkpoint/video/config artifacts without modifying them.

## Checkpoint cadence

`runner.save_interval` controls periodic saves. Runners use the helper that saves when:

- `save_interval > 0`, and
- the current global step is divisible by `save_interval`, or
- the run reaches the train end, or
- runtime limit handling asks for a final save.

If validation is enabled, `save_interval` must be divisible by `runner.val_check_interval` unless checkpointing is disabled with a negative save interval. Misaligned intervals fail early.

`runner.resume_dir` is the path to a `global_step_<N>` checkpoint directory, or `null`/unset for a fresh run. Reasoning runners also support `resume_dir: auto`, which chooses the highest `global_step_<N>` under the logger checkpoint root.

## Checkpoint layouts

### Embodied/FSDP-style runner layout

Embodied, SFT, and offline-style FSDP runs normally save under logger path plus experiment name:

```text
<log_path>/<experiment_name>/checkpoints/global_step_<N>/
└── actor/
    ├── dcp_checkpoint/        # distributed checkpoint shards when used
    │   ├── __0_0.distcp
    │   └── ...
    └── model_state_dict/
        └── full_weights.pt    # consolidated weights for eval/conversion when emitted
```

Some actor workers add replay-buffer, value-model, policy-head, or rank-local files beneath `actor/`; inspect layout before assuming a single weight file is enough.

### Reasoning/Megatron-style runner layout

Reasoning/coding-online RL Megatron-style runs save under output directory plus experiment name:

```text
<output_dir>/<experiment_name>/checkpoints/global_step_<N>/
├── actor/
│   ├── iter_00000<N>/
│   │   ├── mp_rank_00/
│   │   │   ├── distrib_optim.pt
│   │   │   └── model_optim_rng.pt
│   │   └── ...
│   └── latest_checkpointed_iteration.txt
├── critic/                    # present only for actor-critic/critic runs
└── data/
    └── data.pt                # dataloader/sampler state when saved
```

This layout preserves sharded model/optimizer/RNG state and data-sampler state. `data.pt` missing during resume is a warning for reasoning: training can continue, but sample order may restart.

### Evaluation checkpoints

Standalone embodied evaluation does not train or save actor checkpoints. It may load:

- `runner.ckpt_path`: a consolidated `.pt`/`full_weights.pt` style checkpoint.
- `rollout.model.model_path`: base or deploy model directory.
- model-family extras such as LoRA paths, tokenizer paths, norm stats, or config paths.

## Resume procedure

1. **Choose the exact checkpoint root.** Use the highest complete `global_step_<N>` directory, not a partial rank directory. Confirm `actor/` exists; for actor-critic/reasoning, also check `critic/` if the config expects it.
2. **Confirm config compatibility.** Resume with the same model family, backend, tensor/pipeline parallel sizes, component placement, tokenizer/model paths, data source, and env/task setup. Changing these can break shard loading or silently change training semantics.
3. **Set `runner.resume_dir`.** It must point to the selected `global_step_<N>` directory. Use `resume_dir: auto` only for runners that implement it and only when the checkpoint root contains one run family.
4. **Relaunch with the same training entrypoint and cluster shape.** The runner parses `N` from `global_step_<N>`, loads actor/critic checkpoints, and restores sampler state when available.
5. **Verify resume.** The next printed metric table should continue from step `N+1` or the runner's step convention immediately after `N`; the next save should follow the configured `save_interval`.

Do not delete failed partial checkpoints unless the user explicitly asks. Prefer choosing an older complete checkpoint.

## Conversion and deployment guardrails

Checkpoint conversion is useful but mutating/heavy. Before running any converter:

- Confirm the source layout: FSDP DCP shards, consolidated `full_weights.pt`, Megatron sharded actor, OpenPI JAX/Orbax, OpenPI PyTorch, or OpenPI_RLinf.
- Confirm target format: HuggingFace/safetensors, OpenPI_RLinf bare layout, OpenPI PyTorch layout, or deploy `full_weights.pt`.
- Confirm dtype policy (`fp32` vs `bf16`) and whether it is a storage cast or runtime compute hint.
- Write to a new output directory. Never overwrite a training checkpoint in place.
- Preserve norm-stat files verbatim for OpenPI-family conversions; wrong norm stats can produce abnormal actions even when weights load.
- For conversions that need a reference model to supply missing heads or validate shapes, treat the reference as required. Do not emit an incomplete checkpoint.

If conversion fails after writing partial files, keep them isolated and report the target path as suspect rather than retrying in the same directory.
