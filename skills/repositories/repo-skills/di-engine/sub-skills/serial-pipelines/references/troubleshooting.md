# Serial pipeline troubleshooting

## `load_path` is missing or wrong

- `eval` and some serial flows expect a checkpoint path in the config or as a
  function argument.
- Make sure the path points to the checkpoint produced by the matching config
  and seed.

## Expert-data or config mismatch

- GAIL, SQIL, DQFD, and TREX flows often need the expert config that produced
  the expert model or dataset.
- Re-check the config naming convention before assuming the pipeline is broken.

## The loop never stops

- Confirm the config's `stop_value`, `max_train_iter`, and `max_env_step` are
  realistic for the selected environment.
- Check that the evaluator is actually running and that the env count is not
  zero.

## Random collect or offline-data issues

- `random_collect_size` may be larger than the actual replay capacity or the
  collector settings.
- Make sure `n_sample`/`n_episode` and the collector type agree with the replay
  buffer type.
- If the collected data needs post-processing, confirm whether the recipe
  expects transition-level or episodic data.

## Reward-model or imitation failures

- The serial special-mode helpers often assume extra data files, a specific
  expert config, or a policy checkpoint that can be loaded in eval mode.
- Route to `env-integration` if the failure is actually caused by the env
  wrapper or observation/action shape.

## Smoke-test strategy

- Use the bundled config smoke only to validate the config and launch surface.
- Save full training runs for the native verification phase or for a user who
  explicitly wants to execute the recipe.
