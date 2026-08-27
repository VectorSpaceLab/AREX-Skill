# Offline and Specialized RL API Reference

This reference summarizes the Tianshou 2.0.1 public surfaces most often needed for offline RL, imitation learning, model-based/curiosity wrappers, multi-agent wrappers, and evaluation utilities.

## Import Map

| Capability | Preferred import | Notes |
| --- | --- | --- |
| Continuous offline RL | `from tianshou.algorithm import CQL, BCQ, TD3BC` | Requires compatible continuous policies/networks from procedural APIs. |
| Discrete offline RL | `from tianshou.algorithm import DiscreteBCQ, DiscreteCQL, DiscreteCRR` | `DiscreteBCQPolicy` and policy-specific classes live in deeper modules. |
| Behavior cloning | `from tianshou.algorithm.imitation.imitation_base import ImitationPolicy, OffPolicyImitationLearning, OfflineImitationLearning` | Choose off-policy vs offline by trainer/data source. |
| GAIL | `from tianshou.algorithm import GAIL` | PPO-derived; needs expert buffer and discriminator. |
| Curiosity wrappers | `from tianshou.algorithm import ICMOffPolicyWrapper, ICMOnPolicyWrapper` | Wrap existing base algorithms. |
| PSRL | `from tianshou.algorithm import PSRL`; `from tianshou.algorithm.modelbased.psrl import PSRLPolicy` | Tabular discrete states/actions only. |
| Multi-agent | `from tianshou.algorithm import MultiAgentOffPolicyAlgorithm, MARLRandomDiscreteMaskedOffPolicyAlgorithm` | PettingZoo wrapping belongs to env sub-skill. |
| Launchers | `from tianshou.evaluation.launcher import SequentialExpLauncher, JoblibExpLauncher, JoblibConfig` | Requires evaluation optional dependencies. |
| Rliable analysis | `from tianshou.evaluation.rliable_evaluation import MultiRunExperimentResult, load_and_eval_experiment` | Requires rliable/scipy/matplotlib stack. |

## Continuous Offline Algorithms

| Class | Constructor shape | Use when | Key dependencies |
| --- | --- | --- | --- |
| `BCQPolicy` | `BCQPolicy(actor_perturbation, action_space, critic, vae, forward_sampled_times=100, observation_space=None, action_scaling=False, action_bound_method="clip")` | Policy samples candidate actions from a VAE and perturbs/selects them by critic value. | `VAE`, perturbation actor, critic, continuous action space. |
| `BCQ` | `BCQ(policy, actor_perturbation_optim, critic_optim, vae_optim, critic2=None, critic2_optim=None, gamma=0.99, tau=0.005, lmbda=0.75, num_sampled_action=10)` | Batch-constrained continuous offline RL. | Fixed replay buffer with `obs`, `act`, `rew`, `done`, `obs_next`. |
| `CQL` | `CQL(policy, policy_optim, critic, critic_optim, critic2=None, critic2_optim=None, cql_alpha_lr=1e-4, cql_weight=1.0, tau=0.005, gamma=0.99, alpha=0.2, temperature=1.0, with_lagrange=True, lagrange_threshold=10.0, min_action=-1.0, max_action=1.0, num_repeat_actions=10, alpha_min=0.0, alpha_max=1e6, max_grad_norm=1.0, calibrated=True)` | Conservative Q-learning over continuous actions, usually with `SACPolicy`. | Correct action bounds and critics that accept `(obs, act)`. |
| `TD3BC` | `TD3BC(policy, policy_optim, critic, critic_optim, critic2=None, critic2_optim=None, tau=0.005, gamma=0.99, policy_noise=0.2, update_actor_freq=2, noise_clip=0.5, alpha=2.5, n_step_return_horizon=1)` | TD3 plus behavior-cloning loss for continuous offline data. | `ContinuousDeterministicPolicy`, twin critics, fixed buffer. |

## Discrete Offline Algorithms

| Class | Constructor shape | Use when | Key dependencies |
| --- | --- | --- | --- |
| `DiscreteBCQPolicy` | `DiscreteBCQPolicy(model, imitator, target_update_freq=8000, unlikely_action_threshold=0.3, action_space, observation_space=None, eps_inference=0.0)` | Masks unlikely discrete actions using imitation logits before Q argmax. | `target_update_freq > 0`; discrete action space. |
| `DiscreteBCQ` | `DiscreteBCQ(policy, optim, gamma=0.99, n_step_return_horizon=1, target_update_freq=8000, imitation_logits_penalty=1e-2)` | Discrete BCQ with target network and imitation regularization. | Replay buffer and Q/imitator model outputs aligned to action count. |
| `DiscreteCQL` | `DiscreteCQL(policy, optim, min_q_weight=10.0, gamma=0.99, num_quantiles=200, n_step_return_horizon=1, target_update_freq=0)` | QRDQN-based discrete CQL. | `QRDQNPolicy` and quantile model output shape. |
| `DiscreteCRR` | `DiscreteCRR(policy, critic, optim, gamma=0.99, policy_improvement_mode="exp", ratio_upper_bound=20.0, beta=1.0, min_q_weight=10.0, target_update_freq=0, return_standardization=False)` | Critic-regularized regression for discrete offline data. | `DiscreteActorPolicy`, `DiscreteCritic`, returns computation. |

## Imitation Learning

| Class | Constructor shape | Use when | Notes |
| --- | --- | --- | --- |
| `ImitationPolicy` | `ImitationPolicy(actor, action_space, observation_space=None, action_scaling=False, action_bound_method="clip")` | Shared policy wrapper for behavior cloning. | Discrete actors output action values/logits; continuous actors output regression actions. |
| `OffPolicyImitationLearning` | `OffPolicyImitationLearning(policy, optim)` | Behavior cloning inside off-policy collection/training workflows. | Uses MSE for continuous actions and NLL classification for discrete actions. |
| `OfflineImitationLearning` | `OfflineImitationLearning(policy, optim)` | Behavior cloning from a fixed offline buffer. | Use `OfflineTrainerParams` and route buffer work to `../data-collection/SKILL.md`. |
| `GAIL` | `GAIL(policy, critic, optim, expert_buffer, disc_net, disc_optim, disc_update_num=4, eps_clip=0.2, dual_clip=None, value_clip=False, advantage_normalization=True, recompute_advantage=False, vf_coef=0.5, ent_coef=0.01, max_grad_norm=None, gae_lambda=0.95, max_batchsize=256, gamma=0.99, return_scaling=False)` | Adversarial imitation with PPO-style policy updates. | Policy actor must expose a known vector output dimension; discriminator sees concatenated `obs` and `act`. |

## Model-Based And Curiosity

| Class | Constructor shape | Use when | Notes |
| --- | --- | --- | --- |
| `PSRLPolicy` | `PSRLPolicy(trans_count_prior, rew_mean_prior, rew_std_prior, action_space, discount_factor=0.99, epsilon=0.01, observation_space=None)` | Tabular posterior-sampling policy for small discrete MDPs. | Observations must be NumPy integer state indices. |
| `PSRL` | `PSRL(policy, add_done_loop=False)` | On-policy Bayesian tabular updates. | Ignores mini-batch/repeat semantics during update. |
| `ICMOffPolicyWrapper` | `ICMOffPolicyWrapper(wrapped_algorithm, model, optim, lr_scale, reward_scale, forward_loss_weight)` | Add intrinsic curiosity rewards to off-policy algorithms. | Requires `obs`, `act`, and `obs_next`; discrete action dimension for `IntrinsicCuriosityModule`. |
| `ICMOnPolicyWrapper` | `ICMOnPolicyWrapper(wrapped_algorithm, model, optim, lr_scale, reward_scale, forward_loss_weight)` | Add intrinsic curiosity rewards to on-policy algorithms. | Same ICM schema expectations as off-policy wrapper. |

## Multi-Agent Wrappers

| Class | Constructor shape | Use when | Notes |
| --- | --- | --- | --- |
| `MultiAgentPolicy` | `MultiAgentPolicy(policies)` | Dispatch policy calls by `obs.agent_id`. | Usually created by `MARLDispatcher`; requires batch observations with `agent_id`. |
| `MultiAgentOffPolicyAlgorithm` | `MultiAgentOffPolicyAlgorithm(algorithms, env)` | One off-policy algorithm per PettingZoo agent. | Environment must expose `agents` and `agent_idx`; wrapping mechanics belong to `../envs-and-vectorization/SKILL.md`. |
| `MultiAgentOnPolicyAlgorithm` | `MultiAgentOnPolicyAlgorithm(algorithms, env)` | One on-policy algorithm per PettingZoo agent. | Not exported from the top-level algorithm package in the same way as off-policy; import from `tianshou.algorithm.multiagent.marl` if needed. |
| `MARLRandomDiscreteMaskedOffPolicyAlgorithm` | `MARLRandomDiscreteMaskedOffPolicyAlgorithm(action_space)` | Random masked discrete baseline. | Expects legal-action mask at `batch.obs.mask`; invalid actions get `-inf`. |

## Evaluation And Benchmark Utilities

| Class/function | Constructor or call shape | Safe use |
| --- | --- | --- |
| `JoblibConfig` | `JoblibConfig(n_jobs=-1, backend="loky", verbose=10)` | Override `n_jobs` to `1` or `2` for bounded local checks; backend is forced to `loky` by `JoblibExpLauncher`. |
| `SequentialExpLauncher` | `SequentialExpLauncher(experiment_runner=default_experiment_execution)` | First launcher to use while debugging experiment lists. |
| `JoblibExpLauncher` | `JoblibExpLauncher(joblib_cfg=None, experiment_runner=default_experiment_execution)` | Parallel multi-experiment execution; do not use `n_jobs=-1` for first tests. |
| `ExpLauncher.launch` | `launch(experiments)` | Runs one experiment in-process when the sequence has length one. |
| `RegisteredExpLauncher` | `RegisteredExpLauncher.JOBLIB.create_launcher()` or `.SEQUENTIAL.create_launcher()` | Enum factory for configured launchers. |
| `MultiRunExperimentResult.load_from_disk` | `load_from_disk(exp_dir, exp_name=None, max_env_step=None)` | Load persisted run directories and trim to common evaluation lengths. |
| `MultiRunExperimentResult.eval_results` | `eval_results(algo_name=None, score_thresholds=None, save_as_json=True, save_plots=True, show_plots=True, scope=DataScope.TEST, ...)` | Use `show_plots=False` for non-interactive agents and consider `save_plots=False` for smoke checks. |
| `load_and_eval_experiment` | `load_and_eval_experiment(log_dir, show_plots=True, save_plots=True, save_as_json=True, scope=DataScope.TEST or "both", max_env_step=None)` | Convenience loader/evaluator for existing logs; does not create experiments. |

## Optional Dependency Boundaries

- Core algorithm imports require the normal Tianshou runtime stack, including NumPy, PyTorch, Gymnasium, and Tianshou's required dependencies.
- Evaluation helpers require optional packages such as `joblib`, `rliable`, `scipy`, and plotting/logging dependencies.
- D4RL and Atari examples require dataset/environment extras not required for the core package. Treat them as reference patterns unless the user explicitly installed and requested those extras.
- PettingZoo multi-agent examples require PettingZoo environments and correct wrapping; route environment-specific fixes to `../envs-and-vectorization/SKILL.md`.

## Cross-Skill Dependency Map

| Need | Use |
| --- | --- |
| Build policies, actors, critics, optimizer factories, collectors, and trainer parameter dataclasses | `../procedural-training/SKILL.md` |
| Create, load, validate, sample, or serialize replay buffers and batches | `../data-collection/SKILL.md` |
| Wrap Gymnasium/PettingZoo environments, vectorize envs, debug masks, or install env engines | `../envs-and-vectorization/SKILL.md` |
| Use high-level `Experiment`, persistence, and declarative algorithm builders | `../highlevel-experiments/SKILL.md` |
