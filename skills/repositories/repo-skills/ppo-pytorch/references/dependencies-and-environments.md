# Dependencies and Environments

This repository is a small script-based PPO project, not a packaged Python distribution. Install the runtime dependencies directly before using the bundled helpers.

## Core dependencies

| Package | Used for | Notes |
| --- | --- | --- |
| `torch` | PPO networks, optimization, checkpoint save/load | Core requirement for every route. |
| `numpy` | State/action array conversion and general math | Core requirement. |
| `gym` | Training and evaluation environments | The native scripts import it directly. |
| `roboschool` | Legacy Roboschool presets and checkpoints | Required for the shipped Roboschool routes. |
| `pandas` | Log CSV reading and averaging | Needed for plotting. |
| `matplotlib` | Reward-curve plotting | Needed for plotting. |
| `Pillow` | GIF composition from frame images | Needed for GIF creation. |

## Environment families in the repository

The repository README and pretrained presets cover these families:

- Classic control: `CartPole-v1`
- Box2D: `LunarLander-v2`, `BipedalWalker-v2`
- Legacy Roboschool locomotion: `RoboschoolHalfCheetah-v1`, `RoboschoolHopper-v1`, `RoboschoolWalker2d-v1`
- Optional notebook alternative: `pybullet` / `pybullet_envs`

## Legacy compatibility notes

- The native `train.py`, `test.py`, and `make_gif.py` scripts import `gym` and `roboschool` at module import time.
- The scripts use the older Gym-style `reset()` and `step()` return values.
- Newer Gymnasium environments may need a small adaptation layer for `reset` and `step` handling.
- Roboschool is a legacy dependency. If you only need the non-Roboschool presets, keep the dependency notes separate from the shared PPO core.

## Suggested install order

1. Install `torch` and `numpy`.
2. Install `gym`.
3. Add the route-specific dependency family:
   - `pandas`, `matplotlib`, and `Pillow` for visualization.
   - `roboschool` for the Roboschool checkpoints and scripts.
   - `gym[box2d]` or another Box2D-compatible package for Box2D presets.
   - `pybullet` only when following the notebook's optional alternative environment path.

## Quick sanity check

Use the bundled setup helper before choosing a route:

```bash
python scripts/check_ppo_setup.py
```

If the route needs a checkpoint inspection or device check, pass `--checkpoint-path` to the same helper or use the evaluation sub-skill helper.
