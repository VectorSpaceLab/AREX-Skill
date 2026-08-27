# Debugging, profiling, auto-placement, parity, and CI selection

Use this reference to choose a low-risk verification path, interpret performance artifacts, or decide which CI/test family is relevant. It intentionally starts with read-only/static work and escalates only when the user approves cost and hardware use.

## Verification ladder

1. **Artifact inspection:** run [`../scripts/check_run_artifacts.py`](../scripts/check_run_artifacts.py) on existing outputs.
2. **Config matrix/static review:** run [`../scripts/summarize_config_matrix.py`](../scripts/summarize_config_matrix.py) on user-provided config roots; manually inspect only the narrow config family that matters.
3. **Import/static unit checks:** choose narrowly scoped CPU-safe tests for config parsing, metric utilities, placement, package import, or pure functions.
4. **Backend-specific unit checks:** run only after confirming CUDA/ROCm/MUSA/Ascend or graphics prerequisites.
5. **Small e2e smoke:** use minimal dummy/simulator configs; avoid downloading assets or moving robots.
6. **Full e2e/eval/parity:** run only with explicit user approval, correct environment, model assets, baseline logs, and time budget.

Do not treat a passing CPU import as proof of GPU rollout, SGLang/vLLM, simulator rendering, or hardware robot readiness.

## Profiling and tracing

RLinf has two complementary observability paths:

| Tool | Scope | Use when | Output |
| --- | --- | --- | --- |
| GPU/system profiling | Worker process level via Nsight Systems or ROCm Systems Profiler wrappers | Need kernel/memory/CPU details for selected worker groups | Profiler reports under a profiling output directory, defaulting to the run logger path plus experiment name and `profiling/` |
| Tracing | RLinf runner/worker timed sections across the distributed job | Need high-level overlap/critical-path view with low overhead | JSONL trace events, defaulting to `<log_path>/<experiment_name>/trace/trace_events.jsonl` |

Common profiling fields:

```yaml
cluster:
  profiling:
    backend: nsight        # or rocprof_sys
    enabled: true
    worker_groups: [ActorGroup, RolloutGroup, EnvGroup, Actor, Rollout, Env]
    steps: [3]
    output_dir: null
```

Notes:

- If `enabled: false`, workers are not wrapped and no profiling output is created.
- `worker_groups: null` profiles no workers. List both compute groups and channel groups when needed; channel workers are separate from compute worker groups.
- Restrict `steps` for long jobs; Nsight collection can be large.
- Nsight option maps produce flags such as short `-t cuda,cudnn,cublas,nvtx,osrt` and long `--backtrace=fp`.
- ROCm profiling requires `rocprof-sys-python` on worker `PATH`; environment variables can be injected under the profiling config.

Tracing fields:

```yaml
cluster:
  tracer:
    enable: true
    output_file: null
```

Trace visualization workflow:

1. Locate `trace_events.jsonl`.
2. Convert JSONL to a JSON array with a JSON-lines aggregation tool.
3. Open the JSON in Perfetto UI or a Chrome tracing viewer.
4. Compare runner spans (`step`, `generate_rollouts`) with worker spans such as `actor/run_training`, `rollout/generate`, and `env/interact`.

## Auto-placement workflow

Auto-placement uses profile data to suggest `cluster.component_placement` for RL training workflows. Use it after a small representative run, not before understanding the config.

Required profile data fields:

```yaml
profile_data:
  actor_cost: <seconds-per-iteration>
  inference_cost: <seconds-per-iteration>
  rollout_cost: <seconds-per-iteration>
```

Planning flow:

1. Run or inspect a collocated baseline for a few iterations and record average actor/inference/rollout costs.
2. Confirm total GPUs/nodes and whether actor, rollout, inference, reward, or critic components are present.
3. Run the auto-placement tool or equivalent static scheduler with the profile data.
4. Check the proposed component placement does not exceed cluster capacity and respects model-parallel contiguity requirements.
5. Apply only the placement section to the target YAML and keep all other training/eval semantics unchanged.
6. Re-run a small smoke before launching a long job.

Known placement sanity checks:

- Collocated mode has actor and rollout on the same GPU set; dedicated inference should not be specified.
- Disaggregated mode has disjoint actor/rollout/inference/critic sets.
- Auto mode requires actor → rollout → inference order across the accelerator range and currently has critic limitations.
- Tensor/pipeline parallel sizes must fit world sizes; actor TP and rollout TP divisibility matters in collocated mode.

## Parity and log analysis

RLinf parity tooling batch-runs selected experiments, checks log progress/crashes, extracts `success_once`, plots curves, and compares against baseline logs.

Distilled behavior:

- Task rows encode env name, model name, virtual environment name, YAML/config name, node count, step target, and save interval.
- A log checker scans `Global Step: current/total` and error fragments such as traceback, exception, killed/OOM, CUDA OOM, runtime error, assertion, keyboard interrupt, segmentation fault, or abort.
- If any run reaches the step threshold, it is considered reached; if none reach and any crashed, it is marked crashed.
- Success parsing extracts `success_once` from printed metric tables and can fall back to the last observed step when the target step is absent.
- Baseline matching relies on experiment-directory suffixes ending in the config name; missing baselines should be reported as skipped comparison, not as model failure.

Use parity analysis for regression investigations after a known-good baseline exists. Do not invent baseline metrics or compare across changed coverage settings, env seeds, action chunks, or model checkpoints.

## CI families and safe selection

RLinf CI groups are selected by changed-file filters. Use the conceptual mapping below when recommending local or CI-equivalent checks:

| Change area | Low-risk first checks | Escalation |
| --- | --- | --- |
| Scheduler, channels, placement, metric utilities, package structure | package import, pure unit tests, doctest-like scheduler checks, config matrix inspection | scheduler e2e, auto-placement e2e, dynamic scheduler e2e |
| Logger/checkpoint/resume/runner logic | artifact checker on synthetic layouts, metric utility tests, runner config validation | minimal training smoke with short `max_steps` and save interval |
| Embodied env/model/eval configs | config matrix, static YAML preflight, asset/model path checklist | small simulator e2e or embodied eval smoke; full benchmark only with assets/GPU budget |
| Reasoning/agent rollout backends | static YAML/backend compatibility, package import, small config smoke | SGLang/vLLM or Megatron e2e with correct engine environment |
| SFT/offline RL/data pipelines | data schema inspection, checkpoint/artifact checks, small dataset sample | SFT/offline e2e after data/model paths exist |
| Toolkits/data utilities | read-only metadata checks and dry-run-equivalent review | copy-mode conversion/visualization on a sample directory |
| Docker/install | lint/static review of install matrix | image build or install workflow on matching hardware |

CI labels and workflow dispatch are project-governance details. If the user asks only for diagnosis, do not trigger CI or long local e2e by default.

## What to collect before escalation

- Exact config name and overrides.
- Logger path and experiment name.
- Highest printed global step and last metric table.
- First root-cause error fragment, not only final Ray wrapper.
- GPU/accelerator type, driver, and graphics capability when simulator/rendering involved.
- Ray cluster topology and component placement summary.
- Model path, checkpoint path, LoRA/norm-stat/tokenizer paths as applicable.
- Whether cloud logger credentials are expected or disabled.
- Which artifacts exist: logs, checkpoints, videos, profiling, trace, tensorboard/wandb/swanlab directories.
