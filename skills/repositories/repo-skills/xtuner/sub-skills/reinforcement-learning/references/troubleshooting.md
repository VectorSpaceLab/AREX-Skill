# XTuner RL Troubleshooting

Use this reference to diagnose XTuner RL/GRPO pre-launch and early-runtime failures. Fix data schemas in `data-preparation`, deep model/backend sizing in `model-backends`, and generic SFT issues in `training`.

## Quick triage order

1. **Config loads?** Verify the Python config defines top-level `trainer` and imports required XTuner/RL modules.
2. **Required env vars present?** Check `WORK_DIR`, `MODEL_PATH`, `DATA_PATH`, and `EVAL_DATA_PATH` for env-driven example configs.
3. **Ray is running?** The CLI calls `ray.init(address="auto")`; start/connect Ray before the CLI.
4. **One backend active?** Exactly one of `XTUNER_USE_LMDEPLOY`, `XTUNER_USE_SGLANG`, or `XTUNER_USE_VLLM` should be `1`, and that package must import.
5. **Resources fit Ray?** Compare trainer resource configs with `ray.available_resources()`.
6. **Reward data valid?** GSM8K-style judgers require `reward_model.ground_truth` and a non-empty response before scoring.
7. **Intervals valid?** Evaluation/checkpoint/HF intervals must align with `sync_weights_interval`.
8. **Async policy coherent?** Review `over_sample_threshold`, `max_staleness`, `enable_partial_rollout`, `tail_batch_trigger_size`, and replay buffer type together.

## Symptom table

| Symptom / message | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ray'` while invoking the RL CLI | RL dependencies are not installed in the active Python environment. | Install RL deps such as `ray[default]` and `httpx` in the XTuner runtime environment, then rerun a help/import check. |
| `ray.init(address="auto")` fails or cannot find a cluster | Ray head was not started, or the driver cannot discover it. | Start a local/multi-node Ray cluster externally; verify with a small `ray.init(address="auto")` probe before running XTuner. |
| `Ray must be initialized before creating AcceleratorResourcesConfig` | Resource validation ran before Ray initialization. | Initialize/connect Ray before calling resource validation or trainer build. |
| `Unsupported rollout backend: ... Please set XTUNER_USE_SGLANG, XTUNER_USE_VLLM, or XTUNER_USE_LMDEPLOY to 1.` | No backend env flag is active, or a wrapper cleared it. | Export exactly one backend flag and ensure the matching package imports. Use the bundled command builder to see the intended exports. |
| SGLang selected when user intended LMDeploy/vLLM | Multiple backend flags are `1`; SGLang takes precedence in the backend property. | Set unselected backend flags to `0` or unset them. |
| Backend import error for LMDeploy/SGLang/vLLM | Optional inference backend is not installed or incompatible with accelerator/Python/Torch stack. | Install a compatible backend wheel; if unavailable, switch backend and update env/config accordingly. Do not treat this as an XTuner data-schema issue. |
| `WORK_DIR`, `MODEL_PATH`, `DATA_PATH`, or `EVAL_DATA_PATH` KeyError | Env-driven example config reads `os.environ[...]` directly. | Export the missing variable, pass `--work-dir` as a CLI override where useful, or edit the config copy to use explicit paths. |
| Model path is rejected as not HF-compatible | `load_from`/`MODEL_PATH` does not point to an HF snapshot/model id or lacks expected files such as `config.json`. | Fix model path/model id; route model-family/backend details to `model-backends` if the config needs a different model config. |
| `RolloutState must have reward_model with 'ground_truth' for judging` | GSM8K/native judger extracts `rollout_state.reward_model.get("ground_truth")`, but the data record lacks it. | Inspect one JSONL record; route conversion/validation to `data-preparation`. Expected GSM8K-style records include `prompt` and `reward_model: {"ground_truth": "...", "style": "rule"}`. |
| `RolloutState must have a response for judging` | Judger ran before successful generation or response detokenization. | Check rollout backend health, response status, and agent-loop completion. Ensure failed/aborted rollouts are not being judged. |
| `Not enough available GPUS/NPUS/CPUs/memory in Ray cluster` | Ray visible resources are smaller than `AcceleratorResourcesConfig` demand. | Check `ray.available_resources()`, `CUDA_VISIBLE_DEVICES`/NPU visibility, node count, `num_workers`, `num_cpus_per_worker`, and `cpu_memory_per_worker`. Lower config demand or restart Ray with correct visible resources. |
| CLI `--num-workers` does not change disaggregated resources | The CLI only overwrites `trainer.resources.num_workers` when a colocated `resources` field exists. | For `RLDisaggregatedTrainerConfig`, edit the config copy or env vars that feed `train_resources` and `rollout_resources`. |
| `evaluate_step` / `checkpoint_interval` / `hf_interval` validation error | Enabled interval is not a positive multiple of `sync_weights_interval`. | Set intervals to `-1`/`None` to disable or choose positive multiples of `sync_weights_interval`. |
| `debug_rollout and debug_train cannot be enabled at the same time` | Both debug modes are true. | Enable only one mode. For either mode, set `debug_rollout_dir`. |
| `debug_rollout_dir must be provided` | Debug rollout/train mode lacks an output/input directory. | Add a user-owned debug directory in the config copy. |
| Training stalls with many expired/stale samples | Async production is running too far ahead or staleness threshold is too strict. | Compute `(max_staleness + 1) * sync_weights_interval`; lower `over_sample_threshold`, increase staleness only if acceptable, tune `tail_batch_trigger_size`, and confirm `AsyncReplayBufferConfig()` is used. |
| Warning about `max_staleness > 0, enable_partial_rollout is False` | Long-tail samples can be retried repeatedly without partial continuation. | Prefer `enable_partial_rollout=True` when `max_staleness>0`, especially for long responses or tool-chain tasks. |
| Partial rollout continues with malformed context | Agent loop may not support continuation or trace/token fields may be incomplete. | Disable partial rollout for that agent loop, or use a loop/config that explicitly supports continuation and trace-store training segments. |
| `Global gradient tokens is 0` warning | No valid loss tokens in the prepared training batch. | Check rollout response IDs/labels, data filtering, `max_prompt_length`, `max_response_length`, pack length, and invalid rollout statuses. |
| FA3 runtime error when `XTUNER_USE_FA3=1` | FlashAttention v3 path requested but unavailable/incompatible. | Set `XTUNER_USE_FA3=0` or install a compatible FA3 stack. Deterministic SGLang wrappers set FA3 off. |
| Trace runtime complains about missing exporter/collector | `TraceConfig.enabled=True` but OpenTelemetry packages or `otelcol` binary are missing. | Disable tracing for the run or install required OTel exporter and collector binaries. |
| No per-agent trace files under `$WORK_DIR/trace/` | `WORK_DIR` was unset for agent-loop trace helpers, or trace-writing path is not used by the selected loop. | Set `WORK_DIR` and enable the relevant trace/debug config; verify the selected agent loop actually emits those files. |
| vLLM errors around token ids/input ids | Some XTuner vLLM rollout paths do not support `return_token_ids` or generation with `input_ids`. | Switch to LMDeploy/SGLang or adjust the rollout/agent loop to avoid unsupported token-in-token-out features. |
| Rollout health checks deactivate workers | Backend server is slow, OOMing, misconfigured, or timeout thresholds are too low. | Inspect backend logs under work dir, reduce context/batch/memory utilization, check `health_check_timeout_seconds` and `health_check_failure_threshold`, and verify backend import/device visibility. |

## Diagnosing missing required env vars

Many example configs use direct environment access:

```python
work_dir = os.environ["WORK_DIR"]
model_path = os.environ["MODEL_PATH"]
data_path = os.environ["DATA_PATH"]
eval_data_path = os.environ["EVAL_DATA_PATH"]
```

Preflight:

```bash
python - <<'PY'
import os
required = ["WORK_DIR", "MODEL_PATH", "DATA_PATH", "EVAL_DATA_PATH"]
missing = [k for k in required if not os.environ.get(k)]
print("missing=" + ",".join(missing) if missing else "all required env vars set")
PY
```

If `EVAL_DATA_PATH` is intentionally unused, edit the config copy to avoid direct `os.environ[...]` access or set evaluation off consistently (`enable_evaluate=False` and no initial/eval manager requirement).

## Diagnosing missing `reward_model.ground_truth`

For GSM8K-style RL records, a minimal record has:

```json
{
  "data_source": "openai/gsm8k",
  "prompt": [{"role": "user", "content": "..."}],
  "ability": "math",
  "reward_model": {"ground_truth": "72", "style": "rule"},
  "extra_info": {"split": "train"}
}
```

Preflight one record:

```bash
python - <<'PY' /data/gsm8k_train.jsonl
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    record = json.loads(next(f))
reward = record.get("reward_model") or {}
print("ground_truth=", reward.get("ground_truth"))
assert reward.get("ground_truth") not in (None, ""), "missing reward_model.ground_truth"
PY
```

If this fails, do not patch the judger first. Fix conversion/schema in `data-preparation`, because the reward signal is part of the dataset contract.

## Diagnosing missing inference backend

Preflight exactly one backend:

```bash
python - <<'PY'
import os
flags = {
    "sglang": os.environ.get("XTUNER_USE_SGLANG") == "1",
    "vllm": os.environ.get("XTUNER_USE_VLLM") == "1",
    "lmdeploy": os.environ.get("XTUNER_USE_LMDEPLOY") == "1",
}
active = [name for name, enabled in flags.items() if enabled]
print("active_backends=", active)
assert len(active) == 1, "set exactly one XTUNER_USE_* backend flag to 1"
PY
```

Then test the selected package import:

```bash
python - <<'PY'
import os, importlib
mapping = {
    "XTUNER_USE_SGLANG": "sglang",
    "XTUNER_USE_VLLM": "vllm",
    "XTUNER_USE_LMDEPLOY": "lmdeploy",
}
for env, module in mapping.items():
    if os.environ.get(env) == "1":
        importlib.import_module(module)
        print(f"{module} import ok")
PY
```

Backend import failures are resolved by installing a compatible backend or selecting a different backend; they are not solved by changing `RolloutConfig.model_path` alone.

## Diagnosing Ray/resource mismatch

Run after Ray starts:

```bash
python - <<'PY'
import ray
ray.init(address="auto")
print(ray.available_resources())
PY
```

Compare with config demands:

- colocated: `resources.num_workers`, `num_cpus_per_worker`, `cpu_memory_per_worker`, `accelerator`;
- disaggregated: both `train_resources` and `rollout_resources`;
- CPU judgers/agent loops: `CPUResourcesConfig` workers add more CPU actor demand;
- multi-node: confirm all worker nodes joined and expose the same accelerator type expected by config.

If Ray status shows fewer accelerators than expected, check the Ray start command and device visibility first. If Ray resources are correct but the config still fails, then adjust trainer config.

## Diagnosing stale rollouts and async partial rollout

Inspect these knobs together:

```text
sync_weights_interval
replay_buffer_config: AsyncReplayBufferConfig vs SyncReplayBufferConfig
over_sample_threshold
enable_partial_rollout
max_staleness
tail_batch_trigger_size
train_batch_size
prompt_repeat_k
```

Rules of thumb:

- Use `SyncReplayBufferConfig()` with `SyncProduceStrategyConfig()` for strict colocated runs.
- Use `AsyncReplayBufferConfig()` with async or disaggregated production.
- Effective stale threshold is `(max_staleness + 1) * sync_weights_interval`.
- If `max_staleness>0`, prefer `enable_partial_rollout=True` unless the agent loop cannot safely continue.
- If many samples expire, reduce oversampling or increase resources/backend throughput before loosening staleness for a strict on-policy experiment.
- If long responses often abort at synchronization, consider partial rollout and a larger `max_response_length`/context plan.

## Debug and trace directories

Trainer debug flags:

- `debug_rollout=True`: save rollout debug tensors/files under `debug_rollout_dir`.
- `debug_train=True`: consume debug rollout files for train-side replay; cannot be enabled with `debug_rollout`.
- `debug_rollout_dir` is required for either debug mode.

Trace flags:

- `TraceConfig.enabled=True`: enables trace runtime.
- `TraceConfig.output_dir`: explicit trace root; if omitted, runtime chooses a default under the run context.
- `TraceConfig.enable_rollout_trace=True`: adds rollout spans and carrier propagation.
- Agent-loop sandbox/localhost helpers may write additional JSONL traces under `$WORK_DIR/trace/` and diagnostics under `$WORK_DIR/trace/diagnostics/`.

If trace files are missing, verify both the trainer `TraceConfig` and the specific agent-loop trace writer. Some trace writers intentionally disable themselves when `WORK_DIR` is unset.
