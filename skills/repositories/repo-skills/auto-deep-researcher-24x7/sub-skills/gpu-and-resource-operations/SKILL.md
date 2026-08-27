---
name: gpu-and-resource-operations
description: "Detect and select local NVIDIA GPUs, report their resource status, and explain the explicitly opt-in GPU keep-alive without hiding hardware or CUDA limitations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GPU and resource operations

Use this skill for **local, read-only GPU inspection and selection** before an
experiment. It covers NVIDIA visibility, memory-based availability, the
`reserve_last` policy, and the optional keep-alive's safety contract. It does
not launch training, reserve a device through a scheduler, or start a keeper
implicitly.

## Safety contract

- Begin with the bundled `scripts/gpu_status.py`; it only invokes
  `nvidia-smi` queries and never allocates CUDA memory.
- Treat an absent, timed-out, or failed `nvidia-smi` query as **no usable GPU**.
  Never infer free devices from configuration, PyTorch importability, or a
  missing status result.
- “Free” means reported `memory_used_mb < 1000` by default, not that a device is
  exclusively reserved. Confirm ownership before launching work.
- `reserve_last=true` is a selection policy for a keep-alive slot, not a lock.
  With one detected GPU it remains usable; with two or more, the highest listed
  index is excluded from experiment candidates.
- Do not run the keep-alive during inspection. It allocates a CUDA tensor and
  performs repeated operations, so it is an explicit side effect requiring
  user approval.

## Operating flow

1. Run `python scripts/gpu_status.py --help` if the interface is unfamiliar;
   help must not probe hardware.
2. Run `python scripts/gpu_status.py` (or add `--json` for machine-readable
   output). Record the status reason when no GPU is reported.
3. Select only from `usable_gpus` and then filter to `free_gpus`. Keep the
   reserved device out of training when the default policy excludes it.
4. If the user explicitly chooses a device, report its `gpu_id`, name, memory,
   utilization, and temperature before passing its ID to the experiment
   launcher. Local launchers express this as `CUDA_VISIBLE_DEVICES`.
5. Before CUDA work, verify both a working NVIDIA driver (`nvidia-smi`) and a
   PyTorch build for which `torch.cuda.is_available()` is true. A Python
   package alone is not proof of CUDA support.
6. For SSH/Slurm status, scheduler allocation, or transport details, route to
   `execution-and-monitoring`. For loop launch and experiment lifecycle, route
   to `autonomous-experiments`. For installing external skills, route to
   `skills-and-installation`.

## Bundled references

- [GPU status and selection](references/gpu-status.md) — exact detector
  signatures, output shapes, query fields, thresholds, and edge cases.
- [Keep-alive contract](references/keeper.md) — explicit side effects,
  PyTorch/CUDA prerequisites, interval, signals, cleanup, and invocation
  rules.
- [Troubleshooting](references/troubleshooting.md) — predictable driver,
  CUDA, parsing, selection, and keeper failures.

## Output contract

A normal report should include:

- `detected`: whether a complete local NVIDIA status was obtained;
- one row per GPU with ID, name, used/total memory in MB, utilization percent,
  and temperature in °C;
- `usable_gpus` after `reserve_last` policy;
- `free_gpus` after the strict 1000-MB default threshold (or the stated
  override);
- an explicit `reason` when detection/status is unavailable; and
- whether a last device was excluded, without claiming a reservation lock.

When `detected` is false, both usable and free lists must be empty. Do not
silently substitute Slurm queue occupancy or a remote host's status for local
NVIDIA measurements.

If a report is used to choose a launch mask, preserve the host GPU IDs and the
selection policy in the handoff. Re-run the read-only probe immediately before
a long launch because memory and utilization are live observations, not a
reservation. Never claim that a keeper is active unless its explicit process
and stop/cleanup outcome have been checked.
