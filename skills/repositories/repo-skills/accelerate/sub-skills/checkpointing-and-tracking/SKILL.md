---
name: checkpointing-and-tracking
description: "Save and resume Accelerate training state, register checkpoint
  hooks and custom state, log safely across processes, use experiment trackers,
  profile runs, and clean up memory."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Checkpointing and Tracking

Use this sub-skill when the task involves Accelerate checkpoint save/load, model export, tracker initialization/logging, distributed-safe logging, profiling, state/RNG handling, or memory cleanup around those workflows.

## Route First

- For the core forward/backward/optimizer loop, gradient accumulation, prepared dataloaders, and `skip_first_batches`, use `../training-loop-integration/`.
- For FSDP, DeepSpeed, Megatron-LM, or backend-specific checkpoint strategy and consolidation details, use `../distributed-training-backends/`.
- For large-model dispatch/offload checkpoint loading, route to the large-model or big-modeling sub-skill if present.

## Fast Workflows

- Save and resume same-script training state with `Accelerator.save_state()` and `Accelerator.load_state()`; see `references/checkpointing.md`.
- Configure automatic checkpoint folders and retention with `ProjectConfiguration`; see `references/checkpointing.md`.
- Register custom checkpointable objects and save/load pre-hooks for extra metadata; see `references/checkpointing.md`.
- Initialize trackers with `Accelerator(log_with=...)`, `init_trackers()`, `log()`, `get_tracker()`, and `end_training()`; see `references/tracking-and-logging.md`.
- Use `accelerate.logging.get_logger()` for multiprocess-safe logs and ordered rank logs; see `references/tracking-and-logging.md`.
- Profile CPU/GPU/XPU sections with `ProfileKwargs` and `accelerator.profile()`; see `references/tracking-and-logging.md`.
- Diagnose common failures using `references/troubleshooting.md` before changing training code.

## Bundled Helper

- Run `python scripts/checkpoint_tracker_smoke.py --help` for usage.
- Run `python scripts/checkpoint_tracker_smoke.py` to verify a CPU-only tiny save/load/custom-tracker/logging smoke test without any external tracker service.

## Key Constraints

- `save_state()`/`load_state()` are for resuming the same training script shape, not arbitrary model conversion between unrelated scripts.
- Register custom objects only if they implement both `state_dict()` and `load_state_dict()`.
- For ordinary model artifact export, prefer `accelerator.unwrap_model()`, `accelerator.get_state_dict()`, `accelerator.save()`, or `accelerator.save_model()` rather than treating a training-state checkpoint as a deployment artifact.
