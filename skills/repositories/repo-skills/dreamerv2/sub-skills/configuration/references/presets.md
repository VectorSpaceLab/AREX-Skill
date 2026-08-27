# Presets and high-impact values

Source of truth: the package `dreamerv2/configs.yaml` at the inspected
DreamerV2 snapshot. The built-in runner loads this file, parses `--configs`
with a temporary config whose only key is `configs`, then applies each selected
preset to a `Config` initialized from `defaults`.

## Composition contract

The effective configuration is constructed as follows:

```text
effective = Config(configs['defaults'])
for name in parsed_configs:
    effective = effective.update(configs[name])
effective = Flags(effective).parse(remaining_config_flags)
```

The temporary `--configs` parser has a default value of `['defaults']`. Thus,
when no `--configs` is supplied, `defaults` is applied once. With
`--configs atari debug`, the order is `defaults → atari → debug`, and then
ordinary flags override both presets. With `--configs debug atari`, the later
`atari` values win wherever both presets set the same key. An unknown preset is
not silently ignored: the later `configs[name]` lookup raises `KeyError`.

`--configs` is not an ordinary key in the final configuration. It is consumed
by the first parser. Use it with the module runner, for example:

```sh
python -m dreamerv2.train \
  --logdir /tmp/dv2-atari-debug \
  --configs atari debug \
  --task atari_pong \
  --precision 32
```

The installed `dreamerv2` console wrapper is not the reliable route for this
snapshot because `train.py` resolves `configs.yaml` relative to `sys.argv[0]`.
Use `python -m dreamerv2.train` as above. A writable `--logdir` is required;
`defaults.logdir` is `/dev/null` and is a placeholder, not a useful training
output directory.

For Python composition, `dreamerv2.api.defaults` is the defaults config and
the API module's loaded named mapping contains the presets. Apply the same
ordered `Config.update()` calls, then call `parse_flags()` only with ordinary
configuration keys. Do not pass `--configs` to `defaults.parse_flags()`; it is
not present there.

## Defaults

Every named preset inherits all values not shown in its own block. The tables
below list the complete default block, grouped as it appears in the YAML.
Values written with scientific notation are YAML numeric values; preserve the
actual loaded type when relying on flag conversion.

### Train-script defaults

| Key | Default | Meaning at this route |
|---|---:|---|
| `logdir` | `/dev/null` | output location placeholder; override it |
| `seed` | `0` | random seed setting |
| `task` | `dmc_walker_walk` | `suite_task` selection; environment route owns schemas |
| `envs` | `1` | number of environment workers |
| `envs_parallel` | `none` | serial/parallel mode selector |
| `render_size` | `[64, 64]` | image render size; loaded as tuple |
| `dmc_camera` | `-1` | DMC camera setting |
| `atari_grayscale` | `True` | Atari grayscale setting |
| `time_limit` | `0` | episode time limit |
| `action_repeat` | `1` | environment action repeat |
| `steps` | `1e8` | training step target |
| `log_every` | `1e4` | logging interval |
| `eval_every` | `1e5` | evaluation interval |
| `eval_eps` | `1` | evaluation episode count |
| `prefill` | `10000` | replay prefill steps |
| `pretrain` | `1` | pretraining updates |
| `train_every` | `5` | environment-step update cadence |
| `train_steps` | `1` | updates per training trigger |
| `expl_until` | `0` | exploration duration |
| `replay.capacity` | `2e6` | replay capacity |
| `replay.ongoing` | `False` | keep ongoing episodes setting |
| `replay.minlen` | `50` | minimum sampled episode length |
| `replay.maxlen` | `50` | maximum sampled episode length |
| `replay.prioritize_ends` | `True` | end-prioritization setting |
| `dataset.batch` | `16` | sequence batch size |
| `dataset.length` | `50` | sequence length |
| `log_keys_video` | `['image']` | keys logged as video |
| `log_keys_sum` | `'^$'` | sum-metric key regex |
| `log_keys_mean` | `'^$'` | mean-metric key regex |
| `log_keys_max` | `'^$'` | max-metric key regex |
| `precision` | `16` | runner accepts only 16 or 32 |
| `jit` | `True` | keep TensorFlow functions compiled when true |

### Agent and model defaults

| Group | Keys and defaults |
|---|---|
| Agent | `clip_rewards: tanh`; `expl_behavior: greedy`; `expl_noise: 0.0`; `eval_noise: 0.0`; `eval_state_mean: False` |
| World model | `grad_heads: [decoder, reward, discount]`; `pred_discount: True`; `rssm: {ensemble: 1, hidden: 1024, deter: 1024, stoch: 32, discrete: 32, act: elu, norm: none, std_act: sigmoid2, min_std: 0.1}` |
| Encoder | `encoder: {mlp_keys: '.*', cnn_keys: '.*', act: elu, norm: none, cnn_depth: 48, cnn_kernels: [4, 4, 4, 4], mlp_layers: [400, 400, 400, 400]}` |
| Decoder | `decoder: {mlp_keys: '.*', cnn_keys: '.*', act: elu, norm: none, cnn_depth: 48, cnn_kernels: [5, 5, 6, 6], mlp_layers: [400, 400, 400, 400]}` |
| Heads | `reward_head: {layers: 4, units: 400, act: elu, norm: none, dist: mse}`; `discount_head: {layers: 4, units: 400, act: elu, norm: none, dist: binary}` |
| Loss/optimizer | `loss_scales: {kl: 1.0, reward: 1.0, discount: 1.0, proprio: 1.0}`; `kl: {free: 0.0, forward: False, balance: 0.8, free_avg: True}`; `model_opt: {opt: adam, lr: 1e-4, eps: 1e-5, clip: 100, wd: 1e-6}` |
| Actor/critic | `actor: {layers: 4, units: 400, act: elu, norm: none, dist: auto, min_std: 0.1}`; `critic: {layers: 4, units: 400, act: elu, norm: none, dist: mse}` |
| Actor/critic optimizers | `actor_opt: {opt: adam, lr: 8e-5, eps: 1e-5, clip: 100, wd: 1e-6}`; `critic_opt: {opt: adam, lr: 2e-4, eps: 1e-5, clip: 100, wd: 1e-6}` |
| Actor/critic values | `discount: 0.99`; `discount_lambda: 0.95`; `imag_horizon: 15`; `actor_grad: auto`; `actor_grad_mix: 0.1`; `actor_ent: 2e-3`; `slow_target: True`; `slow_target_update: 100`; `slow_target_fraction: 1`; `slow_baseline: True`; `reward_norm: {momentum: 1.0, scale: 1.0, eps: 1e-8}` |
| Exploration | `expl_intr_scale: 1.0`; `expl_extr_scale: 0.0`; `expl_opt: {opt: adam, lr: 3e-4, eps: 1e-5, clip: 100, wd: 1e-6}`; `expl_head: {layers: 4, units: 400, act: elu, norm: none, dist: mse}` |
| Disagreement | `disag_target: stoch`; `disag_log: False`; `disag_models: 10`; `disag_offset: 1`; `disag_action_cond: True`; `expl_model_loss: kl` |
| Exploration normalization | `expl_reward_norm: {momentum: 1.0, scale: 1.0, eps: 1e-8}` |

Nested YAML lists become tuples in `Config`; for example `render_size`,
`grad_heads`, `cnn_kernels`, and `mlp_layers` are tuples after construction.
The final type matters for later flags.

## Named preset deltas

Each row is applied on top of the values above and on top of any earlier
preset. A nested mapping updates only the listed leaves; it does not replace
unmentioned sibling leaves.

### `atari`

| Key | Value |
|---|---|
| `task` | `atari_pong` |
| `encoder.mlp_keys`, `decoder.mlp_keys` | `'$^'` |
| `encoder.cnn_keys`, `decoder.cnn_keys` | `image` |
| `time_limit` | `27000` |
| `action_repeat` | `4` |
| `steps` | `5e7` |
| `eval_every` | `2.5e5` |
| `log_every` | `1e4` |
| `prefill` | `50000` |
| `train_every` | `16` |
| `clip_rewards` | `tanh` |
| `rssm.hidden`, `rssm.deter` | `600` |
| `model_opt.lr` | `2e-4` |
| `actor_opt.lr` | `4e-5` |
| `critic_opt.lr` | `1e-4` |
| `actor_ent` | `1e-3` |
| `discount` | `0.999` |
| `loss_scales.kl` | `0.1` |
| `loss_scales.discount` | `5.0` |

### `crafter`

| Key | Value |
|---|---|
| `task` | `crafter_reward` |
| `encoder.mlp_keys`, `decoder.mlp_keys` | `'$^'` |
| `encoder.cnn_keys`, `decoder.cnn_keys` | `image` |
| `log_keys_max` | `'^log_achievement_.*'` |
| `log_keys_sum` | `'^log_reward$'` |
| `rssm.hidden`, `rssm.deter` | `1024` |
| `discount` | `0.999` |
| `model_opt.lr`, `actor_opt.lr`, `critic_opt.lr` | `1e-4` |
| `actor_ent` | `3e-3` |
| `.*\.norm` | `layer` for every currently existing flat key matching the regex |

The final regex row changes `rssm.norm`, `encoder.norm`, `decoder.norm`,
`reward_head.norm`, `discount_head.norm`, `actor.norm`, `critic.norm`, and
`expl_head.norm` from `none` to `layer`. It does not create future keys and it
does not change unrelated optimizer or normalization subkeys.

### `dmc_vision`

| Key | Value |
|---|---|
| `task` | `dmc_walker_walk` |
| `encoder.mlp_keys`, `decoder.mlp_keys` | `'$^'` |
| `encoder.cnn_keys`, `decoder.cnn_keys` | `image` |
| `action_repeat` | `2` |
| `eval_every` | `1e4` |
| `prefill` | `1000` |
| `pretrain` | `100` |
| `clip_rewards` | `identity` |
| `pred_discount` | `False` |
| `replay.prioritize_ends` | `False` |
| `grad_heads` | `[decoder, reward]` |
| `rssm.hidden`, `rssm.deter` | `200` |
| `model_opt.lr` | `3e-4` |
| `actor_opt.lr`, `critic_opt.lr` | `8e-5` |
| `actor_ent` | `1e-4` |
| `kl.free` | `1.0` |

### `dmc_proprio`

`dmc_proprio` has the same training, replay, optimization, and RSSM deltas as
`dmc_vision`, except its modality keys are `encoder.mlp_keys: '.*'`,
`encoder.cnn_keys: '$^'`, `decoder.mlp_keys: '.*'`, and
`decoder.cnn_keys: '$^'`. It therefore selects proprioceptive rather than image
features. The full shared delta is: `task: dmc_walker_walk`,
`action_repeat: 2`, `eval_every: 1e4`, `prefill: 1000`, `pretrain: 100`,
`clip_rewards: identity`, `pred_discount: False`,
`replay.prioritize_ends: False`, `grad_heads: [decoder, reward]`,
`rssm.hidden: 200`, `rssm.deter: 200`, `model_opt.lr: 3e-4`,
`actor_opt.lr: 8e-5`, `critic_opt.lr: 8e-5`, `actor_ent: 1e-4`, and `kl.free: 1.0`.

### `debug`

`debug` is a small override preset, not a CPU mode:

| Key | Value |
|---|---:|
| `jit` | `False` |
| `time_limit` | `100` |
| `eval_every` | `300` |
| `log_every` | `300` |
| `prefill` | `100` |
| `pretrain` | `1` |
| `train_steps` | `1` |
| `replay.minlen`, `replay.maxlen` | `10`, `30` |
| `dataset.batch`, `dataset.length` | `10`, `10` |

It leaves `precision` unchanged at `16`, leaves replay capacity and other replay
siblings unchanged, and does not choose a task or environment suite. Put it
last when it is meant to shorten a preceding `atari`, DMC, or Crafter preset.

## High-impact combinations

- `atari debug` keeps Atari image-only encoders, repeat/time horizon, Atari
  optimizer/model changes, and task, then applies the short debug cadence and
  eager execution. Override `task` after the presets if a different Atari game
  is intended.
- `dmc_vision` and `dmc_proprio` differ materially in encoder/decoder key
  filters. Choosing the wrong one can make the model expect keys the selected
  environment does not emit; route environment contract questions to
  `environments`.
- `crafter debug` keeps Crafter's metric regexes and normalization pattern,
  then applies debug cadence. `debug crafter` instead lets Crafter restore its
  own overlapping values, including `jit` remaining `False` only if Crafter
  does not set it (it does not), while Crafter's later values win for its own
  leaves.
- Preset composition is shallow only at the leaf level because `Config` first
  flattens nested mappings. Updating `replay.minlen` preserves
  `replay.capacity`, `ongoing`, `maxlen`, and `prioritize_ends`.
