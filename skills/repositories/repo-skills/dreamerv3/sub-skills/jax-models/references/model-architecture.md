# DreamerV3 JAX Model Architecture

This reference distills the DreamerV3 3.3.1 neural/JAX implementation into a self-contained operating guide. It does not require access to the source checkout.

## High-Level Object Graph

`dreamerv3.agent.Agent(obs_space, act_space, config)` builds the world model, actor, critic, slow critic, normalizers, and optimizer. Because it subclasses `embodied.jax.Agent`, construction returns the JAX wrapper object; the inner Dreamer model is available as `agent.model`.

Main submodules inside the inner model:

| Attribute | Implementation | Purpose |
|---|---|---|
| `enc` | `dreamerv3.rssm.Encoder` | Encodes non-lifecycle observations into tokens. |
| `dyn` | `dreamerv3.rssm.RSSM` | Recurrent state-space model over actions and tokens. |
| `dec` | `dreamerv3.rssm.Decoder` | Reconstructs observations from RSSM features. |
| `rew` | `embodied.jax.MLPHead` | Reward predictor, scalar output. |
| `con` | `embodied.jax.MLPHead` | Continuation predictor, binary output for not-terminal. |
| `pol` | `embodied.jax.MLPHead` | Action policy over the environment action spaces. |
| `val` | `embodied.jax.MLPHead` | Value predictor. |
| `slowval` | `embodied.jax.SlowModel` | Exponential moving target copy of `val`. |
| `retnorm`, `valnorm`, `advnorm` | `embodied.jax.Normalize` | Return, value, and advantage scaling. |
| `opt` | `embodied.jax.Optimizer` | Ninjax-aware optimizer over model modules. |

Observation keys `is_first`, `is_last`, `is_terminal`, and `reward` are excluded from encoder and decoder reconstruction spaces. Action spaces are used both by the RSSM transition and the policy head.

## Config Defaults That Matter For Models

DreamerV3 has class-level fallback defaults and config-level defaults. In normal training, `configs.yaml` `defaults.agent.*` overrides the class-level values. Prefer inspecting the final config with `scripts/inspect_model_config.py` when debugging a specific run.

### Default agent dimensions

| Component | Key | Default value |
|---|---|---:|
| RSSM deterministic state | `agent.dyn.rssm.deter` | `8192` |
| RSSM hidden units | `agent.dyn.rssm.hidden` | `1024` |
| RSSM stochastic variables | `agent.dyn.rssm.stoch` | `32` |
| RSSM categorical classes | `agent.dyn.rssm.classes` | `64` |
| RSSM grouped blocks | `agent.dyn.rssm.blocks` | `8` |
| RSSM observation layers | `agent.dyn.rssm.obslayers` | `1` |
| RSSM imagination/prior layers | `agent.dyn.rssm.imglayers` | `2` |
| RSSM dynamic hidden layers | `agent.dyn.rssm.dynlayers` | `1` |
| Encoder depth multiplier base | `agent.enc.simple.depth` | `64` |
| Encoder/decoder MLP units | `agent.enc.simple.units`, `agent.dec.simple.units` | `1024` |
| Encoder/decoder layers | `agent.enc.simple.layers`, `agent.dec.simple.layers` | `3` |
| Decoder block-space groups | `agent.dec.simple.bspace` | `8` |
| Reward/value bins | `agent.rewhead.bins`, `agent.value.bins` | `255` |
| Policy hidden layers/units | `agent.policy.layers`, `agent.policy.units` | `3`, `1024` |

The feature tensor fed to reward, continuation, policy, and value heads is:

```text
concat(feat['deter'], flatten(feat['stoch']))
feature_dim = deter + stoch * classes
```

With default dimensions, this is `8192 + 32 * 64 = 10240` features per batch/time element.

### Size presets

The built-in size presets are regex-style config patches. They change many parameter shapes and therefore are not checkpoint-compatible with each other unless only a compatible subset is loaded.

| Preset | RSSM patch | Global depth patch | Global units patch |
|---|---|---|---|
| `size1m` | `deter=512`, `hidden=64`, `classes=4` | `depth=4` | `units=64` |
| `size12m` | `deter=2048`, `hidden=256`, `classes=16` | `depth=16` | `units=256` |
| `size25m` | `deter=3072`, `hidden=384`, `classes=24` | `depth=24` | `units=384` |
| `size50m` | `deter=4096`, `hidden=512`, `classes=32` | `depth=32` | `units=512` |
| `size100m` | `deter=6144`, `hidden=768`, `classes=48` | `depth=48` | `units=768` |
| `size200m` | `deter=8192`, `hidden=1024`, `classes=64` | `depth=64` | `units=1024` |
| `size400m` | `deter=12288`, `hidden=1536`, `classes=96` | `depth=96` | `units=1536` |

`debug` is a much smaller debug patch: it sets CPU-oriented JAX flags, small batch/sequence lengths, `bins=5`, `layers=1`, `units=8`, `stoch=2`, `classes=4`, `deter=8`, `hidden=3`, `blocks=4`, and `depth=2` under `agent.*`.

## Agent Flow

### Construction

1. The wrapped `embodied.jax.Agent.__new__` splits `config.jax` into wrapper options and `internal.setup()` arguments.
2. `internal.setup()` sets JAX platform/JIT/debug/preallocation/mock-device flags and sets `embodied.jax.nets.COMPUTE_DTYPE`.
3. The inner Dreamer model is instantiated and then wrapped by `embodied.jax.Agent`.
4. The wrapper initializes Ninjax parameters through `transform.init()` and compiles train/report functions when `jax.precompile` is enabled.

Important wrapper-side policy parameter filter:

```text
policy_keys = '^(enc|dyn|dec|pol)/'
```

Only matching parameters are copied to the policy device mesh for asynchronous policy inference. Reward, continuation, value, slow value, normalizers, and optimizer state are train-side parameters/state.

### Carry contracts

`dreamerv3.agent.Agent.init_policy(batch_size)` returns:

```text
(enc_carry, dyn_carry, dec_carry, prevact)
```

- `enc_carry`: `{}` for the simple encoder.
- `dyn_carry`: RSSM state dict with `deter` and `stoch`.
- `dec_carry`: `{}` for the simple decoder.
- `prevact`: zero action tree matching `act_space`.

`init_train()` and `init_report()` use the same carry contract. Internally, `train()` removes `prevact` from the carry while computing loss and appends the last action after the update.

### Policy call

`policy(carry, obs, mode='train')`:

1. Reads `obs['is_first']` as reset mask.
2. Encodes the current observation with `single=True`.
3. Updates RSSM state with previous action and current token.
4. Optionally decodes if decoder carry is non-empty.
5. Applies the policy head to `feat2tensor(feat)` with one batch dimension.
6. Samples actions from output distributions.
7. Returns finite diagnostics for observations, carry, tokens, features, and actions.

The outer wrapper asserts exact observation keys, finite observations, finite policy diagnostics, non-negative discrete actions, and finite continuous actions.

### Training call

`train(carry, data)`:

1. `_apply_replay_context()` builds `obs`, previous actions, and optionally replaces the prefix carry from replay context entries.
2. `opt(loss, carry, obs, prevact, training=True, has_aux=True)` computes gradients and updates Ninjax state.
3. `slowval.update()` updates the target value model.
4. Replay-context entries can be returned under `outs['replay']` when `config.replay_context` is enabled.
5. The returned carry appends the final action from the sequence.

`data` must contain the wrapper `spaces`: observations, actions, `consec`, `stepid`, and any replay-context entries. The wrapper `stream()` inserts `seed` before `train()`.

### Report call

`report(carry, data)` returns metrics only when `config.report` is true. It can compute train metrics, optional per-loss grad norms, and open-loop image predictions for decoder image keys. Open-loop videos are logged under `openloop/<obs_key>`.

## RSSM Details

`RSSM(act_space, **kw)` is a Ninjax module with:

```text
entry_space = {
  'deter': float32[deter],
  'stoch': float32[stoch, classes],
}
```

### State and feature shapes

For batch `B`, time `T`, stochastic variables `S=stoch`, classes `C=classes`, deterministic size `D=deter`:

| Method | Main input shape | Main output shape |
|---|---|---|
| `initial(B)` | `B` | `{'deter': [B,D], 'stoch': [B,S,C]}` |
| `observe(..., single=True)` | tokens `[B,*]`, action tree `[B,*]`, reset `[B]` | carry/entry `[B]`, feat with `logit [B,S,C]` |
| `observe(..., single=False)` | tokens `[B,T,*]`, action tree `[B,T,*]`, reset `[B,T]` | entries/features `[B,T,*]` |
| `imagine(..., single=True)` | carry `[B,*]`, policy or action `[B,*]` | next carry and `(feat, action)` |
| `imagine(..., single=False)` | carry `[B,*]`, length `H` or action sequence | features/actions `[B,H,*]` |
| `starts(entries, carry, nlast)` | entries `[B,T,*]` | flattened starts `[B*nlast,*]` |

### Transition core

The RSSM transition:

1. Masks previous deterministic state, stochastic state, and action on reset.
2. Flattens and normalizes actions by `max(1, abs(action))`.
3. Builds separate linear-normalized embeddings for deterministic state, stochastic state, and action.
4. Splits the deterministic state into `blocks` groups and applies grouped `BlockLinear` layers.
5. Uses GRU-style reset/candidate/update gates to produce the next deterministic state.
6. Predicts prior logits with `imglayers` MLP layers.

Invariants:

- `deter % blocks == 0`.
- Decoder also asserts `feat['deter'].shape[-1] % bspace == 0`.
- RSSM stochastic samples are straight-through one-hot vectors from `outs.OneHot` with optional `unimix`.

### RSSM loss

`RSSM.loss(carry, tokens, acts, reset, training)` returns:

```text
carry, entries, losses, feat, metrics
```

Losses:

- `dyn`: KL from posterior (stopped) to prior.
- `rep`: KL from posterior to prior (stopped).
- Both are clamped by `free_nats` when non-zero.

Metrics:

- `dyn_ent`: prior entropy mean.
- `rep_ent`: posterior entropy mean.

## Encoder Details

`Encoder(obs_space, **kw)` separates observations:

- Vector keys: spaces with rank `<= 2`.
- Image keys: spaces with rank `== 3` and `uint8` dtype.

Vector path:

1. `DictConcat` sorts keys, masks unavailable values, one-hots discrete values, applies `symlog` to continuous values when enabled, and concatenates flat features.
2. A stack of `layers` linear + norm + activation blocks produces vector tokens.

Image path:

1. Sorted image keys are concatenated on channels.
2. Input must be `uint8`; values are cast to compute dtype, scaled to `[0,1]`, then shifted by `-0.5`.
3. Convolution depths are `depth * mult` for each `mult` in `mults`.
4. Downsampling uses either stride-2 convolutions or conv + 2x2 max-pooling.
5. Final spatial size must be between `3` and `16` in height and width.
6. The image feature is flattened and concatenated with vector features.

The returned `tokens` shape preserves batch dimensions: `[B, token_dim]` for single policy calls and `[B,T,token_dim]` for train/report.

## Decoder Details

`Decoder(obs_space, **kw)` reconstructs vector and image observation keys from RSSM features.

Vector path:

- Input is concatenated `stoch` and `deter` features.
- A shared MLP feeds `DictHead` outputs.
- Discrete spaces use `categorical` outputs.
- Continuous spaces use `symlog_mse` when `symlog=True`, else `mse`.

Image path:

- Computes minimum spatial resolution from original image resolution and upsampling factor.
- Uses `BlockLinear` over deterministic features plus a stochastic MLP projection when `bspace` is non-zero.
- Upsamples with repeat+conv or transposed-style conv depending on `strided`/`outer`.
- Applies sigmoid output and splits channels back to image keys.
- Each image reconstruction is an `outs.MSE` wrapped in `outs.Agg(..., dims=3, agg=sum)`, so image reconstruction loss has batch/time shape.

## Heads, Action Distributions, And Losses

Default heads:

| Head | Config | Output implementation |
|---|---|---|
| Reward | `agent.rewhead.output=symexp_twohot` | `outs.TwoHot` over symmetric symlog-like bins. |
| Continuation | `agent.conhead.output=binary` | `outs.Binary` predicting `~is_terminal`. |
| Discrete policy actions | `agent.policy_dist_disc=categorical` | `outs.Categorical`. |
| Continuous policy actions | `agent.policy_dist_cont=bounded_normal` | `outs.Normal` with `tanh(mean)` and learned stddev. |
| Value | `agent.value.output=symexp_twohot` | `outs.TwoHot`. |

Training losses assembled by `Agent.loss()`:

| Loss key | Meaning |
|---|---|
| `dyn` | RSSM prior-vs-posterior dynamics KL. |
| `rep` | RSSM representation KL. |
| Observation keys | Decoder reconstruction losses; `loss_scales.rec` is expanded to each decoded key. |
| `rew` | Reward prediction loss. |
| `con` | Continuation prediction loss. |
| `policy` | Imagined actor loss from lambda returns and entropy bonus. |
| `value` | Imagined value loss plus slow-value regularization. |
| `repval` | Optional replay value loss when `agent.repval_loss=True`. |

`Agent.loss()` asserts that the final loss-key set exactly matches `config.loss_scales` after expanding `rec` to decoded observation keys. If you add a head or loss, update `loss_scales`; if you add an observation decoder key, ensure `rec` expansion still covers it.

Default model loss scales:

```text
rec=1.0, rew=1.0, con=1.0, dyn=1.0, rep=0.1,
policy=1.0, value=1.0, repval=0.3
```

Important imagination settings:

- `imag_length=15`: imagined rollout horizon for actor/value loss.
- `imag_last=0`: use the whole replay sequence as start candidates unless overridden.
- `horizon=333`, `contdisc=True`: continuation-discount handling.
- `imag_loss.lam=0.95`, `imag_loss.actent=3e-4`.
- `slowvalue.rate=0.02`, `slowvalue.every=1`.

## Safe Extension Checklist

When extending the model:

1. Keep Ninjax module names stable if loading old checkpoints.
2. Preserve batch/time leading dimensions; output losses must be `[B,T]` or `[B,K]` before reduction.
3. Preserve compute dtype expectations: floating activations should be `embodied.jax.nets.COMPUTE_DTYPE`; scalar losses must be `float32`.
4. Add new loss keys to `loss_scales` and metrics under clear names.
5. Verify finite policy diagnostics before trusting training metrics.
6. Avoid changing `policy_keys` unless you understand which parameters must be synced to the policy mesh.
