# S-TIR Schedule Workflow Playbook

## When to use S-TIR schedules

Use `tvm.s_tir.Schedule` when the task is to transform a TensorIR/TIRx
`PrimFunc` or `IRModule` while preserving semantics: split/fuse/reorder loops,
inline blocks, cache reads/writes, set memory scope, tensorize, vectorize,
parallelize, or inspect a schedule trace.

Do not use this route as a substitute for high-level Relax graph import or TIRx
native tile primitive dispatch. Relax can lower to TIR, and TIRx can feed into
TIRx-specific lowering, but schedule debugging should start from the low-level
function that actually fails.

## Manual schedule loop

1. Construct or obtain a small `PrimFunc` or `IRModule`.
2. Create a schedule with explicit debug settings when diagnosing failures:

   ```python
   sch = tvm.s_tir.Schedule(
       mod,
       seed=0,
       debug_mask="all",
       error_render_level="detail",
       enable_check=True,
   )
   ```

3. Locate blocks and loops by name; avoid positional guesses until the IR has
   been printed.
4. Apply one primitive at a time.
5. Print or show `sch.mod` and inspect `sch.trace` after each meaningful step.
6. Compile or pass to meta-schedule only after the scheduled module is valid.

## Common primitive families

| Goal | Typical primitives or namespaces | Notes |
|---|---|---|
| Loop structure | `split`, `fuse`, `reorder`, `parallel`, `vectorize`, `unroll` | Preserve loop/domain legality; use detailed errors for invalid factors |
| Data locality | `cache_read`, `cache_write`, `compute_at`, `reverse_compute_at`, `set_scope` | Check producer/consumer placement and memory scope availability |
| Reduction transforms | `rfactor`, reduction block transforms | Require valid reduction block structure |
| Tensorization | `tensorize`, tensor intrinsics | Requires exact pattern and target-specific intrinsics |
| Layout transforms | `transform_layout`, reindex/cache helpers | Confirm buffer indexing and shape assumptions |
| Debug/trace | `sch.trace`, schedule state inspection, structural equality checks | Use for reproducibility and bug reports |

## DLight/default schedules

DLight rules are useful when Relax or TIR has already identified common GPU/CPU
patterns such as matmul, reductions, or GEMV. Treat dlight as a rule selection
layer, not a magic backend enabler:

- CPU dlight rules can be smoke-tested in a CPU/LLVM environment.
- GPU dlight rules require a CUDA-capable build and target.
- If dlight emits target-specific TIR that fails codegen, classify the failure
  as target/backend or scheduling rule mismatch before changing the Relax
  frontend.

## Native evidence candidates

For a CPU/LLVM environment, focused candidates include schedule error tests,
split/fuse/reorder tests, selected transform tests, and CPU dlight tests. CUDA
schedule-rule, tensor-core, or GPU transform tests require optional backend
preparation and must not be counted as CPU verification.
