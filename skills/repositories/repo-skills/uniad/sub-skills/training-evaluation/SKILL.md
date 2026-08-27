---
name: training-evaluation
description: "Build and troubleshoot UniAD distributed and SLURM train/eval runs
  for BEVFormer, stage1, and stage2 workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Evaluation

Use this sub-skill when the task is about launching, resuming, or troubleshooting UniAD training or evaluation runs for BEVFormer, stage1 track/map, or stage2 end-to-end workflows.

## Route here for

- `tools/train.py` and `tools/test.py` command questions.
- `tools/uniad_dist_train.sh`, `tools/uniad_dist_eval.sh`, `tools/uniad_slurm_train.sh`, and `tools/uniad_slurm_eval.sh` launcher behavior.
- Checkpoint placement, `work_dirs/` layout, logs, and stage smoke checks.
- `--seed`, `--deterministic`, `--cfg-options`, `--resume-from`, or `load_from` usage.
- GPU-count, memory, or distributed-launch issues during training or evaluation.

## Route elsewhere for

- Dataset download, info-PKL generation, CAN bus/map layout, or motion-anchor preparation -> `data-preparation`.
- Config semantics, model-head ownership, or architecture changes -> `config-and-model-architecture`.
- Result PKLs, visualization, or log plots -> `visualization-and-results`.

## Operating rules

- Prefer command construction, path validation, and dry-run diagnosis before recommending an expensive run.
- Treat `ckpts/` at the repo root as the default checkpoint landing zone; the stage configs use relative `load_from` paths that expect that layout.
- `tools/test.py` is distributed-only in practice: the non-distributed branch asserts false, so evaluation must go through `torchrun`, `srun`, or the bundled command builder.
- The bundled launchers cap one node at 8 GPUs per node. Fewer GPUs are allowed, but runtime increases and exact metrics can drift.
- Quote list or tuple `--cfg-options` values so the shell preserves brackets and commas.
- Use `--resume-from` only for resuming optimizer or scheduler state; use `load_from` or `--cfg-options load_from=...` for initialization checkpoints.
- When the user asks for an exact metric match, remind them that the published stage1 eval numbers are reference targets and can vary slightly with GPU count or launch topology.

## Read/run next

- Read [`references/train-eval-cli.md`](references/train-eval-cli.md) for CLI surfaces, launcher flags, launcher defaults, and work-dir/log behavior.
- Read [`references/runtime-and-gpu.md`](references/runtime-and-gpu.md) for the public v2.0 stack, memory guidance, and inspection caveats.
- Read [`references/checkpoints.md`](references/checkpoints.md) for checkpoint names, placement, and expected stage signals.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for missing-data, missing-checkpoint, launcher, GPU-count, and version-mismatch failures.
- Run [`scripts/build_uniad_command.py`](scripts/build_uniad_command.py) with `--help` to render a dry-run command template without starting training or evaluation.
- If you need dataset preparation or visualization instead, switch sub-skills rather than extending this one.
