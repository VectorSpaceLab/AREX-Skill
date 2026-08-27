---
name: s-tir-tuning
description: "Guides TVM S-TIR scheduling, transformations, dlight rules,
  meta-schedule tuning, builders, runners, and CPU/GPU tuning decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# S-TIR Scheduling and Tuning

Use this route when a task involves `tvm.s_tir.Schedule`, schedule primitives,
transform passes, dlight/default schedules, meta-schedule, `tune_tir`, or
bounded tuning of TIR generated from Relax or TIRx.

## Route

1. Confirm TVM imports and the selected target is available. Use
   [`../install-build/SKILL.md`](../install-build/SKILL.md) for package/build
   failures.
2. Decide whether the user needs manual scheduling, a transform pass, dlight, or
   meta-schedule tuning.
3. For manual schedules and debug traces, read
   [`references/schedule-workflows.md`](references/schedule-workflows.md).
4. For `tune_tir`, builder/runner/database/cost-model decisions, or bounded
   tuning runs, read [`references/meta-schedule.md`](references/meta-schedule.md).
5. Run [`scripts/meta_schedule_import_probe.py`](scripts/meta_schedule_import_probe.py)
   before a tuning run to verify the API and optional dependencies.
6. Use [`references/troubleshooting.md`](references/troubleshooting.md) for
   `ScheduleError`, invalid traces, no-candidate tuning, database, XGBoost,
   runner/RPC, and backend issues.

## API anchors

```python
from tvm.s_tir import Schedule
from tvm.s_tir import meta_schedule as ms

sch = Schedule(mod, seed=None, debug_mask="none", error_render_level="detail", enable_check=True)
ms.tune_tir(mod, target, work_dir, max_trials_global, runner="local", database="json")
```

`tune_tir` returns a meta-schedule `Database`. Use tiny `max_trials_global`
values for smoke checks, a disposable `work_dir`, and a CPU target unless the
user has explicitly prepared a GPU/RPC backend.

## Boundaries

- Relax model import and high-level pipelines: [`../relax-compile/SKILL.md`](../relax-compile/SKILL.md).
- TIRx tile primitives and native kernel dispatch: [`../tirx-kernels/SKILL.md`](../tirx-kernels/SKILL.md).
- RPC tracker/server setup for remote runners: [`../rpc-deployment/SKILL.md`](../rpc-deployment/SKILL.md).
- Package/toolchain failures: [`../install-build/SKILL.md`](../install-build/SKILL.md).
