# Troubleshooting

## Purpose

Read this when easy-MARL command construction, environment selection, scenario loading, hyperparameter dispatch, imports, training logs, or extension work fail. The guidance is bounded to safe diagnosis; it does not certify full training or benchmark reproduction.

## Quick diagnosis table

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: <env> does not exist.` | The selected entry script does not support that environment family. | Use the compatibility table in `easy-marl-workflows.md` or the bundled command builder. For example, DQN uses discrete environments only; DDPG uses continuous environments only; PPO supports all four easy-MARL families. |
| `ValueError: <agent> does not exist.` | The selected entry script does not import that agent name. | Check capitalization and family. `IDQN`, `VDN`, `QMIX`, and source-level `CommNet` belong to DQN; `IDDPG` and `MADDPG` belong to DDPG; `IPPO` and `MAPPO` belong to PPO. |
| `NotImplementedError: <env>_<agent> does not exist.` | `hyper_param_setting.py` has no branch for the chosen environment/agent pair. | Add a matching hyperparameter module and dispatcher branch, or choose an implemented pair. This commonly affects CommNet. |
| Command accepts no scenario or scenario appears ignored | Meeting environments do not use scenario names. | Remove `--scenario-name` for `discrete_meeting` and `continuous_meeting`. Use scenarios only for `discrete_magym` and `continuous_mpe`. |
| Empty scenario silently becomes `Switch4-v0` or `simple_tag` | Source hyperparameter classes define internal defaults for MAGYM/MPE. | Prefer explicit `--scenario-name` for reproducibility. The bundled command builder requires explicit scenarios for `discrete_magym` and `continuous_mpe`. |
| MAGYM registration fails around Gym registry APIs | The wrapper uses older Gym registration patterns such as `envs.registry.all()` and private spec kwargs. | Use a Gym version compatible with those APIs or patch registration before training. Do not treat this sub-skill as proof that modern Gym versions work. |
| MPE scenario loading fails | Scenario name does not match a vendored scenario module, or scenario dependencies/rendering are unavailable. | Use known scenario module names such as `simple_tag` or `simple_spread`. Verify that the scenario file exists in the environment package before running training. |
| `ImportError: No module named tensorboardX`, `torch`, `gym`, or similar | Required Python dependency is missing. | Install/verify the dependency in the runtime environment chosen by the user. This sub-skill does not install packages or record private environment details. |
| `NotImplementedError` from `render()` | Meeting environments have placeholder render methods. | Avoid rendering for `discrete_meeting` and `continuous_meeting`, or implement a renderer as a separate code change. |
| Shape mismatch in action or observation tensors | Agent family and environment action type are mismatched, or a new environment wrapper does not expose expected spaces. | Re-check action type: DQN expects discrete action IDs; DDPG expects continuous actions; PPO entry branches on discrete/continuous spaces. Validate `agent_count`, `observation_space`, `state_space`, and `action_space` after environment construction. |
| CommNet starts but fails at dispatch or training | CommNet is only partially wired. | Add CommNet hyperparameter modules and dispatcher branches, then adapt `CommNet.train` to the current `Buffer.sample()` dictionary contract before running training. |
| `test/test.py` imports missing `envs.discrete_env.smac.smac_env` | The test file is stale/reference-only for this inspected easy-MARL tree. | Do not use that test as a native validation source for this skill. Prefer command-builder checks and bounded, dependency-aware smoke cases. |
| Logs or model files appear in unexpected directories | Entry scripts write relative to the training working directory. | Expect `./logs/{exp_name}/{exp_id}` plus checkpoint prefixes under the same tree. Run from the intended easy-MARL working directory and clean up after experiments if needed. |

## Command-builder failures

`scripts/build_easy_marl_command.py` rejects incompatible combinations before any ML import or training starts. Use it to catch:

- DQN requested on continuous environments.
- DDPG requested on discrete environments.
- Missing scenario for `discrete_magym` or `continuous_mpe`.
- Unknown agent or environment spelling.

Example rejected request:

```bash
python scripts/build_easy_marl_command.py --agent-name IDDPG --env-name discrete_meeting
```

Expected outcome: non-zero parser error explaining that `IDDPG` is not compatible with `discrete_meeting` and naming allowed environments.

## Training-cost and verification limits

Do not present a command as benchmark-verified just because the command was constructed. Full RL training can be slow, stochastic, dependency-sensitive, and hardware-sensitive. The generated skill only supports safe routing, command construction, configuration reasoning, and extension planning.

Treat these as prerequisites or limitations unless another verified artifact proves them:

- CUDA/GPU behavior.
- MAGYM scenario training completion.
- MPE scenario training completion.
- SMAC, API-network, MuJoCo, DMControl, D4RL, Waymo, or other external benchmark reproduction.
- Long-run convergence or paper-level performance.

## Extension recovery flow

When a new algorithm/config pair fails:

1. Confirm the correct entry script family from `easy-marl-workflows.md`.
2. Confirm a hyperparameter module exists for exactly `{env_name}_{agent_name}`.
3. Confirm `hyper_param_setting.py` imports that module in an explicit branch.
4. Confirm the entry script imports the algorithm class for exactly that `agent_name`.
5. Confirm the algorithm method signatures match the entry script's expected calls.
6. Confirm the algorithm's `train` method consumes the current `Buffer.sample()` structure.
7. Only after those checks pass, consider a tiny bounded training run if dependencies and runtime budget permit.

## Environment-wrapper recovery flow

When a new or existing environment wrapper fails:

1. Verify it exposes `agent_count`, `observation_space`, `action_space`, and `reset()`/`step()` with the expected easy-MARL return shape.
2. Verify `state_space` and state arrays exist for workflows that use centralized state, such as QMIX or MAPPO.
3. Verify action-space type matches the entry script family.
4. For scenario-aware wrappers, validate scenario names before training.
5. For wrappers using older Gym APIs, decide whether to pin a compatible Gym version or patch registration.

## Stop conditions

Stop and report a prerequisite/block instead of continuing when:

- The user asks for an external benchmark or dataset that is not bundled/verified here.
- Required dependencies would require network installation or large downloads not already approved.
- A requested scenario cannot be found or registered.
- The command would launch expensive training but the user's request only needed routing, config inspection, or command construction.
- A requested algorithm is only conceptual or partially wired in the inspected code.
