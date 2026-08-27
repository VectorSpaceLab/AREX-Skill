# Train and Play Workflows

## Train flow

1. Select the RL library with `--rl_library`.
2. Choose the task with `--task`.
3. Add any required launcher or preset tokens, such as `physics=...`, `renderer=...`, or `presets=...`.
4. Provide the library-specific agent, seed, checkpoint, distributed, and video flags.
5. Launch through the repo wrapper so the correct package paths and library helpers are selected.

## Play flow

1. Select the same RL library that produced the checkpoint.
2. Use the matching task and observation preset combination.
3. Pass the checkpoint path or run directory expected by the library.
4. Add `--video` and `--video_length` if you want replay recording.
5. Keep the preset token aligned with the training run when the preset changes observation structure.

## Typical wrapper commands

```bash
./isaaclab.sh train --rl_library rl_games --task Isaac-Ant-v0
./isaaclab.sh train --rl_library rsl_rl --task Isaac-Reach-Franka-v0
./isaaclab.sh play --rl_library skrl --task Isaac-Reach-Franka-v0 --num_envs 32 --checkpoint /PATH/TO/model.pt
```

## Common command arguments

- `--video` records videos during training or playback when the library and task support it.
- `--num_envs` changes the number of parallel environments.
- `--distributed` enables multi-GPU or multi-node training where supported.
- `--export_io_descriptors` exports IO descriptors for manager-based RL environments.
- `--agent` selects a non-default training agent config when a task exposes multiple agents.
- `--load_run` and `--checkpoint` select the stored run or model file in playback flows.

## When to use the bundled helper

Use `scripts/inspect_rl_dispatch.py` when you want to confirm the wrapper syntax, supported library names, and install-extra mapping without starting a training job.
