# Optional BOHB tuning

Tensorforce ships a repository-level tuning workflow based on BOHB/Hyperband. Treat it as an optional extension to the runner workflow, not part of the minimum runtime path.

## When to use

Use BOHB tuning when you want to explore a small hyperparameter space for a Tensorforce agent while keeping the same environment and episode budget structure used by the runner workflow.

Do not use this path for quick smoke checks or default verification. It introduces extra dependencies (`ConfigSpace`, `hpbandster`) and longer optimization loops.

## Required concepts

- `episodes`: number of episodes per training run.
- `num_parallel`: optional parallel environments used by the worker.
- `runs_per_round`: a tuple such as `1,2,5,10` describing how many independent runs are performed at each optimization round.
- `selection_factor`: the BOHB/Hyperband downsampling factor.
- `num_iterations`: number of optimization iterations.
- `directory`: output directory for logs and results.
- `restore`: optional previous tuning output directory.
- `id`: worker/optimizer run id.

## Tuning flow

1. Build a Tensorforce agent spec from the sampled hyperparameters.
2. Create a `Runner` with the chosen environment and episode budget.
3. Run the training loop for each sampled configuration.
4. Aggregate the mean reward metrics into a scalar loss.
5. Let BOHB/Hyperband advance the better configurations.

The historical worker computes a loss from the negative mean of the average and final episode rewards:

```python
loss = -(mean_average_reward + mean_final_reward)
```

## Search-space fields used by the historical worker

- `batch_size`
- `learning_rate`
- `multi_step`
- `horizon`
- `discount`
- `importance_sampling`
- `clipping_value`
- `baseline`
- `baseline_weight`
- `estimate_advantage`
- `entropy_regularization`

The worker maps those values into Tensorforce agent configuration blocks such as `update`, `policy`, `optimizer`, `objective`, `reward_estimation`, `baseline`, and `baseline_optimizer`.

## Runner/parallel notes

- If `num_parallel` is set, the tuning worker uses a multiprocessing runner when supported.
- Batched agent calls are useful when the environment is faster than the policy network and the tuning objective benefits from higher throughput.
- Keep `use_tqdm=False` in tuning workers.

## Dependency caution

Tuning is optional. If the environment does not have `ConfigSpace` and `hpbandster`, do not block the runner workflow on them. Instead, fall back to ordinary `Runner` sweeps or document the missing extra.
