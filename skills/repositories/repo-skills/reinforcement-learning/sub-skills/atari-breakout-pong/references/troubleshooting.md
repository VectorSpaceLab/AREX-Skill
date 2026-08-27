# Troubleshooting Standard Atari Breakout/Pong

## Purpose

Use this matrix to diagnose predictable failures in the standard Atari DQN/PPO
workflows: dependency/ROM setup, device selection, W&B, checkpoints, replay
sampling, frame shapes, return metrics, display handling, and benchmark
expectations.

## Fast triage

1. If the task only needs to validate model/replay/GAE logic, run
   `python scripts/atari_basic_smoke.py --device cpu` from the sub-skill
   directory. This does not need Gymnasium, ALE, ROMs, W&B, network, or display.
2. If actual Breakout/Pong env creation fails, inspect dependencies and ROM
   installation before changing algorithm code.
3. If training starts but learning is slow, check run budget, reward/return
   interpretation, and benchmark caveats before assuming a code bug.

## Failure matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `invalid choice` for `--env` | The standard Atari workflow accepts only `breakout` and `pong`. | Use `--env breakout` or `--env pong`. Route Montezuma/Pitfall/PrivateEye requests to the hard-Atari owner. |
| Gymnasium/ALE cannot create `ALE/Breakout-v5` or `ALE/Pong-v5`; ROM not found; namespace/id errors | Atari dependencies or ROM assets are missing, or the ROM license/import step was not completed. | Do not debug DQN/PPO first. Verify Gymnasium Atari support and `ale-py` are installed, then install/import ROMs under the user's valid license workflow. Use the bundled smoke helper while ROM setup is unresolved. |
| `ModuleNotFoundError` for `gymnasium`, `ale_py`, `pygame`, `torch`, or `wandb` | Required runtime dependency missing. `wandb` is only needed for `--wandb`; Gymnasium/ALE/Pygame are not needed for the bundled smoke helper. | Install the repository's Python 3.11 dependency set or remove optional `--wandb`. For a logic-only check, run `scripts/atari_basic_smoke.py`, which only imports NumPy and Torch. |
| Explicit `--device cuda` fails with unavailable CUDA or device transfer errors | User forced CUDA on a host without a matching CUDA Torch build/device. | Retry with `--device auto` or `--device cpu`, or prepare a CUDA-enabled Torch environment. Do not treat CPU smoke success as proof that CUDA training is configured. |
| Explicit `--device mps` fails or is much slower than expected | Apple MPS backend unavailable, unsupported in the installed Torch build, or limited by memory/kernel support. | Retry with `--device auto`/`cpu`; ensure an MPS-capable Torch build on Apple Silicon. For correctness checks, prefer the CPU smoke first. |
| Run opens a window or crashes with display/Pygame errors | `--render` or `--test` requests human rendering. Headless servers may have no display. | Omit `--render` during training. For `--test`, either provide a display, run on a desktop, or adapt a local evaluation entrypoint to use non-human render mode. The bundled smoke helper is headless. |
| `FileNotFoundError: atari_dqn.pt` or `atari_ppo.pt` during `--test` | Test mode expects the relevant checkpoint in the current working directory. | Train first or copy the matching checkpoint into the working directory. Use `atari_dqn.pt` for DQN and `atari_ppo.pt` for PPO. |
| Checkpoint load shape mismatch | The checkpoint was produced by a different workflow, model architecture, or action count. | Do not load a PPO checkpoint into DQN or the reverse. Recreate the model with the same `n_actions` as the env used for training. If switching games, verify the action space before reusing weights. |
| DQN `RuntimeError("buffer too small to sample yet")` | Replay sampling was called before enough single frames existed to reconstruct 4-frame states and next states. | Wait until at least `stack + 2` frames are present. The training loop already waits until `LEARN_START=80_000` frames; custom probes should do the same or use the smoke helper's synthetic replay setup. |
| DQN RAM spikes or machine swaps | `BUFFER_CAPACITY=500_000` stores many Atari frames; full training can require multiple GB of RAM. | Reduce replay capacity in a local experiment, use a machine with more RAM, or run only the smoke helper when validating logic. Do not expect the documented full run to be lightweight. |
| PPO memory spikes | PPO stores `ROLLOUT_STEPS * N_ENVS` stacked observations plus tensors for optimization; default is `128 * 8`. | Reduce `N_ENVS` or rollout length in a local experiment if memory-constrained, understanding this changes training dynamics. |
| Tensor shape error around Conv2d; expected 4 channels | Observation was not frame-stacked or was shaped NHWC instead of NCHW. | Ensure preprocessing emits `(4, 84, 84)` per env and batched tensors are `(batch, 4, 84, 84)`. Keep dtype `uint8`; the model normalizes internally. |
| Model outputs `nan` or loss explodes | Inputs may be incorrectly scaled, rewards may not be clipped, or gradients may not be clipped. | Use `uint8` frames in `[0,255]`, normalize once in the model, use `np.sign(reward)` for training rewards, keep DQN Huber loss/grad clip 10 and PPO grad clip 0.5. |
| `recent_mean_return` looks much lower than `recent_mean_game_return` | `recent_mean_return` is per-life because the life-loss wrapper emits terminal transitions on life loss. | Explain the distinction; benchmark discussion should use per-game returns. See `preprocessing-and-devices.md` for the wrapper semantics. |
| W&B prompts for login, fails with authentication/network errors, or logs to an unexpected account | `--wandb` is opt-in and uses the user's active W&B credentials. | Run the user's W&B login first, verify the active account/project, or omit `--wandb`. Without `--wandb`, the workflow should not touch the network. |
| Full training gives scores far below README rows after a short run | Atari learning needs millions of frames; early returns are not comparable to 10M-step results. | Check the global frame count, not just wall-clock time. Use the README rows only as single-seed, hardware/protocol-specific reference points. |
| User compares results to older deterministic `*-v4` papers | The workflow uses `ALE/*-v5` with sticky actions, making direct absolute-score comparison invalid. | Compare only under the same env id, sticky-action setting, frame budget, preprocessing, and seed protocol. State the caveat explicitly in reports. |
| Breakout agent waits without launching the ball after reset/life loss | A `FIRE` action may be required. | The preprocessing contract includes a fire-reset wrapper that presses action `1` if `FIRE` is present in action meanings. If using a custom env wrapper, preserve this behavior. |

## When to stop and ask for user resources

Stop instead of silently proceeding when the requested task requires any of the
following and they are absent or unauthorized:

- Atari ROM installation or license acceptance.
- W&B authentication/network logging.
- A full multi-hour/multi-million-frame benchmark run.
- A specific unavailable hardware backend such as CUDA or MPS.
- Human rendering on a headless machine.

For purely algorithmic checks, do not ask for those resources; run the bundled
synthetic smoke helper instead.
