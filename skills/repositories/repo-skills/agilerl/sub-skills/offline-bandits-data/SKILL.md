---
name: offline-bandits-data
description: "Use AgileRL offline RL datasets, replay/data conversion, CQL/ILQL,
  contextual bandits, NeuralUCB/NeuralTS, and BanditEnv workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL Offline RL And Bandit Data

Use this sub-skill for AgileRL offline reinforcement learning, replay/data conversion, `CQL`, `ILQL`, `train_offline`, contextual bandits, `NeuralUCB`, `NeuralTS`, and `BanditEnv` workflows.

## Read First

- `references/workflows.md` for offline RL and contextual bandit recipes.
- `references/data-formats.md` for transition, HDF5/Minari, and tabular bandit schemas.
- `references/api-reference.md` for replay/bandit/offline APIs.
- `references/troubleshooting.md` for shape, schema, and network/download failures.
- `scripts/inspect_bandit_setup.py --help` for a no-download synthetic bandit probe.

## Boundaries

- Use `../training-workflows/SKILL.md` for online Gymnasium PPO/DQN/DDPG/TD3 workflows.
- Use `../hpo-and-mutation/SKILL.md` for tournament/mutation configuration.
- Use `../llm-fine-tuning/SKILL.md` for language/LLM datasets and RL post-training environments.
- This sub-skill owns static transition datasets, replay filling, Minari/HDF5 handling, and one-step contextual bandit datasets.

## Offline RL Flow

1. Load or validate a dataset with observations, actions, rewards, next observations, and done/terminal flags.
2. Create an environment only for spaces/evaluation, not online data collection.
3. Create a `CQN`/`ILQL`-style population with `create_population(...)`.
4. Fill `ReplayBuffer` with `Transition(...).to_tensordict()` entries.
5. Configure HPO and call `train_offline(...)` or a custom offline loop.

## Contextual Bandit Flow

1. Prepare tabular or array features and targets.
2. Create `BanditEnv(features, targets)`.
3. Use `NeuralUCB` or `NeuralTS` with a discrete action space.
4. Use replay memory and `train_bandits(...)` or a custom one-step loop.

## Safe Validation

```bash
python scripts/inspect_bandit_setup.py --rows 8 --features 4 --arms 3
```

The helper creates synthetic in-memory data. It does not download UCI datasets or run training.
