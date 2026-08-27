# CartPole troubleshooting

Use this guide for DQN, A2C, and PPO CartPole-v1 failures involving dependencies, headless rendering, Gymnasium API behavior, checkpoint formats, tensor shapes, and smoke validation.

## Quick triage

1. **No display?** Run training without `--render` and avoid `--test`; use `python scripts/cartpole_smoke.py` for headless synthetic checks.
2. **Checkpoint error?** Confirm the algorithm/file pairing in [cli-and-checkpoints.md](cli-and-checkpoints.md): DQN/PPO use raw state dicts; A2C uses nested `actor`/`critic` state dicts.
3. **Tensor shape error?** CartPole state must be a 4-value float vector and action must be an integer in `{0, 1}`.
4. **Training looks slow?** Rendering slows the loop, DQN waits for 1000 replay samples before SGD, and PPO updates only after each 1024-step rollout.

## Failure matrix

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | Runtime environment lacks PyTorch. | Install/sync the repository runtime environment before training. The smoke script also requires PyTorch because it checks the actual model/update shapes. |
| `ModuleNotFoundError: No module named 'gymnasium'` | Gymnasium classic-control dependency is missing. | Install/sync the runtime dependencies before running training or `--test`. The bundled smoke script can still check model/checkpoint logic because it does not import Gymnasium. |
| `ModuleNotFoundError: No module named 'pygame'` | Pygame dependency is missing. | Install/sync runtime dependencies for `--render` or `--test`. Plain synthetic smoke checks do not require Pygame. |
| Pygame error such as `No available video device`, `cannot open display`, or `XDG_RUNTIME_DIR is invalid` | `--render` or `--test` requested `render_mode="human"` on a headless host. | Omit `--render`, avoid `--test`, or provide a real display/X server/Xvfb appropriate for the host. Use `python scripts/cartpole_smoke.py --require-render-ready` to preflight display variables without opening a window. |
| `--test` opens a window even though no `--render` flag was supplied | Shared helper treats `args.test` as a request for human rendering. | This is expected. For headless checkpoint inspection, use the smoke script's `--algorithm ... --checkpoint ...` validator. |
| Test mode never exits | The shared replay helper loops forever. | Stop with `Ctrl-C` or close the Pygame window if a display exists. Do not run `--test` as an unattended CI job. |
| `FileNotFoundError: cartpole_dqn.pt`, `cartpole_a2c.pt`, or `cartpole_ppo.pt` | Test mode looks for the algorithm's default checkpoint in the current working directory. | Train first, run from the directory containing the checkpoint, or pass the file to the smoke validator to diagnose structure. |
| DQN load reports `Unexpected key(s): actor, critic` | A2C checkpoint passed to DQN. | Use `cartpole_dqn.pt`, not `cartpole_a2c.pt`. |
| A2C raises `KeyError: 'actor'` or `KeyError: 'critic'` | Raw DQN/PPO state dict passed to A2C. | Use `cartpole_a2c.pt`, whose payload is `{"actor": ..., "critic": ...}`. |
| PPO load reports keys like `net.0.weight` | DQN checkpoint passed to PPO. | Use `cartpole_ppo.pt` or retrain PPO. |
| `size mismatch for ... weight` while loading | Checkpoint was produced by a different network architecture or different state/action sizes. | Use the matching CartPole architecture: state size 4, action size 2. Retrain if the implementation changed. |
| `RuntimeError: mat1 and mat2 shapes cannot be multiplied` | State tensor shape is wrong, often nested incorrectly or missing the 4 features. | Feed a single state as shape `(4,)` or a batch as `(batch, 4)` with `dtype=float32`. |
| `TypeError` or unpacking error around `env.step` | Old Gym API expected one `done` flag, but Gymnasium returns five values. | Use `next_state, reward, terminated, truncated, info = env.step(action)` and set `done = terminated or truncated`. |
| Reward values look like `0.1` and `-1` instead of Gym's `+1` | The training update uses shaped reward while the printed score is raw episode length. | This is intentional. Compare raw scores for performance and shaped rewards for update logic. |
| DQN appears not to learn for early episodes | Replay training is disabled until `len(memory) >= train_start` with `train_start=1000`. | Let enough transitions accumulate, or for a tiny diagnostic use the smoke script's reduced synthetic replay threshold. |
| PPO prints only once per large block of environment steps | PPO batches 1024 single-env rollout steps before each optimization pass. | This is expected. Do not judge PPO liveness by per-step prints. |
| A2C/PPO test score varies across runs | Their test action pickers sample from categorical policies. | For deterministic demonstrations, modify the action picker to choose `argmax(logits)`; do not assume source test mode is deterministic. |
| Full training passes smoke but fails to solve CartPole | Smoke validates model/API invariants, not convergence. | Check random seed, dependency versions, render overhead, reward shaping, and whether training ran long enough. Report raw mean return over recent episodes, not smoke status. |
| `torch.load` warning or refusal for untrusted pickle-like files | Newer PyTorch may prefer weight-only loading for security. | The repository checkpoints are plain state dictionaries; load only files you trust, and prefer weight/state-dict payloads. The smoke validator loads to CPU and checks expected keys. |

## Headless rendering guidance

The shared CLI has no separate headless evaluation flag. Because `--test` sets `render_mode="human"`, a checkpoint can be structurally valid while replay still fails on a server without a display. Separate the concerns:

```bash
# Safe: synthetic model/update/checkpoint diagnostics, no display
python scripts/cartpole_smoke.py
python scripts/cartpole_smoke.py --algorithm dqn --checkpoint cartpole_dqn.pt

# Display-dependent: only use when a human window is available
uv run python 1-dqn.py --test
```

If a user asks to watch training remotely, recommend a real display forwarding setup rather than hiding the issue with dummy video drivers; a dummy driver may let initialization proceed but does not provide a useful human visualization.

## Checkpoint mismatch diagnostic flow

1. Identify the requested algorithm: DQN, A2C, or PPO.
2. Identify the file name and payload shape:
   - DQN: raw Q-network state dict, typically keys such as `net.0.weight`.
   - A2C: nested dictionary with top-level `actor` and `critic`.
   - PPO: raw actor-critic state dict, typically keys under `shared`, `policy`, and `value`.
3. Run the smoke validator with the expected algorithm:

```bash
python scripts/cartpole_smoke.py --algorithm a2c --checkpoint cartpole_a2c.pt
```

4. If validation fails, do not coerce keys between algorithms. Retrain or locate the matching checkpoint.

## PPO GAE diagnostics

When checking PPO behavior manually:

- `dones[t]` must be `1.0` for terminal/truncated transitions so the GAE recursion resets.
- `last_value` bootstraps only the final rollout boundary; it should not leak across terminal transitions inside the rollout.
- Advantages are normalized per batch after `compute_gae`; do not compare raw and normalized advantages directly.
- The clipped objective uses the **minimum** of clipped and unclipped terms before negation. Reversing this is a common implementation bug.

## A2C update diagnostics

- The actor should see `advantage.detach()` so its gradient does not update the critic through the advantage.
- The critic target should be treated as a constant.
- For terminal transitions, target is just the shaped reward; do not bootstrap `V(next_state)`.

## DQN update diagnostics

- The target network, not the online network, supplies `max_a' Q(s',a')` for the TD target.
- Terminal transitions zero the bootstrap term.
- `append_sample` decays epsilon; `train_model` does not decay epsilon by itself.
- `update_target_model()` is a hard copy and is called once per episode in the workflow.
