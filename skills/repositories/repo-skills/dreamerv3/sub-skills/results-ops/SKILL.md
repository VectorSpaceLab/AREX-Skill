---
name: results-ops
description: "Install and operate DreamerV3 environments and backends, inspect
  result logdirs, and summarize score artifacts without reopening the source
  repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Results And Operations

Use this sub-skill when a task is about making DreamerV3 runnable, checking optional environment/backend readiness, inspecting logdir outputs, viewing metrics, or summarizing benchmark score files.

Do **not** use this sub-skill for:

- choosing training commands, config blocks, tasks, or run scripts; route those decisions to `train-configure`.
- explaining the embodied environment step/space contract; route those details to `embodied-dataflow`.
- changing neural-network internals, JAX module structure, or model precision/device policies beyond operational install checks; route those details to `jax-models`.

## Read Or Run

- Read [references/install-and-backends.md](references/install-and-backends.md) before installing DreamerV3, selecting CPU/CUDA/Docker setup, or diagnosing optional suite dependencies.
- Read [references/results-and-plotting.md](references/results-and-plotting.md) when a user has a logdir, `metrics.jsonl`, `scores.jsonl`, Scope summaries, TensorBoard/WandB/Expa outputs, or gzipped benchmark score artifacts.
- Read [references/operations-checklist.md](references/operations-checklist.md) before long runs, while supervising a run, before resuming a stopped logdir, and after collecting artifacts.
- Read [references/troubleshooting.md](references/troubleshooting.md) for install/import/backend/viewer/plotting/optional-environment failures.
- Run [scripts/check_optional_env_imports.py](scripts/check_optional_env_imports.py) to identify which optional environment-suite Python modules are present without constructing the heavy environments.
- Run [scripts/metrics_summary.py](scripts/metrics_summary.py) to list scalar keys and summarize DreamerV3 `metrics.jsonl`, `scores.jsonl`, or gzipped score-record JSON with only Python standard-library dependencies.

## Fast Operating Recipes

### Check base package and backend readiness

```sh
python -m pip check
python - <<'PY'
import dreamerv3, embodied
from embodied.envs import dummy
import jax, jax.numpy as jnp
print('jax', jax.__version__, 'backend', jax.default_backend())
print('devices', jax.devices())
print('sum', float(jnp.array([1.0, 2.0]).sum()))
env = dummy.Dummy({'image': (8, 8, 3)}, {'action': (2,)})
print('dummy obs keys', sorted(env.obs_space.keys()))
PY
```

If this fails on an optional environment module but the selected task does not use that suite, treat it as optional rather than blocking the whole installation. Use the optional import checker to make the missing suite explicit.

### Inspect a logdir without Scope

```sh
python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --list-keys
python scripts/metrics_summary.py --input <logdir>/scores.jsonl --key episode/score --last 10
python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --key episode/length --last 10
```

If the key is absent, list keys first. DreamerV3 metric names commonly use slash-separated names such as `episode/score`, `episode/length`, `fps/train`, `replay/inserts`, and `train/loss/...`.

### View live summaries

```sh
python -m pip install -U scope
python -m scope.viewer --basedir <logdir-parent> --port 8000
```

Point Scope at a directory that contains one or more run logdirs. If Scope is unavailable, use the summary script above and the JSONL schema in [references/results-and-plotting.md](references/results-and-plotting.md).

## Contracts To Preserve

- DreamerV3 requires Python 3.11+ for the documented setup.
- The distribution name is `dreamer`; import roots are `dreamerv3` and `embodied`.
- The repo-declared base requirements pin `jax[cuda12]==0.4.33`; CPU-only use is possible by selecting the CPU JAX platform at runtime, while production defaults target CUDA.
- Base install/import/JAX CPU smoke and optional CUDA smoke were verified during skill construction. Optional environment-suite packages are intentionally not all required for every task.
- Runtime guidance in this sub-skill is self-contained. Do not require future agents to reopen the original repository to understand installation, result files, plotting concepts, or optional dependency failures.
