# Training and Distribution Troubleshooting

## Purpose

Use this when a training command, launcher, or hook setup fails.

## Common failures

### Distributed training works for one model family but fails for another

**Symptoms**
- A static GAN runs, but a dynamic GAN crashes in DDP.
- Gradients or unused-parameter warnings appear only in one path.

**Likely causes**
- `find_unused_parameters` does not match the model family.
- `use_ddp_wrapper` and `is_dynamic_ddp` are set inconsistently.

**Recovery**
- Use `DynamicIterBasedRunner` for dynamic GANs.
- Compare with the repo's distributed-training tutorial before changing the runner.

### `apex_amp` fails or is ignored

**Symptoms**
- Mixed-precision settings appear in the config, but the run errors out.

**Likely causes**
- Apex AMP is only supported with DDP training in this repo.
- The model was not moved to CUDA before Apex initialization.

**Recovery**
- Keep Apex only on the distributed path.
- If possible, prefer the repo's non-Apex paths for inspection and debugging.

### CPU training is extremely slow

**Symptoms**
- The job technically runs, but progress is not practical.

**Likely causes**
- CPU training is a debug fallback, not the normal production path.

**Recovery**
- Use CPU only to validate a config or code path.
- Move the real claim to a CUDA-capable environment.

### Validation hooks do not appear to run

**Symptoms**
- Training starts, but no validation or metric logging shows up.

**Likely causes**
- `cfg.evaluation` is absent.
- The validation loader is not configured in the expected place.
- A custom hook priority prevents the hook from firing when expected.

**Recovery**
- Check the config's `evaluation` block and `workflow`.
- Compare with the examples in `customize_runtime.md`.

### Checkpoint or resume behavior is confusing

**Symptoms**
- The run resumes from an unexpected state.
- The wrong checkpoint path is used.

**Likely causes**
- `resume_from` and `load_from` were both present.
- `work_dir` points at a different run than expected.

**Recovery**
- Remember that `resume_from` takes precedence over `load_from` in the training script.
- Print the resolved config and work directory before launching the long job.

### Hook state is missing or appears stale

**Symptoms**
- EMA or visualization hooks appear to do nothing.

**Likely causes**
- The hook class was not imported.
- The hook interval or priority is wrong.
- The runner type does not match the hook's assumptions.

**Recovery**
- Re-check the registry and import path.
- Compare the hook parameters with the test patterns under `tests/test_cores/`.

## When to escalate

Stop and ask for a narrower scope or a different backend when the fix needs:

- A GPU runtime the host does not provide.
- A different launcher or cluster scheduler.
- A repo code change in the runner or hook implementation.
