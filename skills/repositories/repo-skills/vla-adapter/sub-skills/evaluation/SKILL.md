---
name: evaluation
description: "Guide VLA-Adapter LIBERO and CALVIN evaluation, command
  generation, outputs, prerequisites, metrics, and benchmark cautions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation (external-checkout adapter)

This sub-skill renders plans for native LIBERO/CALVIN evaluators in a separate
checkout. It contains only documentation and a command renderer: it does not
contain `experiments/robot/` or `vla-scripts/`, does not run an evaluation, and
is not a self-contained benchmark runtime.

Set the absolute source root and enter it before any native workflow:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"
```

Native entrypoints are `experiments/robot/libero/run_libero_eval.py` and
`vla-scripts/evaluate_calvin.py`. The bundled builder only prints commands
beginning with `cd <absolute-repo-root> &&`; it never imports the model or
launches a rollout. External prerequisites are CUDA-capable PyTorch, the base
VLA-Adapter package, a complete compatible checkpoint, the selected LIBERO or
CALVIN checkout and assets/data/config layout, and a working EGL/OpenGL/MuJoCo
or pybullet renderer. Video runs may additionally require imageio/ffmpeg.

## Read first

- Read [references/evaluation-workflows.md](references/evaluation-workflows.md) for checkpoint-to-command workflows, expected outputs, and benchmark-specific runtime behavior.
- Read [references/benchmarks.md](references/benchmarks.md) for suite names, checkpoint names, default evaluation volumes, and published LIBERO/CALVIN metrics.
- Read [references/troubleshooting.md](references/troubleshooting.md) for dependency, renderer, checkpoint, unnormalization-key, log, and video failures.
- Run `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" --repo-root "$VLA_ADAPTER_REPO_ROOT" --help` to inspect the non-executing command renderer.

## Operating route

1. Identify the benchmark: use LIBERO for `libero_spatial`, `libero_object`, `libero_goal`, or `libero_10`; use CALVIN for `calvin_abc`.
2. Confirm the checkpoint family and suite match. Prefer the Pro checkpoints for published reproduction unless the user explicitly asks for the original release or a custom checkpoint.
3. Confirm downstream prerequisites before launching: CUDA-capable PyTorch, the base VLA-Adapter package dependencies, the external benchmark stack, benchmark assets, and the checkpoint files.
4. Generate the command with the bundled builder, then review the resulting `CUDA_VISIBLE_DEVICES=... python ...` invocation before execution.
5. Capture stdout/stderr into an `eval_logs/` file for long runs. LIBERO also writes internal text logs and rollout videos; CALVIN writes evaluation result files and per-subtask videos.
6. Interpret only full-volume runs against published metrics: LIBERO defaults to 500 episodes per suite, while CALVIN reports average successful sequence length across 1,000 five-instruction sequences.

## Critical cautions

- LIBERO evaluation depends on the repository's image preprocessing: both third-person and wrist camera images are rotated 180 degrees before policy input.
- LIBERO/OpenVLA action execution normalizes the gripper action to `[-1, +1]`, binarizes it, then inverts the OpenVLA gripper sign for environment execution.
- CALVIN reports average sequence length, not a single binary episode success rate; also inspect chain success rates for 1 through 5 consecutive instructions.
- External LIBERO and CALVIN stacks were not part of the base package import surface. Treat them as downstream prerequisites, not guaranteed installed dependencies.
