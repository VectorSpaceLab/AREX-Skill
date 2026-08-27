# Video recording workflows

This reference covers `record_video` and `record_training`. Both commands work on already-trained models and local run folders. They do not train a model, but they can still require rendering support, video dependencies, and `ffmpeg`.

## Choose the right command

- Use `python -m rl_zoo3.record_video` when you want a video from one selected model: final, best, a named checkpoint, or the latest checkpoint.
- Use `python -m rl_zoo3.record_training` when you want videos for the final model, best model, and each saved checkpoint in one run folder.
- For local evaluation without video, route to `../evaluation-and-artifacts/SKILL.md`.
- For the training command that produces the model folder in the first place, route to `../training-cli/SKILL.md`.

## `record_video`

Command shape:

```bash
python -m rl_zoo3.record_video \
  --algo ppo --env CartPole-v1 \
  -f logs --exp-id 1 \
  -n 1000 --no-render \
  -o ./videos
```

Key points:

- `--env`, `--folder`, `--exp-id`, `--load-best`, `--load-checkpoint`, and `--load-last-checkpoint` use the same local model-selection logic as `enjoy`.
- The command loads the selected model and then wraps the evaluation environment with `VecVideoRecorder`.
- `--no-render` is the safest default for headless or CI sessions. It still records video frames; it just avoids explicit on-screen rendering calls.
- `--output-folder` defaults to `<log_path>/videos` when omitted.
- `--custom-objects` helps with older saved models that need loading patches.
- `--deterministic` and `--stochastic` control action selection. Atari/Minigrid may flip the default behavior unless `--deterministic` is set.

## `record_training`

Command shape:

```bash
python -m rl_zoo3.record_training \
  --algo ppo --env CartPole-v1 \
  -f logs --exp-id 1 \
  -n 1000 --deterministic \
  -o ./videos
```

What it does:

1. Resolves the selected run folder.
2. Deletes and recreates the requested output folder.
3. Runs `record_video` for the final model when `<run>/<env>.zip` exists.
4. Runs `record_video` for `best_model.zip` when present.
5. Runs `record_video` once for each `rl_model_<steps>_steps.zip` checkpoint.
6. Adds text overlays to the individual clips with `ffmpeg`.
7. Concatenates them into `training.mp4`.
8. Optionally creates `training.gif` when `--gif` is passed.

Important consequences:

- `record_training` requires `ffmpeg`.
- `--gif` adds a second `ffmpeg` conversion step.
- The command expects actual checkpoint files in the run folder. If there are no `rl_model_<steps>_steps.zip` files, only the final/best model clips will be created.
- The script assumes it can write to the output folder and that the output folder may be deleted and recreated.

## Display and video prerequisites

Video recording can fail for reasons that are not model-related:

- Some environments or wrappers need `render_mode="rgb_array"` support.
- A missing `DISPLAY` can break live rendering for environments that expect a screen, even when the command uses `--no-render` for on-screen drawing.
- `ffmpeg` must be installed for `record_training` and GIF conversion.
- If the environment cannot render frames or the selected model cannot step successfully, the output may be an empty or tiny video file.
- Optional video dependencies from the package installation may be needed for `VecVideoRecorder` to function correctly in your environment.

## Safe checks before recording

Before using video commands, confirm the selected model exists in the run folder and that the output destination is writable. A quick layout check can be done with the bundled Hub/model checker when the same run folder is also being prepared for upload:

```bash
python ../scripts/hub_model_layout_checker.py \
  --mode push --folder logs --algo ppo --env CartPole-v1 --exp-id 1
```

For more detailed local model-folder inspection, use the evaluation-and-artifacts sub-skill.

## Practical troubleshooting pattern

If a video is empty or missing:

1. Confirm the selected model file exists.
2. Confirm the output folder was created and is writable.
3. Re-run with a small `-n` value only after confirming the model loads.
4. Check whether `ffmpeg` is installed and available on `PATH`.
5. If the environment needs screen rendering, arrange a display-capable session outside this sub-skill.
