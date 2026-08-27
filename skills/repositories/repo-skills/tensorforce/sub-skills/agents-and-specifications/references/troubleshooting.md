# Agent Troubleshooting

## Purpose

Use this file when Tensorforce agent construction, state/action specs, action masking, or manual interaction loops fail. Start with the symptom, check the likely cause, then apply the recovery step before changing unrelated modules.

## Import and dependency symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError` while importing `tensorforce`, `tensorflow`, or `gym` | Tensorforce 0.6.5 depends on an older TensorFlow/Gym/NumPy ecosystem. | Use a compatible Python/TensorFlow/NumPy/Gym environment. In particular, avoid NumPy 2.x with older Gym releases. Re-run a minimal import check before debugging specs. |
| `AttributeError: module 'numpy' has no attribute 'bool8'` | Older Gym code with NumPy 2.x. | Pin NumPy below 2 or use a Gym/TensorFlow stack compatible with Tensorforce 0.6.5. |
| TensorFlow logs say CUDA drivers are missing | TensorFlow is probing GPU but the selected workflow only requires CPU. | If the task is CPU-compatible, continue with `config=dict(device='CPU')`. If the user explicitly requires GPU acceleration, verify their TensorFlow GPU install outside this sub-skill. |

## `Agent.create(...)` failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TensorforceError.value` for `Agent.create` argument `agent` | Unknown alias or non-importable module path. | Use one of the verified aliases in [`api-reference.md`](api-reference.md), or make the custom Agent subclass importable and pass its module path/class. |
| Missing `states` or `actions` error | No `environment` was passed and manual specs were omitted. | Prefer `Agent.create(..., environment=environment)`. Otherwise pass explicit `states` and `actions` primitive or multi-component specs. |
| Missing `max_episode_timesteps` for `ppo`, `trpo`, or `vpg` | The algorithm requires an episode horizon and the environment did not provide one. | Pass `max_episode_timesteps` to `Environment.create` or directly to `Agent.create`. |
| `TypeError` about missing `batch_size` | The selected alias requires `batch_size`. | Add a task-appropriate `batch_size`; for smoke/debug, use `random` instead of a learning algorithm. |
| `TypeError` about missing `memory` | DQN/DPG-family alias requires replay memory. | Add `memory=<capacity>` or a memory spec. Route memory catalogs to `../modules-and-configuration/`. |
| Missing `update`, `optimizer`, `objective`, or `reward_estimation` | The `tensorforce`/`default` generic agent was selected without its required custom-learning arguments. | Either provide all required generic-agent fields or switch to a higher-level alias such as `ppo` when appropriate. |
| State/action shape assertion fails | The runtime value includes a batch dimension in the spec or omits a state component. | Specs describe one state/action value only. Keep batch dimensions in `act`/`experience` inputs, not in `shape`. |
| DQN-family agent rejects continuous actions or behaves nonsensically | Q-learning aliases are intended for discrete integer actions. | Use integer `actions` with `num_values`, or choose a continuous-action algorithm such as DPG/PPO depending on the task. |

## State/action spec fixes

1. For a single float vector observation, use `states=dict(type='float', shape=(N,))`.
2. For a single discrete action, use `actions=dict(type='int', shape=(), num_values=K)`.
3. For multiple components, use one top-level dict layer per component name.
4. `num_values` is mandatory for every integer component.
5. Float bounds are optional but should match environment semantics when actions are bounded.
6. If `act` receives a dict for a singleton state, use key `state` unless the dict only contains the raw singleton value through Tensorforce's singleton handling. Auxiliary mask keys may appear beside `state`.

## Action masking failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Masked action can still be selected | Wrong mask key, non-integer action, masking disabled, or invalid shape. | For singleton actions use `action_mask`; for named action `move`, use `move_mask`. Ensure the target action spec is `type='int'` with `num_values`, `config.enable_int_action_masking` is true, and mask shape is `action.shape + (num_values,)`. |
| `states` validation complains about extra `action_mask` | The mask was passed while masking is disabled or the action is not maskable. | Re-enable `config=dict(enable_int_action_masking=True)` and ensure the action is integer/discrete. Do not include masks for float/bool actions. |
| Mask shape assertion or TensorFlow boolean-mask error | The mask shape does not match the action spec. | For scalar `num_values=3`, pass shape `(3,)`; for action shape `(2,)` and `num_values=4`, pass `(2, 4)`. |
| Random or policy sampling errors when all entries are masked | No valid action option remains. | Guarantee at least one `True` mask value for every action element. Add environment-side fallback if the user's domain can temporarily make all actions invalid. |
| Multi-action dict masks only one action | Other integer action names also need their own masks if they should be constrained. | Add one mask per named integer action: `move_mask`, `turn_mask`, etc. Missing masks default to all-valid. |

Run:

```bash
python scripts/action_masking_smoke.py --trials 20
```

A passing run proves the installed package respects a singleton integer `action_mask` for the bundled smoke case.

## `act`/`observe` ordering errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Calling agent.act must be preceded by agent.observe` | A non-independent `act` was called twice for the same parallel id. | Call `observe` after every online `act`, or use `independent=True` for evaluation/probing calls that should not be learned from. |
| `Calling agent.observe must be preceded by agent.act` | `observe` was called before any online `act`, called twice, or used during independent evaluation. | Only call `observe` once after a non-independent `act`. Do not observe independent actions. |
| `Episode longer than max_episode_timesteps` | Loop did not terminate or report time-limit terminal before the configured horizon. | Fix the environment loop, set the correct max timesteps, or return/use terminal code `2` for time-limit aborts. |
| `Agent.act` rejects `internals` | Internals were supplied while `independent=False`. | Pass `internals` only with `independent=True`; for online training, Tensorforce manages internals internally. |
| Independent evaluation returns only actions, not `(actions, internals)` | `internals` argument was omitted. | Initialize `internals = agent.initial_internals()` and pass it to `act(..., independent=True)` if the caller expects a tuple. |

Run:

```bash
python scripts/act_observe_smoke.py --episodes 1 --max-timesteps 3
```

A passing run validates the basic online loop plus an independent evaluation pass.

## `experience(...)` / `update()` errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Calling agent.experience is not possible mid-episode` | An online `act` occurred without its matching `observe`. | Complete or discard the online episode before feeding offline traces. Keep online and offline interaction modes separate. |
| `Agent.experience() requires full episodes as input` | The final terminal entry is `False`/`0`. | Feed complete episodes only; end the trace with terminal `True`/`1` or abort/time-limit `2`. |
| Length mismatch for states/actions/internals/reward/terminal | Per-timestep lists have different lengths. | Append one state, internal state, action, terminal, and reward per timestep before calling `experience`. |
| Recurrent or stateful behavior does not learn as expected from offline traces | Independent collection can miss updates for some stateful preprocessing/network layers. | Avoid stateful layers such as `exponential_normalization` for this pattern unless you add dedicated validation. Prefer online `act`/`observe` or `Runner` when stateful online behavior matters. |

## Parallel interaction mismatches

| Symptom | Likely cause | Recovery |
|---|---|---|
| Parallel id out of range or `len(parallel)` mismatch | Agent was created with too few `parallel_interactions`, or batched arrays have inconsistent first dimensions. | Create the agent with `parallel_interactions=N`, pass exactly N entries when using default parallel ids, and keep reward/terminal/parallel arrays the same length. |
| Independent mode with `parallel != 0` fails | Independent `act` does not use parallel interaction buffers. | For independent batches, pass batched states/internals without a non-zero `parallel` argument; for true parallel environments use online mode or `Runner`. |
| Socket/multiprocessing behavior hangs or is unclear | This is runner/environment orchestration, not agent spec construction. | Route to `../runner-and-cli-workflows/` and `../environments-and-interaction/`. |

## When to route elsewhere

- **Network/layer/memory/objective/optimizer registry errors**: `../modules-and-configuration/`.
- **Custom environment `reset`/`execute` return-shape errors or optional Gym/adaptor issues**: `../environments-and-interaction/`.
- **Runner stopping criteria, evaluation environments, callbacks, CLI flags, or parallel execution modes**: `../runner-and-cli-workflows/`.
- **Save/load checkpoint formats, summaries, recording, pretraining, or SavedModel export**: `../persistence-export-and-recording/`.
