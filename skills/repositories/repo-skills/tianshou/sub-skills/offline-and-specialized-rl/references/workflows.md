# Offline and Specialized RL Workflows

These workflows are safe, bounded patterns for Tianshou 2.0.1 specialized algorithms. They intentionally avoid downloading datasets, running benchmark suites, or starting long training jobs by default.

## Bounded API Smoke

1. Run `python skills/tianshou/sub-skills/offline-and-specialized-rl/scripts/check_offline_api_imports.py --help` to confirm the helper itself is usable.
2. In an environment where `tianshou` and its core dependencies are installed, run the helper with no arguments to print class availability and signatures.
3. If optional evaluation packages are not installed, the helper reports evaluation imports as optional failures instead of starting any experiments.
4. Use `--strict` only when the selected optional groups are expected to be installed and importable.

## Fixed Offline Replay Buffer For CQL/BCQ/TD3BC

1. Choose the algorithm by action space:
   - Continuous actions: `CQL` with `SACPolicy`, `BCQ` with `BCQPolicy`, or `TD3BC` with `ContinuousDeterministicPolicy`.
   - Discrete actions: `DiscreteBCQ`, `DiscreteCQL`, or `DiscreteCRR`.
2. Prepare the offline data as a `ReplayBuffer`-compatible schema before constructing the algorithm: same length for `obs`, `act`, `rew`, terminal flags, and `obs_next`; finite numeric values; and action values matching the action space.
3. Use `ReplayBuffer.from_data(...)`, `VectorReplayBuffer.load_hdf5(...)`, or a previously serialized buffer only after schema validation. Buffer construction, sampling, slicing, and HDF5/pickle details belong in `../data-collection/SKILL.md`.
4. Construct the policy/networks/optimizers exactly as for the matching online base algorithm, then wrap with the offline algorithm class.
5. Use `OfflineTrainerParams(buffer=..., test_collector=..., max_epochs=..., epoch_num_steps=..., batch_size=...)`; trainer parameter tuning and collector setup belong in `../procedural-training/SKILL.md`.
6. For a smoke run, use a tiny synthetic or already-local buffer and extremely small epoch/step counts. Do not invoke D4RL, Atari, or benchmark scripts as the first validation.

## Behavior Cloning And GAIL

- `ImitationPolicy` maps an actor to discrete argmax actions or continuous regression outputs; `OffPolicyImitationLearning` updates from off-policy batches and `OfflineImitationLearning` updates from a fixed offline buffer.
- `GAIL` extends PPO-style on-policy training and requires an expert `ReplayBuffer`, a discriminator network `disc_net`, and a discriminator optimizer `disc_optim`.
- Validate that expert and policy batches share compatible observation and action dimensions before creating `GAIL`; the discriminator receives concatenated state-action tensors and should output one logit.
- GAIL requires live environment collection plus an expert buffer. Route environment/vectorization mechanics to `../envs-and-vectorization/SKILL.md` and on-policy trainer details to `../procedural-training/SKILL.md`.

## Curiosity And Model-Based Components

- `ICMOffPolicyWrapper` and `ICMOnPolicyWrapper` wrap an already-created base algorithm and add intrinsic reward preprocessing around each batch.
- Use `IntrinsicCuriosityModule` with discrete action dimensions and an optimizer factory for the ICM model. Keep `reward_scale` small for first tests so intrinsic rewards do not dominate task rewards.
- The wrappers temporarily add curiosity reward during preprocessing and restore original rewards after the wrapped algorithm update; failures often come from missing `obs_next`, non-discrete actions, or action-dimension mismatch.
- `PSRL` is tabular and expects discrete state indices and discrete actions. Use it for small MDPs with priors shaped `(n_state, n_action, n_state)` for transitions and `(n_state, n_action)` for reward statistics.

## Multi-Agent Algorithms

1. Create one compatible Tianshou algorithm per PettingZoo agent.
2. Wrap the PettingZoo environment through the environment integration layer; do not duplicate PettingZoo wrapping here.
3. Pass the per-agent off-policy algorithms and wrapped environment into `MultiAgentOffPolicyAlgorithm`.
4. Use `MARLRandomDiscreteMaskedOffPolicyAlgorithm` as a safe random masked baseline when a legal-action mask exists at `batch.obs.mask`.
5. Ensure batches contain `obs.agent_id` so dispatch can split data by agent. If observations/actions/masks are malformed, route to `../envs-and-vectorization/SKILL.md` first.

## Evaluation Launchers And Rliable Outputs

- `SequentialExpLauncher` runs a list of experiments sequentially; use it for first validation and debugging.
- `JoblibExpLauncher` runs multiple experiments through joblib and forces the backend to `loky`. Use `JoblibConfig(n_jobs=1 or 2, verbose=...)` for bounded local tests before increasing parallelism.
- `ExpLauncher.launch(...)` avoids parallelism when exactly one experiment is supplied.
- `MultiRunExperimentResult.load_from_disk(...)` and `load_and_eval_experiment(...)` evaluate already-produced experiment logs with rliable and can save JSON/plots. Set `show_plots=False` in non-interactive runs.
- Benchmark orchestration is reference-only by default because it can start tmux sessions, many scripts, many tasks, and multi-seed jobs. If a benchmark-like request is required, first reduce to `max_scripts=1`, `max_tasks=1`, `num_experiments=1`, explicit low `max_epochs`/`epoch_num_steps`, and a small `max_concurrent_sessions`.

## Difficult Case Patterns

- Fixed-buffer CQL without D4RL: create or load a tiny local `ReplayBuffer`, validate schema/finite values/action-space compatibility, construct `SACPolicy` plus critics, and run an `OfflineTrainerParams` smoke with tiny counts.
- Multi-seed evaluation without benchmark explosion: create two or three persisted toy experiments, launch with `SequentialExpLauncher` first, then `JoblibExpLauncher(JoblibConfig(n_jobs=2))`, and run rliable evaluation on the persisted directory with plots disabled.
