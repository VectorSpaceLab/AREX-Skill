# Troubleshooting

This page collects the failure modes most likely to appear when operating the
installed mjlab CLIs. The goal is to fix the command surface first, then move on
to longer runs only after the inputs are known to be valid.

## W&B auth and downloads

- W&B downloads and uploads require a valid login.
- `--wandb-run-path` should use the `entity/project/run_id` form.
- `--wandb-checkpoint-name` can be used when the run contains multiple models.
- For local smoke runs, prefer `--agent.logger tensorboard` and
  `--agent.upload-model False` to avoid W&B side effects.
- If a tracking task says it cannot find a motion artifact, confirm that the run
  actually logged an artifact of type `motions`.

## Motion file errors

- Tracking tasks need a local `--motion-file` or a registry-backed motion
  source.
- Playback from W&B still needs the motion artifact to exist in the run.
- If the converter fails, validate the CSV first with the bundled helper.
- If the motion tracks the wrong bodies, suspect a converter mismatch rather
  than a policy bug.

## CPU and GPU selection

- `--gpu-ids None` selects CPU mode.
- GPU indices are relative to `CUDA_VISIBLE_DEVICES` when it is set.
- If you need to keep Warp away from GPUs entirely, hide the devices before
  launch; a CPU flag alone does not guarantee that visible GPUs are untouched.
- Multi-GPU training is data-parallel, so each GPU runs the full environment
  count.

## Tyro syntax mistakes

- booleans must be explicit: `--agent.resume True`
- collections use Python literal syntax: `--gpu-ids "[0, 1]"`
- nested fields use dotted paths and hyphenated names from help output
- when in doubt, inspect `--help` instead of guessing the flag spelling

## Viewer and rendering problems

- `viewer=auto` chooses native when a display is available and Viser otherwise.
- Native viewer is best for perturbations and local debugging.
- Viser is best for browser-based or headless work and camera feeds.
- `--video` uses the offscreen renderer, so it depends on a working GL/EGL
  setup.
- If rendering fails, try the other viewer mode before changing the task.

## Checkpoint path problems

- `train --agent.resume True` searches the latest matching run and checkpoint
  under the configured log root.
- `--agent.load-run` and `--agent.load-checkpoint` are regex filters, not exact
  path literals.
- `play` needs either a local checkpoint file or a W&B run path.
- If the CLI cannot find a checkpoint, confirm the file name and the log root
  before looking for a training bug.

## NaNs and stability

- Use `--enable-nan-guard True` to capture a dump when instability appears.
- Inspect the resulting dump with `viz-nan`.
- A `nan_detection` termination can keep training alive, but it is only a band-
  aid; fix the underlying cause after capturing a dump.

## Networked or credentialed workflows

Treat these as non-bounded workflows unless the user explicitly asked for them:

- `demo`
- W&B artifact download or upload
- cloud launchers and sweeps
- benchmark automation

A good default is to stop after help output, registry inspection, or local
validation unless the task explicitly requires a longer run.
