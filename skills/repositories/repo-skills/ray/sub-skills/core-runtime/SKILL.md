---
name: core-runtime
description: "Use Ray Core for Python tasks, actors, object refs, resources,
  runtime environments, and local runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray Core Runtime

Use this sub-skill when the task is about distributed Python with Ray Core primitives: `ray.init`, `ray.remote`, tasks, actors, `ObjectRef`, `ray.put`, `ray.get`, `ray.wait`, resource annotations, runtime environments, local startup/shutdown, or performance issues in task/actor/object workflows.

## Quick Start

```python
import ray

ray.init()  # Starts a local runtime or connects according to Ray's address rules.

@ray.remote
def square(value):
    return value * value

refs = [square.remote(i) for i in range(4)]
print(ray.get(refs))  # [0, 1, 4, 9]

ray.shutdown()
```

## Read Next

- Read `references/api-reference.md` for the verified Core API signatures, startup options, task/actor options, and object API behavior.
- Read `references/workflows.md` for recipes covering tasks, actors, object-store usage, `ray.wait` polling, resources, runtime environments, retries, and anti-pattern rewrites.
- Read `references/troubleshooting.md` when code blocks on `ray.get`, pins object-store memory, fails serialization, deadlocks on resources, exits workers, or leaks local Ray processes.
- Run `python scripts/core_smoke.py --help` for a safe helper. Add `--run-local` only when starting a tiny local Ray runtime is acceptable.

## Boundaries

- Use this sub-skill for Python Ray Core. C++ and Java APIs are out of scope.
- For Ray CLI, jobs, cluster startup, dashboard, and state commands, route to `../cluster-ops/SKILL.md`.
- For Ray Data datasets and IO pipelines, route to `../data-pipelines/SKILL.md`.
- For Ray Train or Tune orchestration, route to `../train-tune/SKILL.md`.
- For Ray Serve deployments, route to `../serve-deployments/SKILL.md`.
- For RLlib algorithms and environments, route to `../rllib-workloads/SKILL.md`.
