# Operations Checklist

Use this checklist to supervise DreamerV3 setup, long-running jobs, resume attempts, and result collection. Training command and config construction belongs to `train-configure`; this document covers operational readiness and evidence collection.

## Pre-Run Checklist

### 1. Match task suite to dependencies

- Identify the suite prefix in the intended task id, for example `dummy`, `atari`, `crafter`, `dmc`, `dmlab`, `minecraft`, or `procgen`.
- Run the optional dependency checker:
  ```sh
  python scripts/check_optional_env_imports.py
  ```
- Install only the optional suite dependencies needed by the selected task. A missing DMLab package should not block Atari, dummy, or result-only work.

### 2. Verify base package and JAX

```sh
python -m pip check
python - <<'PY'
import dreamerv3, embodied
from embodied.envs import dummy
import jax, jax.numpy as jnp
print('backend', jax.default_backend())
print('devices', jax.devices())
print(float(jnp.array([1.0, 2.0]).sum()))
env = dummy.Dummy({'image': (8, 8, 3)}, {'action': (2,)})
print(sorted(env.obs_space.keys()))
PY
```

Expected: imports succeed, JAX tiny array succeeds, and the dummy env exposes spaces.

### 3. Confirm display/rendering requirements

- Headless Atari/ProcGen/DMC/Minecraft/DMLab runs may need a virtual display or EGL path depending on suite.
- For MuJoCo/DeepMind Control/Loconav, set or confirm `MUJOCO_GL=egl` on headless GPU hosts.
- For Docker/headless shell use, wrap commands with `xvfb-run` when the environment creates an X11 viewer or image context.

### 4. Choose logdir intentionally

- Use a fresh logdir for new experiments.
- Use the exact same logdir only when intentionally resuming the same run.
- Keep logdir on storage with enough capacity for JSONL, Scope summaries, checkpoints, replay chunks, and optional environment logs.
- Avoid logdirs that contain checkpoints from incompatible configs or model sizes.

### 5. Decide portable outputs

- Default portable outputs: terminal, `metrics.jsonl`, `scores.jsonl`, and Scope summaries.
- Enable TensorBoard/WandB/Expa only when the host has the package, credentials, and network/infrastructure policy.
- If using WandB/Expa, keep JSONL enabled as the portable fallback.

## During-Run Checklist

### First minutes

- Confirm terminal logs start and the logdir is created.
- Confirm `metrics.jsonl` appears after the first logger write interval.
- Confirm `scores.jsonl` appears after completed episodes produce `episode/score`.
- Watch the first CUDA/JAX error, not just the final stack trace.
- If CUDA memory errors occur immediately, separate version mismatch from capacity by rerunning the tiny JAX smoke and a small debug run.

### Ongoing monitoring

Use standard host tools and portable files:

```sh
nvidia-smi
python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --list-keys
python scripts/metrics_summary.py --input <logdir>/scores.jsonl --key episode/score --last 5
```

Look for:

- `step` increasing over time;
- `episode/score` and `episode/length` appearing once episodes finish;
- `fps/...` values that are nonzero and stable enough for the host;
- replay/client/server stats if using parallel execution;
- no repeated malformed final JSONL lines except from an interrupted writer.

### Viewer monitoring

```sh
python -m scope.viewer --basedir <logdir-parent> --port 8000
```

If Scope cannot start, do not stop a healthy run solely for viewer issues. Use JSONL summaries and fix viewer dependencies separately.

## Resume Checklist

DreamerV3 resume is logdir-based: use the same command/config intent and point to the same logdir.

Before resuming:

1. Confirm the logdir is the intended run, not an old experiment.
2. Record the last available `step`:
   ```sh
   python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --key step --last 1
   ```
3. Confirm the current code/config/model size matches the checkpoint.
4. Check write permissions and free storage.
5. Keep JSONL files; robust readers can ignore a malformed trailing line.

If resume fails with a checkpoint tree mismatch such as `Too many leaves for PyTreeDef`, treat it as an incompatible checkpoint/config/logdir combination. Use a fresh logdir for the new config or restore the exact old config before retrying.

## Multi-GPU And Parallel Operations

Detailed config selection belongs to `train-configure`, but operations should verify:

- GPU visibility and memory per process before launch;
- unique logdir per independent run;
- no accidental sharing of actor/replay/logger ports across unrelated runs;
- port availability for distributed or parallel modes;
- if multiple replicas write under one parent, each replica has an unambiguous subdirectory or replica id;
- every worker can import the same optional environment suite packages;
- host display/EGL settings are valid for every environment worker that renders frames.

If one worker repeatedly fails an optional env import while others run, fix the environment package on all workers rather than treating it as a training instability.

## Storage And Logging Hygiene

- Keep `metrics.jsonl` and `scores.jsonl` append-only during a run.
- Copy or compress logs only after stopping the writer cleanly.
- Check for replay/checkpoint growth before long runs.
- Use run-specific directories for environment-side logs such as Crafter stats.
- Preserve the full logdir when reporting bugs: JSONL alone may not be enough for resume, and checkpoints alone may not be enough for result analysis.

## Post-Run Checklist

1. List available scalar keys:
   ```sh
   python scripts/metrics_summary.py --input <logdir> --list-keys
   ```
2. Summarize score and episode length:
   ```sh
   python scripts/metrics_summary.py --input <logdir>/scores.jsonl --key episode/score --last 20
   python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --key episode/length --last 20
   ```
3. If using Scope, verify the viewer sees the completed run.
4. If comparing to benchmark score artifacts, state whether the score is raw, normalized, capped, or self-normalized.
5. Archive the logdir with enough metadata to recover: task id, config blocks, seed, package version, backend, and host notes.
6. Do not delete partial logs after a transient failure; they are useful for resume decisions and error diagnosis.

## Safe Escalation Rules

- Base import/JAX failure blocks all training and should be fixed first.
- Optional suite import failure blocks only tasks using that suite.
- Viewer/tracker failure does not block training if JSONL and checkpoints are healthy.
- CUDA failure blocks production-scale GPU claims, but CPU debug/summarization can continue.
- Checkpoint incompatibility should not be worked around by editing checkpoints; use the matching config or a fresh logdir.
