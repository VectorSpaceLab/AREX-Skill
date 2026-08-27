# Checkpoint Playback and Test-Mode Guide

Use this guide before any saved-model or `--mode test` task. Checkpoint playback is the most failure-prone continuous-control workflow in this repository because file paths are relative, env IDs are part of directory names, and architecture dimensions must match the environment.

## General playback checklist

1. Confirm algorithm family: DDPG, SAC, SAC dual-Q, SAC BipedalWalker, TD3, or TD3 BipedalWalker.
2. Confirm environment ID and action dimension. A Pendulum checkpoint cannot load into a BipedalWalker actor.
3. Confirm the current working directory expected by the script. The repo scripts save and load relative paths; running from a different directory changes where files are searched.
4. Confirm all required `.pth` files exist before rendering.
5. If CUDA availability differs from the training host, load with `map_location=device` or `map_location='cpu'` when patching the script.
6. For modern Gym, use `Pendulum-v1` or `BipedalWalker-v3` and patch legacy reset/step handling if needed.

## Expected files by workflow

| Workflow | Required files | Default relative root |
| --- | --- | --- |
| DDPG | `actor.pth`, `critic.pth` | `./expDDPG.py<env>./` |
| SAC single-Q | `policy_net.pth`, `value_net.pth`, `Q_net.pth` | `./SAC_model/` |
| SAC dual-Q / BipedalWalker | `policy_net.pth`, `value_net.pth`, `Q_net1.pth`, `Q_net2.pth` | `./SAC_model/` |
| SAC `test_agent.py` | `policy_net.pth`, `value_net.pth`, `Q_net1.pth`; inspect whether Q2 is separately saved | `./SAC_model/` |
| TD3 | `actor.pth`, `actor_target.pth`, `critic_1.pth`, `critic_1_target.pth`, `critic_2.pth`, `critic_2_target.pth` | `./expTD3.py<env>./` |
| TD3 BipedalWalker | Same six TD3 files | `./expTD3_BipedalWalker-v2.py<env>./` |

The odd `./exp...<env>./` directory strings are deliberate source behavior: the scripts build `directory = './exp' + script_name + args.env_name +'./'`.

## DDPG test mode

DDPG exposes `--mode test` and `--test_iteration`. Before using it:

- Patch or define the missing `max_length_of_trajectory` guard in the source test loop. A safe replacement is a fixed horizon such as `200` for Pendulum smoke playback.
- Modernize the env ID to `Pendulum-v1` unless working in an older Gym environment.
- If loading a CUDA checkpoint on CPU, patch each `torch.load(path)` to `torch.load(path, map_location=device)`.

## SAC playback

For Pendulum SAC:

- Prefer the dual-Q script for saved-model playback because the single-Q `SAC.py` load method is incorrectly written.
- If using `SAC.py`, patch each load line to `module.load_state_dict(torch.load(path, map_location=device))`.
- Ensure the normalized action wrapper works on the installed Gym version. On modern Gym, implement `action()` instead of relying only on `_action()`.

For BipedalWalker SAC:

- Use the modern env ID `BipedalWalker-v3` when Gym rejects `BipedalWalker-v2`.
- Verify Box2D and pygame before rendering.
- Check that Q2 was independently saved. The playback-oriented `test_agent.py` has source-level mistakes where Q2 can be saved/loaded from the Q1 path.

## TD3 test mode

TD3 exposes `--mode test` for both Pendulum and BipedalWalker variants.

- All six TD3 files are expected, not just `actor.pth`.
- The env ID is embedded in the checkpoint directory. Changing `BipedalWalker-v2` to `BipedalWalker-v3` changes the lookup path unless the script is patched.
- Rendering may require an available display or pygame-compatible headless setup; for non-rendered validation, patch the test loop to skip `env.render()` and print action/reward summaries instead.

## Minimal missing-checkpoint diagnosis

When a checkpoint load fails, report:

- algorithm variant and env ID,
- current working directory used for playback,
- expected relative checkpoint directory,
- missing filenames,
- whether the env observation/action shapes match the actor architecture,
- whether `map_location` is needed for CPU/CUDA mismatch,
- whether modern env-ID migration changed the directory name.

Do not silently retrain just to create missing checkpoints unless the user explicitly asks for training and provides a budget.
