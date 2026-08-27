# Configuration and Extension

## Purpose

Read this before changing easy-MARL hyperparameters, adding a new algorithm, adding a new scenario/config pair, or repairing a partially wired algorithm. It distills the dispatcher, hyperparameter class contracts, algorithm interface expectations, and safe extension points.

## Hyperparameter dispatch model

The easy-MARL dispatcher accepts only three command-line options:

- `--env-name`: environment family.
- `--scenario-name`: scenario identifier for scenario-aware environments.
- `--agent-name`: algorithm identifier.

It then computes `temp_args.exp_name = temp_args.env_name + "_" + temp_args.agent_name` and imports one hyperparameter class by explicit `if`/`elif` branches. For meeting environments it constructs `Hyperparameter()` and sets `args.exp_name` to `{env_name}_{agent_name}`. For scenario-aware environments it constructs `Hyperparameter(temp_args.scenario_name)` and sets `args.exp_name` to `{env_name}_{args.scenario_name}_{agent_name}`.

Operational consequence: adding an algorithm file is not enough. A runnable command also needs a matching hyperparameter module and a dispatcher branch.

## Implemented dispatcher combinations

| Environment | Implemented hyperparameter agent names |
| --- | --- |
| `discrete_meeting` | `IDQN`, `VDN`, `QMIX`, `IPPO`, `MAPPO` |
| `discrete_magym` | `IDQN`, `VDN`, `QMIX`, `IPPO`, `MAPPO` |
| `continuous_meeting` | `IDDPG`, `MADDPG`, `IPPO`, `MAPPO` |
| `continuous_mpe` | `IDDPG`, `MADDPG`, `IPPO`, `MAPPO` |

There are also legacy `mpe_*` hyperparameter files in the source tree, but the inspected dispatcher routes `continuous_mpe_*` names for current `continuous_mpe` commands. Do not treat the legacy `mpe_*` files as active command targets unless you also change the dispatcher and entry scripts.

## Hyperparameter class contract

All hyperparameter classes are plain Python objects whose attributes are read later by entry scripts, environments, buffers, and algorithms. Keep names stable.

Common attributes:

- `agent_name`, `env_name`, and optionally `scenario_name`.
- `exp_count`, `episode_count`, `episode_max_step`, `test_interval`, `test_episode_count`, and `save_interval`.
- `hidden_dim`, `hidden_layer_count`, `gamma`, and `clip_grad_norm`.
- `buffer_size` and `batch_size` for replay/episode buffer sampling.

DQN-specific attributes:

- `epsilon`, `min_epsilon`, `epsilon_decay`, `train_interval`.
- `lr` for the DQN optimizer.
- `state_dim` and action/observation dimensions are filled by `main_dqn.py` after environment construction, not by the hyperparameter file.

DDPG-specific attributes:

- `train_interval`, `lr_actor`, `lr_critic`, and `tau` for soft target updates.
- Continuous action dimensions are filled by `main_ddpg.py` after environment construction.

PPO-specific attributes:

- `lr` and `eps_clip`.
- PPO uses a fresh buffer per episode in `main_ppo.py`; it still expects `buffer_size` and `batch_size` on `args`.

## Adding a new algorithm safely

1. Choose the family whose entry loop matches the algorithm's action/data shape:
   - DQN family for discrete action IDs and `generate_q_list`.
   - DDPG family for continuous actions and `generate_action`.
   - PPO family for policy probabilities/actions and `generate_action_list`.
2. Implement the algorithm class in the matching family module with the method signatures expected by the entry script.
3. Confirm the algorithm's `train(...)` signature matches `Buffer.sample()` output for that entry script. Current `Buffer.sample()` returns a dictionary with `agent_specific` and `shared` sections, not a raw list of tuples.
4. Add an import branch in the correct entry script.
5. Add one hyperparameter module for each supported environment family and agent pair.
6. Add explicit branches in `hyper_param_setting.parse_arguments()` for each new `{env_name}_{agent_name}` pair.
7. Validate with a parser/command check first. Run only tiny or bounded training after dependencies and runtime cost are acceptable.

## Existing algorithm interface expectations

DQN agents used by `main_dqn.py`:

- Provide `generate_q_list(observation_list)` returning per-agent Q arrays.
- Provide `train(batch_experience_dict)` consuming current buffer dictionaries.
- Provide `save_model(model_dir)`; optional `load_weights(model_dir)` exists in the source agents.
- For value-decomposition agents, use `shared.team_reward`, `shared.state`, and/or `shared.next_state` as appropriate.

DDPG agents used by `main_ddpg.py`:

- Provide `generate_action(observation_list)` returning per-agent continuous action arrays.
- Provide `train(batch_experience_dict)` returning `(actor_loss, critic_loss)`.
- Provide `save_model(model_dir)` with actor/critic save behavior.

PPO agents used by `main_ppo.py`:

- Provide `generate_action_list(observation_list)` returning action IDs and action probabilities.
- Provide `train(batch)` returning a scalar loss.
- Provide `save_model(model_dir)`.

## Adding a new environment or scenario

For a new scenario within an existing scenario-aware family:

1. Confirm whether it is a MAGYM-style Gym id or an MPE-style vendored scenario module name.
2. Add or verify registration/loading in the relevant environment wrapper.
3. Create hyperparameter modules for every algorithm that should support that scenario's action type.
4. Keep `env_name` as the family name (`discrete_magym` or `continuous_mpe`) and put the scenario in `scenario_name`.
5. Use explicit scenario names in commands so `exp_name` is unambiguous.

For a new environment family:

1. Implement an environment wrapper exposing `agent_count`, `observation_space`, `state_space` when needed, `action_space`, `is_discrete`, `reset()`, and `step(action_list)` returning `((observation_list, state), (reward_list, team_reward), done, info)`.
2. Add a branch in the relevant entry script(s).
3. Add compatible hyperparameter modules and dispatcher branches.
4. Update command-building/validation logic so incompatible agent families are rejected before training.

## Special caution: CommNet

The source tree contains `algorithms/DQN_based/CommNet.py`, and `main_dqn.py` has a branch for `agent_name == 'CommNet'`. However, the inspected configuration is incomplete:

- The hyperparameter dispatcher has no `discrete_meeting_CommNet` or `discrete_magym_CommNet` branch.
- Matching CommNet hyperparameter files are absent.
- The CommNet `train` method expects an older raw batch shape, while current `main_dqn.py` passes `Buffer.sample()` dictionaries.

Therefore, for CommNet requests, route the user to an extension/repair plan: add hyperparameters, update dispatcher branches, and adapt `CommNet.train` to the current buffer dictionary contract before claiming trainability.

## Safe editing checklist

- Preserve command-line names exactly: `--agent-name`, `--env-name`, `--scenario-name`.
- Preserve agent-name capitalization used by dispatch branches.
- Keep scenario names explicit for MAGYM and MPE commands.
- Do not turn a conceptual MARL paper method into a runnable easy-MARL command unless the entry script, algorithm class, hyperparameter module, environment branch, and buffer contract all agree.
- Avoid broad training while testing a configuration edit. Prefer syntax checks, parser checks, and a tiny bounded run only after dependencies are known available.
