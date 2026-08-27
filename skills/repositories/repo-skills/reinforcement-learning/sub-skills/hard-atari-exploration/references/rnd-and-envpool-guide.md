# PPO + RND and Envpool Guide

This reference covers the hard-exploration PPO+RND workflow label `1-ppo-rnd.py` and its shared environment plumbing label `env.py`. Use it for sticky-action RL training, model/RND interface checks, and safe interpretation of sparse-reward Atari runs.

## Scope and protocol

PPO+RND is an RL policy workflow for sparse-reward Atari games:

| Field | Contract |
| --- | --- |
| Environment keys | `montezuma`, `pitfall`, `private_eye` |
| Gymnasium/ALE id style | `ALE/MontezumaRevenge-v5`, `ALE/Pitfall-v5`, `ALE/PrivateEye-v5` |
| Envpool task style | `MontezumaRevenge-v5`, `Pitfall-v5`, `PrivateEye-v5` |
| Sticky actions | On: `repeat_action_probability=0.25` |
| Frameskip | 4 |
| Observation | 84x84 grayscale, 4-frame stack for policy; single newest 84x84 frame for RND |
| Episode handling | Full game-length episodes; life loss does not end the episode |
| Score meaning | Sticky-action RL policy return; comparable only with other matching sticky-action RL scores |
| Long-run scale | Millions to tens of millions of agent steps; first sparse reward can require very high parallel breadth |

Do not compare a PPO+RND sticky-action score directly with deterministic Go-Explore Phase 1 archive scores. The latter are deterministic trajectory-search results, not learned sticky-action policies.

## Backend split: envpool versus raw/single ALE

The workflow intentionally has two environment paths:

- **Training path:** vectorized envpool backend. It provides many parallel Atari instances, high throughput, sticky actions, frame stacking, and no rendering. This is the intended path for PPO+RND training because sparse exploration benefits from breadth.
- **Single-env render/test path:** Gymnasium/ALE wrapper path. It exists for human-mode replay or local debug and can render a window. It is much slower and does not substitute for the vectorized training backend.

Go-Explore and robustification use different raw-ALE restore paths because envpool does not expose emulator `cloneState`/`restoreState`. Keep these families separate: envpool for PPO+RND breadth; raw ALE restore for deterministic trajectory search or demo reset curriculum.

## PPO+RND model contract

The policy model is a Nature-style convolutional actor-critic with two value heads:

- input: `(batch, 4, 84, 84)` uint8 or float frames;
- shared CNN trunk: convolution sizes 8/4/3 and a 512-unit fully connected layer;
- outputs:
  - policy logits `(batch, n_actions)`,
  - extrinsic value `(batch,)`,
  - intrinsic value `(batch,)`.

The RND subsystem has two CNNs over a single normalized frame:

- `RNDTarget`: frozen random target; never optimized after initialization;
- `RNDPredictor`: trainable predictor; deeper head than target;
- input: `(batch, 1, 84, 84)` float32, normalized and clipped;
- intrinsic reward: mean squared error between predictor and target features.

Use the bundled smoke script for a CPU-only shape check:

```bash
python scripts/hard_atari_smoke.py --section rnd
```

## RND normalizers and intrinsic stream

The RND workflow depends on three details that are easy to break:

1. **Observation RMS uses the newest single frame only.** Do not feed the whole 4-stack into the RND normalizer. The normalizer tracks shape `(84, 84)` and the model then receives an explicit channel dimension.
2. **Observation values are clipped after normalization.** Convert frames to float, subtract running mean, divide by running std, clip to `[-5, 5]`, cast to float32, and use shape `(batch, 1, 84, 84)`.
3. **Intrinsic reward scale uses running std of discounted intrinsic returns.** This is scale normalization only; do not mean-center intrinsic rewards.

PPO uses separate GAE streams:

- extrinsic stream: episodic, nonterminals are `1 - done`, discount near `0.999` for sparse reward;
- intrinsic stream: non-episodic, nonterminals are all ones, discount near `0.99` so curiosity chains across deaths.

The combined advantage is weighted as:

```text
A = ext_coef * A_ext + int_coef * A_int
```

The predictor update is intentionally throttled. A large predictor update proportion can drive prediction error to near zero before exploration reaches the first key or another sparse event.

## Safe run template

The exact executable name is implementation-specific; the flags below describe the expected CLI contract of the PPO+RND workflow label.

```bash
# Long-running sticky-action PPO+RND training. Requires Atari ROM availability
# and a working envpool/Gymnasium/ALE stack.
python <ppo-rnd-workflow> \
  --env montezuma \
  --seed 0 \
  --n-envs 128 \
  --total-frames 10000000 \
  --device auto \
  --run-dir runs/rnd-montezuma-seed0 \
  --ckpt-every 1000000

# Resume from run-dir/ckpt/latest.pt if present.
python <ppo-rnd-workflow> \
  --env montezuma \
  --seed 0 \
  --run-dir runs/rnd-montezuma-seed0 \
  --resume auto \
  --ckpt-every 1000000
```

W&B logging is optional. Omit any W&B flag for offline/local runs. Do not rely on W&B for the canonical local result; use `run-dir/final.json` and `metrics.jsonl`.

## Hyperparameter landmarks

| Parameter | Typical value | Why it matters |
| --- | ---: | --- |
| `N_ENVS` | 64-128+ | Parallel breadth is the main lever for first sparse reward discovery. |
| `ROLLOUT_STEPS` | 128 | Batch is `N_ENVS * ROLLOUT_STEPS`. |
| `GAMMA_EXT` | 0.999 | Sparse extrinsic rewards need long horizon credit. |
| `GAMMA_INT` | 0.99 | Curiosity is shorter-horizon and non-episodic. |
| `EXT_COEF` / `INT_COEF` | 2.0 / 1.0 | Balances sparse extrinsic objective and curiosity. |
| `PREDICTOR_UPDATE_PROPORTION` | small, e.g. 0.05 | Slows predictor convergence so novelty signal persists. |
| `OBS_NORM_WARMUP_ROLLOUTS` | 50 | Seeds observation RMS before learning. |

If you reduce `N_ENVS` heavily for a laptop smoke, treat results only as a plumbing check. Lack of first-key discovery at small scale is expected.

## Expected local outputs

With a run directory, a well-behaved implementation should write:

```text
run-dir/
  metrics.jsonl
  final.json
  ckpt/
    latest.pt
    best.pt              # when a gate metric improves
    step_<N>M.pt          # periodic milestone, if enabled by implementation
```

A full PPO+RND checkpoint should include the actor-critic state, RND predictor, frozen RND target, optimizer, observation RMS, intrinsic-return RMS, current intrinsic-return filter, update counter, and recent episode returns. If resume restores only model weights and omits the RMS/optimizer/filter state, the resumed run is not faithful.

## Interpreting progress

Useful metrics include:

- `game_return_mean_lastK` or recent mean return: sparse extrinsic progress;
- `int_rew_mean` and `int_rew_std`: curiosity signal health;
- `predictor_loss`: whether predictor is still learning novelty;
- `entropy`: exploration health;
- `approx_kl`, `policy_loss`, `value_loss`: PPO stability;
- `nan_flag`: immediate stop-and-debug signal.

Sparse-reward Atari can look flat for a long time. A zero score does not prove the code is broken; exploding losses, NaNs, zeroed intrinsic rewards from the beginning, missing RMS state on resume, or a protocol mismatch are stronger evidence of a defect.
