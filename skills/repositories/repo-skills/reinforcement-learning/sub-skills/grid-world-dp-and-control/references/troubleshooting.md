# GridWorld Troubleshooting

Use this reference when a GridWorld adaptation fails, hangs, renders incorrectly, or gives surprising values. All runtime checks should use the bundled self-contained script under `scripts/`; the original training files are provenance labels only.

## Quick triage commands

```bash
# Show available checks and options.
python scripts/grid_world_smoke.py --help

# Default: DP + tabular + dynamic + optional Torch neural checks.
python scripts/grid_world_smoke.py

# Coordinate and Bellman checks only.
python scripts/grid_world_smoke.py --section dp

# Require Torch neural checks to run rather than being skipped.
python scripts/grid_world_smoke.py --section neural --strict-torch
```

## Coordinate and action-order problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Policy/value arrows point to transposed cells. | DP state `[row, col]` was passed directly to a drawing helper expecting `(x, y)` or `[col, row]`. | Keep DP tables as `V[row][col]`, but convert for drawing with `x = col`, `y = row`. |
| Moving `right` changes the row in a DP adaptation. | Action deltas were written for `[col, row]` instead of `[row, col]`. | DP deltas must be `up=(-1,0)`, `down=(+1,0)`, `left=(0,-1)`, `right=(0,+1)` on `[row, col]`. |
| Tabular SARSA/Q-learning goes to `[0, 1]` after action `3` from `[0, 0]`. | Static tabular state was mistakenly treated as `[row, col]`. | Static tabular state is `[col, row]`; action `3=right` should move `[0,0] -> [1,0]`. |
| A dynamic Deep SARSA action `2` moves right but a tabular action `2` moves left. | The dynamic action order differs from the static tabular action order. | Static tabular: `2=left`, `3=right`. Dynamic neural world: `2=right`, `3=left`. Convert policies explicitly when moving code between worlds. |
| A neural policy samples action `4` and the agent does not move. | The source-compatible neural agents expose five outputs, while the dynamic environment only moves for actions `0..3`. | Treat `4` as a no-op for source-compatible behavior, or reduce action size to four everywhere: model output, sampling, loss indexing, and tests. |

## Dynamic programming issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Terminal state policy lookup crashes or returns a scalar instead of a list. | The goal `[2,2]` has no action policy in the educational workflow. | Special-case `[2,2]`: keep `V[2][2]=0.0`, policy `[]`, and stop rollouts before selecting an action there. |
| Values differ slightly from the visual example. | The educational workflow rounds each sweep to two decimals. | If matching the example, round `V_new` after each sweep. If implementing for research, document that you removed intermediate rounding. |
| Policy iteration does not change after `policy_improvement`. | `policy_evaluation` was not run first, or all current Q candidates tie. | Run several evaluation sweeps before improvement; inspect the greedy candidate values for one state. |
| Value iteration arrows show too many ties. | Too few value-iteration sweeps have been run, so many states remain equal. | Run additional sweeps until value changes are small, then extract the greedy policy. |
| Rewards look mirrored. | Reward table indexes were interpreted as `[col][row]`. | DP reward table is indexed as `reward[row][col]`; the negative cells are `[1,2]` and `[2,1]`, goal `[2,2]`. |

## Tabular SARSA and Q-learning issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Q-table never updates. | State keys mismatch between writes and reads, commonly list/tuple/string inconsistency. | Pick one key style. For source-compatible overlays use `str([col, row])`; for new code, tuples such as `(col, row)` are safer if used consistently. |
| SARSA update equals Q-learning update unexpectedly. | `next_action` was chosen greedily or after overwriting the state/action. | SARSA must sample `next_action` under the current epsilon-greedy behavior policy before the update. |
| Q-learning is too optimistic near obstacles compared with SARSA. | This is expected: Q-learning is off-policy and bootstraps from greedy next-state value. | Explain the on-policy/off-policy distinction; do not force both algorithms to match. |
| Learning seems random run-to-run. | Epsilon-greedy tie-breaking and exploration are stochastic. | Seed Python, NumPy, and Torch if reproducibility matters; use deterministic tie-breaking only if that change is intentional. |
| Agent bounces at grid edges. | Boundary clipping keeps moves inside the grid. | This is expected. Check whether repeated edge actions come from an untrained or tied Q-table. |

## Rendering and display failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Script hangs waiting for a window or user clicks. | The DP viewer is an interactive button-driven Pygame loop. | Use the bundled smoke script for validation. Only run visual demos in an interactive desktop session. |
| `pygame.error: video system not initialized` or missing display. | Pygame tried to open a window on a headless server. | Keep validation headless. For dynamic workflows, use a `render_mode=None` pattern. For a real visual run, configure a display separately. |
| Training is extremely slow. | Rendering every step dominates runtime. | Disable or guard rendering in training and smoke checks. Render only short demonstrations. |
| Closing a Pygame window exits the process. | The viewer pumps a quit event and exits. | Treat GUI loops as interactive demos, not library APIs. Keep reusable checks non-rendering. |

## Torch/neural-control issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'`. | Torch is not installed in the current environment. | Run non-neural checks with `--section dp`, `--section tabular`, or `--section dynamic`; install Torch before using `--section neural --strict-torch`. |
| Neural smoke is skipped but the command exits successfully. | Default smoke treats Torch as optional so pure-Python checks remain useful. | Add `--strict-torch` when Deep SARSA/REINFORCE verification is required. |
| `mat1 and mat2 shapes cannot be multiplied` or similar. | Dynamic state vector length is not 15, or a batch dimension was mishandled. | Ensure each state has three obstacle feature groups of four values plus three goal features. Convert to `float32`; add batch dimensions only when the network expects them. |
| `IndexError` selecting Q-value or log-prob. | Action size changed but model output or sampled action range was not updated. | Keep five outputs for source-compatible action `0..4`, or consistently change every action-size use to four. |
| Deep SARSA diverges or loss behaves oddly. | TD target was left attached to the gradient graph. | Compute the target under no-grad/stop-gradient semantics. Only `Q(s)[a]` should carry gradient. |
| REINFORCE loss becomes `nan`. | Return standardization divided by near-zero standard deviation, or logits/probabilities became invalid. | Use `std + 1e-8`, check finite logits, and keep learning rate small. Tiny identical-reward trajectories are not useful learning signals. |
| REINFORCE buffers keep growing. | Episode buffer was not cleared after the policy update. | After each `train_model` call, reset `states`, `actions`, and `rewards` to empty lists. |

## Smoke-script interpretation

| Result | Meaning | Next step |
| --- | --- | --- |
| `PASS dp` | Bellman updates and row/col safeguards worked. | Use DP formulas from `algorithm-guide.md` for adaptations. |
| `PASS tabular` | Static `[col,row]` actions and TD updates worked. | Proceed with tabular SARSA/Q-learning changes. |
| `PASS dynamic` | Headless dynamic state/action behavior worked. | Use this fixture for Deep SARSA/REINFORCE environment-shape checks. |
| `PASS neural` | Torch one-step Deep SARSA and REINFORCE checks worked. | This proves API/update shape only, not convergence. |
| `SKIP neural` | Torch was unavailable and strict mode was not requested. | Install Torch or rerun with `--strict-torch` if neural coverage is required. |
| Failure with assertion text about coordinates. | A row/column or action-order invariant was violated. | Fix coordinate conversion before debugging algorithm math. |

## What not to infer from these checks

- Passing smoke checks does not prove an agent will train to optimal behavior.
- One Bellman sweep does not prove DP convergence.
- One TD update does not prove stable tabular learning.
- One neural optimizer step does not prove policy improvement.
- Headless checks intentionally do not validate Pygame rendering quality.
