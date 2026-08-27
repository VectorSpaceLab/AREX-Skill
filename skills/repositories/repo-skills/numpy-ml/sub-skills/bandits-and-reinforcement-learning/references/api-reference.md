# API Reference

## Bandits

- `BernoulliBandit(payoff_probs)`
- `MultinomialBandit(payoffs, payoff_probs)`
- `GaussianBandit(payoff_dists, payoff_probs)`
- `ContextualBernoulliBandit(...)`
- `ContextualLinearBandit(K, D, payoff_variance=1)`

Common methods include pulling an arm, reporting oracle payoff, and resetting
state. Validate payoff probabilities before constructing the bandit.

## Policies

- `EpsilonGreedy(epsilon=0.05, ev_prior=0.5)`
- `UCB1(C=1, ev_prior=0.5)`
- `ThompsonSamplingBetaBinomial(alpha=1, beta=1)`
- `LinUCB(alpha=1)`

`policy.act(bandit, context=None)` initializes policy state if needed, selects
an arm, samples reward, updates estimates, and returns `(reward, arm_id)`.

## Trainers

- `BanditTrainer()` supports repeated comparisons and plotting when optional
  plotting dependencies are installed.
- Use `plot=False` for safe, headless smoke checks.

## RL utilities and agents

- `EnvModel()` stores tabular transition/reward counts.
- `tile_state_space(env, env_stats, n_tilings, obs_max=None, obs_min=None, state_action=False, grid_size=(4, 4))` creates tile encodings for continuous observations.
- `CrossEntropyAgent(env, n_samples_per_episode=500, retain_prcnt=0.2)`
- `MonteCarloAgent(env, off_policy=False, temporal_discount=0.9, epsilon=0.1)`
- `TemporalDifferenceAgent(env, lr=0.4, epsilon=0.1, n_tilings=8, obs_max=None, obs_min=None, grid_dims=[8, 8], off_policy=False, temporal_discount=0.99)`
- `DynaAgent(env, lr=0.4, epsilon=0.1, n_tilings=8, obs_max=None, obs_min=None, q_plus=False, grid_dims=[8, 8], explore_weight=0.05, temporal_discount=0.9, n_simulated_actions=50)`

RL agent constructors expect Gym-like environments. Gym is optional for the
package as a whole but required for real environment training.
