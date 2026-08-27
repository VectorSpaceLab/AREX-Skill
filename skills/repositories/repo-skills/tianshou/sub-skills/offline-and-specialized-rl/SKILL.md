---
name: offline-and-specialized-rl
description: "Use Tianshou 2.0.1 offline RL, imitation learning,
  model-based/curiosity wrappers, multi-agent wrappers, and safe evaluation
  utilities without accidentally launching expensive runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Offline and Specialized RL

Use this sub-skill when the request mentions offline RL datasets or algorithms (`CQL`, `BCQ`, `TD3+BC`, `DiscreteBCQ`, `DiscreteCQL`, `DiscreteCRR`), imitation learning (`GAIL`, behavior cloning, expert buffers), model-based or curiosity methods (`PSRL`, `ICM`), multi-agent algorithm wrappers, or multi-seed evaluation/benchmark utilities.

## Read First

- `references/api-reference.md`: class map, constructor shape, optional dependency boundaries, and cross-skill dependencies.
- `references/workflows.md`: safe workflows for offline buffers, imitation learning, model-based wrappers, MARL, and evaluation launchers.
- `references/troubleshooting.md`: import, optional dependency, dataset schema, launcher, and benchmark-scale failure handling.
- `scripts/check_offline_api_imports.py`: safe smoke probe for installed API availability and signatures; it performs no dataset downloads, training, networking, or source-checkout reads.

## Route Here For

- Building an offline trainer around a fixed `ReplayBuffer` for `CQL`, `BCQ`, `TD3BC`, `DiscreteBCQ`, `DiscreteCQL`, or `DiscreteCRR`.
- Preparing vanilla imitation learning or `GAIL` from expert data while validating expert/action schema before training.
- Wrapping existing on-policy/off-policy algorithms with `ICMOnPolicyWrapper` or `ICMOffPolicyWrapper`.
- Creating tabular `PSRL` components for small discrete state/action MDPs.
- Combining per-agent algorithms with `MultiAgentOffPolicyAlgorithm` or random masked agents for PettingZoo-style workflows.
- Planning bounded multi-seed evaluation with `SequentialExpLauncher`, `JoblibExpLauncher`, or rliable outputs without launching full benchmarks.

## Route Elsewhere

- General algorithm, policy, network, optimizer, collector, and trainer wiring belongs in `../procedural-training/SKILL.md`.
- `ReplayBuffer`, `VectorReplayBuffer`, `Batch`, collector hooks, and buffer serialization mechanics belong in `../data-collection/SKILL.md`.
- Gymnasium/PettingZoo environment wrapping, vector env worker selection, action masks from env wrappers, and optional env engines belong in `../envs-and-vectorization/SKILL.md`.
- Declarative high-level `Experiment` builder chains and persisted experiment directories belong in `../highlevel-experiments/SKILL.md`.

## Safety Defaults

- Treat D4RL, Atari, MuJoCo, EnvPool, PettingZoo games, VizDoom, robotics, and rliable/joblib stacks as optional until imports are proven.
- Do not run benchmark scripts, Atari/D4RL examples, or multi-seed experiment launchers as a smoke test; first reduce to one seed, one tiny env/task, low epoch/step counts, and explicit output directories.
- Validate offline buffer fields before choosing an algorithm: `obs`, `act`, `rew`, `done`/`terminated`/`truncated`, and `obs_next` must be present, aligned, finite, and shape-compatible with the policy and action space.
- Keep dataset loading separate from algorithm construction; use this sub-skill for algorithm/evaluation choices and `../data-collection/SKILL.md` for buffer mechanics.
