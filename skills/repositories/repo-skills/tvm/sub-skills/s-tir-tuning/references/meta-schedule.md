# Meta-Schedule Workflow Notes

## Verified `tune_tir` signature

```python
tvm.s_tir.meta_schedule.tune_tir(
    mod,
    target,
    work_dir,
    max_trials_global,
    *,
    max_trials_per_task=None,
    num_trials_per_iter=64,
    builder="local",
    runner="local",
    database="json",
    cost_model="xgb",
    measure_callbacks="default",
    task_scheduler="gradient",
    space="post-order-apply",
    strategy="evolutionary",
    num_tuning_cores="physical",
    seed=None,
    module_equality="structural",
    special_space=None,
    post_optimization=False,
)
```

The return value is a meta-schedule database. Use a small, disposable
`work_dir`, a tiny `max_trials_global`, and an LLVM target that declares
`num-cores` for the first smoke unless the user has prepared a GPU or RPC
runner. The default meta-schedule CPU rules expect the target to expose core
count information.

## Choice matrix

| Parameter | CPU smoke choice | When to change |
|---|---|---|
| `target` | `Target({"kind": "llvm", "num-cores": 8})` | Use `"cuda"` or a detailed target only after backend verification |
| `max_trials_global` | 1-16 | Increase only for approved tuning budget |
| `builder` | `"local"` | Custom builders when integrating CI or constrained devices |
| `runner` | `"local"` | `"rpc"` for remote hardware; then use rpc-deployment first |
| `database` | `"json"` in a temp work dir | `"memory"` for ephemeral tests or custom database for reuse |
| `cost_model` | `"xgb"` if XGBoost is installed, otherwise `"random"` for smoke | Use `"mlp"` or custom model only with dependency/budget approval |
| `space` | `"post-order-apply"` | `"union"` or callable spaces for custom schedule spaces |
| `strategy` | `"evolutionary"` | Replay strategies for deterministic trace/debug experiments |

## Bounded CPU tuning skeleton

```python
from pathlib import Path
import tempfile
import tvm
from tvm import te
from tvm.target import Target
from tvm.s_tir import meta_schedule as ms

n = 64
A = te.placeholder((n,), name="A")
B = te.compute((n,), lambda i: A[i] + 1, name="B")
mod = tvm.IRModule.from_expr(te.create_prim_func([A, B]))
work_dir = Path(tempfile.mkdtemp(prefix="tvm-ms-"))
db = ms.tune_tir(
    mod,
    target=Target({"kind": "llvm", "num-cores": 8}),
    work_dir=str(work_dir),
    max_trials_global=1,
    num_trials_per_iter=1,
    runner="local",
    database="json",
    cost_model="random",
    seed=0,
)
print(type(db))
```

This is a smoke pattern, not a performance benchmark. It proves basic API,
space generation, builder/runner/database plumbing, and target use. It does not
prove useful performance or GPU readiness.

## RPC runner boundary

When a task uses `runner="rpc"`, first establish the tracker/server/proxy
contract with the rpc-deployment sub-skill. Record host, port, key, timeout,
remote target, and target-device runtime availability. Do not begin a tuning run
until the remote can upload/load/run a small module.

## Database handling

- JSON databases are portable for short local experiments but can become stale
  when the target, IRModule, schedule rules, or TVM version changes.
- Memory databases are useful for tests but vanish after the process exits.
- If tuning writes no useful records, inspect the measure results before
  changing schedule rules; the issue may be target, runner, timeout, or cost
  model configuration.
