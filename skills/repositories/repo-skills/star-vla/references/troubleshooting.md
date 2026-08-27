# Cross-cutting Troubleshooting

## When to read

Read this for errors that cut across model, data, training, benchmark, and deployment workflows. If the symptom is clearly scoped, follow the linked sub-skill troubleshooting file.

## First triage

1. Identify the workflow: framework selection, dataset integration, training, benchmark evaluation, or policy serving.
2. Run the safest available check:
   - install/import: [../scripts/check_starvla_install.py](../scripts/check_starvla_install.py)
   - config summary: [../scripts/inspect_starvla_config.py](../scripts/inspect_starvla_config.py)
   - framework registry: [../sub-skills/model-frameworks/scripts/inspect_framework_registry.py](../sub-skills/model-frameworks/scripts/inspect_framework_registry.py)
   - modality schema: [../sub-skills/data-integration/scripts/validate_modality_json.py](../sub-skills/data-integration/scripts/validate_modality_json.py)
   - training command plan: [../sub-skills/training-config/scripts/plan_training_command.py](../sub-skills/training-config/scripts/plan_training_command.py)
   - benchmark plan: [../sub-skills/benchmark-evaluation/scripts/plan_benchmark_eval.py](../sub-skills/benchmark-evaluation/scripts/plan_benchmark_eval.py)
   - policy contract: [../sub-skills/policy-deployment/scripts/check_policy_server_contract.py](../sub-skills/policy-deployment/scripts/check_policy_server_contract.py)
3. Do not run downloads, training, simulator evaluation, or real-robot control until the safe checks explain what will happen.

## Symptom map

| Symptom | Likely owner | Read next |
| --- | --- | --- |
| `Framework ... is not implemented`, empty registry, stale framework name | model selection/registry | [model-frameworks troubleshooting](../sub-skills/model-frameworks/references/troubleshooting.md) |
| Missing pretrained model directory, flash-attn import failure, action head shape mismatch | model/backend | [model-frameworks troubleshooting](../sub-skills/model-frameworks/references/troubleshooting.md), then this file's backend section |
| `Expected KEY=VALUE`, bare string override rejected, override does not take effect | config/training | [training-config troubleshooting](../sub-skills/training-config/references/troubleshooting.md) |
| `data_mix` missing, `modality.json` missing, wrong language field, statistics/cache issue | dataset registry/data | [data-integration troubleshooting](../sub-skills/data-integration/references/troubleshooting.md) |
| Simulator import/render error, MuJoCo/Vulkan error, benchmark script cannot connect to server | benchmark evaluation | [benchmark-evaluation troubleshooting](../sub-skills/benchmark-evaluation/references/troubleshooting.md) |
| Server response has `actions` but client expects `normalized_actions`, wrong `unnorm_key`, ZMQ codec error | policy serving/client | [policy-deployment troubleshooting](../sub-skills/policy-deployment/references/troubleshooting.md) |

## Install/import failures

### `ModuleNotFoundError` during safe inspection

Likely causes:

- StarVLA is not installed in the active environment.
- The task is using a local checkout that is not on `PYTHONPATH`.
- Optional data/deployment dependencies are missing.

Recovery:

1. Run the install checker with `--repo-root` if using a checkout.
2. Confirm that `starVLA` and `deployment` imports are both available when deployment is needed.
3. Install only the missing dependency surface for the task. Do not install all benchmark/simulator dependencies just to answer a config question.

### Dependency conflict after installing benchmark packages

Likely causes:

- Benchmark clients pin older `numpy`, MuJoCo, or simulator packages.
- StarVLA server environment and simulator environment were merged.

Recovery:

1. Split environments: StarVLA server/training in one environment, simulator client in another.
2. Re-run root import checks in the StarVLA environment.
3. Re-run benchmark-specific smoke checks in the simulator environment.

## Backend and accelerator issues

### CPU import passes but training/evaluation fails on GPU

A CPU import does not validate GPU wheels, CUDA kernels, flash-attn, DeepSpeed, memory, or simulator rendering.

Recovery:

1. Verify backend-specific PyTorch in the target environment.
2. Check a tiny device tensor allocation.
3. Install flash-attn or vendor packages only after torch/backend is verified.
4. For ROCm or NPU, use the vendor-specific torch stack and attention override guidance rather than CUDA wheels.

### Flash-attn or compiled extension failure

Symptoms include build errors, ABI errors, `undefined symbol`, `no kernel image`, or import-time crashes.

Recovery:

1. Check torch version, CUDA/ROCm/NPU runtime, Python version, compiler/toolkit, and GPU architecture.
2. Prefer the repo-documented version when it matches the host.
3. If the workflow can use SDPA/native attention, select that fallback for inspection or evaluation.
4. Do not mark GPU capability verified until a backend smoke passes.

## Configuration and data coupling

Many StarVLA failures are cross-skill because model, data, and deployment share dimensions and statistics.

Check these together:

- `framework.action_model.action_dim` equals the sum of selected action key widths.
- `framework.action_model.state_dim` equals the sum of selected state key widths when state is used.
- `action_horizon` matches the `DataConfig.action_indices` length.
- `data_mix` selects the intended robot type and statistics key.
- The checkpoint is paired with the correct `config.yaml` and `dataset_statistics.json`.
- Deployment clients pass `unnorm_key` for multi-dataset checkpoints.

Use [inspect_starvla_config.py](../scripts/inspect_starvla_config.py) and [validate_modality_json.py](../sub-skills/data-integration/scripts/validate_modality_json.py) before retrying long jobs.

## Stale docs or checkpoint semantics

StarVLA evolves quickly. Some older examples or prose may still describe:

- `normalized_actions` returned by the server; current server-side unnormalization returns `actions`.
- Older `framework.framework_py` style fields; current construction uses `framework.name`.
- Historical action-head semantics for released checkpoints.

Recovery:

1. Prefer current deployment/server references in this skill for live response contracts.
2. Prefer checkpoint-paired config/statistics for exact checkpoint reproduction.
3. Use documented config overrides instead of editing checkpoint config files in place.

## Safety boundaries

Stop and ask before:

- Downloading large datasets or pretrained checkpoints.
- Installing broad GPU/simulator/robot SDK stacks into a user environment.
- Launching distributed training, simulator benchmark sweeps, or physical robot control.
- Deleting caches, videos, checkpoints, or result directories.
- Modifying a checkpoint's saved config instead of applying runtime overrides.
