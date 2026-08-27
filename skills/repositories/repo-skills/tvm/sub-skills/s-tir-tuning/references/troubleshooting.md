# S-TIR and Meta-Schedule Troubleshooting

## Schedule errors

**Symptom:** `ScheduleError` with a long diagnostic.

- Keep `error_render_level="detail"` and `debug_mask="all"` for repros.
- Print the IR before the failing primitive.
- Check block names, loop order, reduction/non-reduction axes, and whether a
  previous primitive changed the structure you are targeting.
- Reduce to the smallest sequence of schedule primitives that reproduces the
  failure.

**Symptom:** A trace does not replay.

- Verify the starting IRModule is structurally the same.
- Check random seed and sampled decisions.
- Avoid mixing traces from different TVM commits or transformed modules.

## Transform/dlight failures

**Symptom:** A transform pass fails on a scheduled module.

- Confirm the schedule output is valid before the pass.
- Apply transforms one at a time.
- Route TIRx-specific scope/layout failures to tirx-kernels.

**Symptom:** DLight emits invalid or unsupported code.

- Check whether the selected rule is CPU or GPU specific.
- Confirm target context and backend availability.
- For GPU rules, do not proceed without CUDA-enabled TVM and compatible device
  evidence.

## Meta-schedule produces no useful candidate

Check in this order:

1. `max_trials_global` and `num_trials_per_iter` are nonzero and not too small
   for the intended result.
2. `target` matches the hardware/compiler being measured.
3. `runner` is usable (`local` device exists or RPC service works).
4. `work_dir` is writable and not polluted by an incompatible previous run.
5. `database` choice is appropriate and records are being written.
6. `cost_model` dependency exists; switch to `random` for a plumbing smoke.
7. Schedule space/postproc does not reject every candidate.

## XGBoost/cost model issues

`cost_model="xgb"` requires XGBoost. If import or training fails during a smoke,
use `cost_model="random"` to isolate TVM plumbing from cost-model dependency
problems. For performance work, reinstall the dependency and rerun with an
approved trial budget.

## RPC runner issues

RPC runners depend on a working TVM RPC tracker/server setup. Timeouts, key
mismatches, target mismatch, and remote device unavailability are RPC deployment
problems first; validate upload/load/run with rpc-deployment before measuring.

## Backend claims

A CPU meta-schedule smoke validates schedule/tuning plumbing for CPU. It does
not validate CUDA schedule rules, tensor-core intrinsics, remote device timing,
or external accelerator performance.
