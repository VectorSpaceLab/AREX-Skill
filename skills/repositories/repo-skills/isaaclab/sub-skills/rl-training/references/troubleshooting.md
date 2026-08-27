# RL Training Troubleshooting

## `No module named common`

- **Likely cause:** a unified training script was invoked outside the repo wrapper or the dispatcher path was not resolved correctly.
- **Recovery:** launch through `./isaaclab.sh train ...` or `./isaaclab.sh play ...` so the repo wrapper sets up the expected module search path.

## `physics=...` or `renderer=...` hits a raw Hydra struct error

- **Likely cause:** the typed preset tokens were not routed through the preset CLI parser before Hydra.
- **Recovery:** make sure the entrypoint uses the preset helper and preserves the remainder on `sys.argv`.

## `Unknown preset(s)` during train/play

- **Likely cause:** the selector reached Isaac Lab's resolver but the name is invalid for the current task or backend.
- **Recovery:** inspect the environment's preset list and use the canonical selector spelling for the task.

## Checkpoint load failures

- **Likely cause:** the checkpoint path, run directory, or observation preset does not match the training configuration.
- **Recovery:** verify the checkpoint naming convention for the selected library and make sure play uses the same observation preset as training.

## Video output missing

- **Likely cause:** the task or library did not enable camera rendering, or the evaluation path did not request video recording.
- **Recovery:** pass `--video`, a non-zero `--video_length`, and the required camera/rendering flags for the task.

## Distributed training rejected on CPU

- **Likely cause:** the requested distributed mode is incompatible with the selected device.
- **Recovery:** use a CUDA device for distributed runs.

## Optional RL extras missing

- **Likely cause:** the selected library extra (`rl_games`, `rsl_rl`, `sb3`, `skrl`, or `rlinf`) was not installed.
- **Recovery:** install only the extra for the selected library instead of the entire optional matrix.
