# TensorFlow Agent Catalog

This catalog covers Acme TensorFlow/Sonnet agents and learner components. Use it to choose an algorithm family before adapting networks or launchers.

## Dependency And Runtime Facts

- Package distribution: `dm-acme` version 0.4.1; import package: `acme`.
- Core install imports are lightweight (`absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, `typing-extensions`) but do not include TensorFlow, Reverb, Launchpad, Sonnet, or TRFL.
- Real TF agent execution needs the TF extra stack: `tensorflow==2.8.0`, `tensorflow_probability==0.15.0`, `tensorflow_datasets==4.6.0`, `dm-reverb==0.7.2`, `dm-launchpad==0.5.2`, `dm-sonnet`, and `trfl`.
- Distributed examples are Launchpad programs. For local debugging prefer `--lp_launch_type=local_mt` first, then `local_mp`; GCP/Vertex launch types require external setup.

## Selection Matrix

| Task signal | Prefer | Entry points | Why |
| --- | --- | --- | --- |
| Continuous control, deterministic actor-critic | `acme.agents.tf.ddpg.DDPG` or `DistributedDDPG` | `DDPG(environment_spec, policy_network, critic_network, observation_network, ...)`; `DistributedDDPG(...).build(name='ddpg')` | Simpler deterministic policy gradient path than distributional variants. |
| Continuous control, distributional critic | `acme.agents.tf.d4pg.D4PG` or `DistributedD4PG` | `D4PG(environment_spec, policy_network, critic_network, observation_network, accelerator, ...)`; `DistributedD4PG(...).build(name='d4pg')` | Uses C51-style distributional critic head and optional accelerator replication. |
| Continuous control, stochastic policy with MPO loss | `acme.agents.tf.mpo.MPO` or `DistributedMPO` | `MPO(..., policy_loss_module, num_samples, ...)`; `DistributedMPO(..., policy_loss_factory, ...).build(name='mpo')` | Learns a stochastic policy with MPO KL constraints. |
| Continuous control, stochastic policy plus distributional critic | `acme.agents.tf.dmpo.DistributionalMPO` or `DistributedDistributionalMPO` | `DistributionalMPO(..., critic_network, policy_loss_module, ...)`; `DistributedDistributionalMPO(...).build(name='dmpo')` | MPO-style policy improvement with a distributional critic. |
| Continuous control, multi-objective rewards/critics | `acme.agents.tf.mompo.MultiObjectiveMPO` or `DistributedMultiObjectiveMPO` | Requires `reward_objectives`, `qvalue_objectives`, policy/critic networks, and MPO loss options | Adds per-objective policy-improvement constraints for multiple reward or Q-value objectives. |
| Continuous control with mixture-of-Gaussians critic | `acme.agents.tf.mog_mpo.DistributedMoGMPO` | `DistributedMoGMPO(..., policy_evaluation_config, ...).build(name='dmpo')` | Distributed-only MoG distributional MPO variant. |
| Discrete control baseline | `acme.agents.tf.dqn.DQN` or `DistributedDQN` | `DQN(environment_spec, network, ...)`; `DistributedDQN(environment_factory, network_factory, ...).build(name='dqn')` | Standard discrete-action Q-learning path. |
| Discrete recurrent replay | `acme.agents.tf.r2d2.R2D2` or `DistributedR2D2` | `R2D2(environment_spec, network, burn_in_length, trace_length, ...)`; `DistributedR2D2(...).build(name='r2d2')` | Use when observations need memory, LSTM state, burn-in, and sequence replay. |
| Discrete actor-learner architecture | `acme.agents.tf.impala.IMPALA` or `DistributedIMPALA` | `IMPALA(environment_spec, network, sequence_length, sequence_period, ...)`; `DistributedIMPALA(...).build(name='impala')` | Throughput-oriented actor/learner architecture using recurrent policy/value networks. |
| Model-based planning | `acme.agents.tf.mcts.MCTS` or `DistributedMCTS` | `MCTS(network, model, optimizer, num_simulations, ...)`; `DistributedMCTS(environment_factory, network_factory, model_factory, ...).build(name='MCTS')` | Monte-Carlo tree search with a simulator or learned model. |
| Learning from demonstrations, discrete | `acme.agents.tf.dqfd.DQfD` or `acme.agents.tf.r2d3.R2D3` | `DQfD(..., demonstration_dataset, demonstration_ratio, ...)`; `R2D3(..., demonstration_dataset, demonstration_ratio, ...)` | Adds demonstration data to DQN/R2D2-style learning. |
| Offline behavior cloning | `acme.agents.tf.bc.learning.BCLearner` | `BCLearner(network, learning_rate, dataset, counter, logger, checkpoint)` | Learner-only supervised imitation from dataset batches. |
| Offline discrete BCQ | `acme.agents.tf.bcq.discrete_learning.DiscreteBCQLearner` | `DiscreteBCQLearner(network, dataset, learning_rate, counter, bc_logger, bcq_logger, **bcq_learner_kwargs)` | Learner-only offline Q-learning constrained by behavior cloning. |
| Quantile/distributional discrete learner | `acme.agents.tf.iqn.learning.IQNLearner` | `IQNLearner(network, target_network, discount, importance_sampling_exponent, learning_rate, target_update_period, dataset, ...)` | Implicit Quantile Network learner component. |
| Recurrent CRR learner | `acme.agents.tf.crr.recurrent_learning.RCRRLearner` | `RCRRLearner(policy_network, critic_network, target_policy_network, target_critic_network, dataset, ...)` | Recurrent offline CRR learner component; route data details to `replay-and-data`. |

## Control Suite Distributed Families

Use these when the user specifically asks for Launchpad Control Suite examples:

| Desired run | Candidate family | Network factory shape |
| --- | --- | --- |
| D4PG Control Suite | `DistributedD4PG` | Return `D4PGNetworks(policy_network, critic_network, observation_network)` or the same structure produced by `d4pg.make_default_networks(action_spec)` patterns. |
| DDPG Control Suite | `DistributedDDPG` | Return policy/critic/observation Sonnet modules for deterministic actor-critic. |
| MPO Control Suite | `DistributedMPO` | Return stochastic policy, critic, and observation modules. |
| DMPO Control Suite | `DistributedDistributionalMPO` | Return stochastic policy, distributional critic, and observation modules; pixels variants add visual torso/augmentation. |
| SVG0 with prior | `DistributedSVG0` | Return `SVG0Networks(policy_network, critic_network, prior_network)`. |

Keep factories pure: `environment_factory(evaluation: bool = False)` constructs an environment; `network_factory(action_spec)` or `network_factory(environment_spec)` constructs new Sonnet modules; the launcher only builds and launches the Launchpad program.

## Bsuite And OpenSpiel Families

- Bsuite DQN: use `acme.agents.tf.dqn.DQN` with a discrete Q-network, typically a small Sonnet `snt.Sequential` ending in `snt.Linear(num_actions)`.
- Bsuite IMPALA: use `acme.agents.tf.impala.IMPALA` with a recurrent `snt.RNNCore` that outputs policy logits and values.
- Bsuite MCTS: use `acme.agents.tf.mcts.MCTS` with a model and policy/value network.
- OpenSpiel DQN: use `acme.agents.tf.dqn.DQN` plus legal-action-aware networks from `acme.tf.networks.legal_actions`; see [network-and-saver-workflows.md](network-and-saver-workflows.md#openspiel-and-legal-actions).

## Offline TF Families

- Behavior cloning uses `BCLearner` or the higher-level offline example pattern: make a policy network, convert episodes to transitions, batch a `tf.data.Dataset`, and train learner-only.
- BCQ uses a discrete Q-network and a dataset with replay-style transition fields; the public learner wraps an internal behavior-cloning learner and a BCQ learner.
- DQfD/R2D3 mix online replay with demonstration datasets; route replay table sizing, priority, and dataset construction to `replay-and-data`.

## Choosing Single-Process vs Distributed

- Prefer single-process classes (`DQN`, `D4PG`, `MPO`, `DistributionalMPO`, `R2D2`, `IMPALA`, `MCTS`) for tests, examples, notebook-like experimentation, or shape debugging.
- Prefer distributed classes when the user needs many actors, separate learner/evaluator nodes, or Launchpad deployment.
- Distributed constructors almost always take `environment_factory`, `network_factory`, actor counts, replay sizing, batch/prefetch settings, variable update period, and optional max actor steps. Their `build(name=...)` returns a Launchpad program.
- Do not recommend distributed runs unless Reverb and Launchpad are installed and the user can handle local multiprocessing or external cluster setup.

## Common Cross-Routes

- If the candidate is JAX-only in the Acme table (TD3, SAC, PPO, CQL, BVE, MBOP, many imitation baselines), route to `jax-agents` instead of inventing a TF implementation.
- If the user is choosing adders, table signatures, dataset iterators, or demonstration data formats, read this catalog for the agent family but route implementation details to `replay-and-data`.
- If the user is wiring environment loops, wrappers, observers, loggers, or counters, route the generic loop pieces to `core-workflows`.
