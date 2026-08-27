---
name: ray
description: "Use Ray for distributed Python applications, clusters, Data
  pipelines, Train/Tune experiments, Serve deployments, and RLlib workloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray

Use this repo skill when a task is about Ray, `ray`, Ray Core, Ray clusters, Ray Data, Ray Train, Ray Tune, Ray Serve, or RLlib. Ray is a distributed Python runtime plus AI libraries for scalable data processing, training, tuning, serving, and reinforcement learning.

## Start Here

1. Confirm the user’s workflow and install surface. Prefer narrow extras such as `ray[default]`, `ray[data]`, `ray[train]`, `ray[tune]`, `ray[serve]`, or `ray[rllib]`; avoid `ray[all]` unless the user explicitly needs many unrelated Ray libraries.
2. Run the root environment checker when package state is unclear:

   ```bash
   python scripts/check_ray_environment.py --help
   python scripts/check_ray_environment.py --require core --require data --json
   ```

3. Route to the focused sub-skill before writing detailed code, commands, configs, or troubleshooting steps.
4. For cluster-mutating commands such as `ray start`, `ray stop`, `ray up`, `ray down`, `ray job submit`, or `serve deploy`, confirm the target cluster/address and side effects first.

## Route Map

| User task | Read |
| --- | --- |
| Use `ray.remote`, tasks, actors, `ObjectRef`, `ray.get`, `ray.wait`, resource annotations, object store behavior, or Core anti-patterns | `sub-skills/core-runtime/SKILL.md` |
| Operate clusters with `ray` CLI, Jobs, dashboard, runtime environments, `ray status`, `ray list`, logs, state APIs, or OOM observability | `sub-skills/cluster-ops/SKILL.md` |
| Build `ray.data` pipelines, load local/cloud data, transform rows/batches, write datasets, tune blocks/concurrency, or debug Data schemas/OOM | `sub-skills/data-pipelines/SKILL.md` |
| Use Ray Train or Tune for distributed training, checkpoints, storage, `Tuner`, `TuneConfig`, schedulers, resources, or `ResultGrid` | `sub-skills/train-tune/SKILL.md` |
| Build, run, deploy, lint, update, or troubleshoot Ray Serve apps, `@serve.deployment`, Serve YAML, `serve run`, or `serve deploy` | `sub-skills/serve-deployments/SKILL.md` |
| Configure RLlib `AlgorithmConfig`/`PPOConfig`, Gymnasium envs, EnvRunners, Learners, RLlib checkpoints, or RLlib Tune sweeps | `sub-skills/rllib-workloads/SKILL.md` |

## Cross-Workflow Rules

- Use `core-runtime` for Python runtime semantics even when a higher-level library starts Ray under the hood.
- Use `cluster-ops` for Jobs, dashboard, state, logs, and runtime environment packaging around any Ray application.
- Use `data-pipelines` for dataset construction before handing training/tuning to `train-tune` or model serving to `serve-deployments`.
- Use `train-tune` for generic Tune search spaces, schedulers, resources, result analysis, and storage; use `rllib-workloads` only for RLlib-specific config/env/algorithm work.
- Use `serve-deployments` for Serve application configs and lifecycle, but route generic cluster startup, dashboard, and node visibility back to `cluster-ops`.

## Installation And Import Checks

Ray’s Python package is distributed as `ray` and imports as `ray`. The source baseline for this skill supports Python `>=3.10`.

```bash
pip install ray
python - <<'PY'
import ray
print(ray.__version__)
PY
```

Choose extras by workflow:

```bash
pip install "ray[default]"  # cluster dashboard, jobs, state APIs
pip install "ray[data]"     # Ray Data readers/transforms
pip install "ray[train]"    # Ray Train
pip install "ray[tune]"     # Ray Tune
pip install "ray[serve]"    # Ray Serve
pip install "ray[rllib]" torch  # RLlib with common PyTorch backend
```

## Shared References

- Read `references/troubleshooting.md` for cross-cutting install/import, optional extras, Python version, cluster command safety, and workflow routing failures.
- Read `references/repo-provenance.md` when checking whether this skill is stale relative to a Ray checkout or package version.
- `references/repo-routing-metadata.json` is structured import metadata consumed by `repo-skills-router` during managed import.

## Bundled Root Script

- `scripts/check_ray_environment.py` checks package metadata, selected imports, optional CLI commands, and common workflow extras without starting a Ray cluster.

## Out Of Default Scope

This skill is Python-focused. Java, C++, LLM extra-extra workflows, heavy benchmarks, release engineering, CI/build infrastructure, cloud credential provisioning, Kubernetes operator deployment authoring, and GPU/service-specific notebooks are recorded as gaps unless the user explicitly asks for those areas and provides the needed environment or platform constraints.
