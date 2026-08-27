# Troubleshooting

Use this matrix when Hub, W&B, or video recording fails. The bundled checker only validates local layout and command planning; it does not contact external services.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Hub upload/download fails with missing token, insufficient rights, private repo denial, or auth errors | The command is trying to talk to a private or gated Hugging Face repository without valid credentials or org access | Stop retrying blindly. Confirm the organization/repo id, confirm the user has access, and rerun only after service login/credentials are approved. Do not embed tokens in the command. |
| `load_from_hub` destination already exists and the command refuses to overwrite it | The target `<folder>/<algo>/<env>_<id>` or `<folder>/<algo>` folder is already present and `--force` was not passed | Pick a different `--exp-id`, choose a fresh log folder, or pass `--force` only when the overwrite is intentional. |
| `load_from_hub` reports a missing Hub file | The remote repo does not contain one of `algo-env.zip`, `config.yml`, `args.yml`, `env_kwargs.yml`, or `train_eval_metrics.zip` | Repackage the repository or inspect it with `scripts/hub_model_layout_checker.py --mode staged-hub ...` if you already have a local clone/snapshot. |
| Hub download says `No normalization file` | The remote repo does not have `vec_normalize.pkl` | This is only safe when the model was trained without normalization. If normalization was used, the Hub repo is incomplete and should be repackaged. |
| Local evaluation after download fails because `vecnormalize.pkl` is missing | The local run folder does not contain the normalization stats needed by the saved config | Repackage from the original training logs or ensure the Hub repo included the normalization file. |
| W&B tracking fails with `ImportError` | `wandb` is not installed in the active environment | Install W&B or remove `--track`. The helper does not install service packages for you. |
| W&B runs but should stay offline | `--track` was used in a session that should not send metrics externally | Remove `--track` or use an explicitly approved offline W&B setup supplied by the user. |
| Video commands complain about `DISPLAY` or render errors | The environment expects screen rendering or an X server is unavailable | Use `--no-render` for headless-friendly recording when possible; otherwise arrange a display-capable session outside this sub-skill. |
| `record_training` cannot build MP4 or GIF output | `ffmpeg` is missing or not on `PATH` | Install `ffmpeg` and rerun. GIF creation always depends on `ffmpeg`. |
| Video file exists but is empty or tiny | The selected model did not load correctly, the environment did not step, or the render pipeline produced no frames | Check the selected model path, lower `-n` for a quick retry, verify the output folder is writable, and confirm the environment supports frame rendering. |
| Hub or W&B commands fail because the network is unavailable | The task is using a live service in an offline session | Use the bundled layout checker, inspect local files only, and postpone the live command until network access is approved. |
| `rl_zoo3 train --help` or a console command fails on plotting imports | The console entry point imports optional plotting dependencies that are not installed | Prefer `python -m rl_zoo3.train` or install the required plotting extras before retrying the console wrapper. |

## Local preflight reminders

- Use `scripts/hub_model_layout_checker.py` to confirm the selected local model, config, and destination behavior before any live Hub command.
- Use the evaluation-and-artifacts sub-skill when you need to inspect the run folder itself.
- Use the training-cli sub-skill when the missing artifact simply means the model has not been trained yet.
