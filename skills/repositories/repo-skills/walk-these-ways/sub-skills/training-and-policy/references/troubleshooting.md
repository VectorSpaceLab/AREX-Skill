# Training and policy troubleshooting

## `ModuleNotFoundError: isaacgym` or CUDA unavailable

`scripts/train.py`, the simulation `HistoryWrapper`, and `scripts/play.py`
import Isaac Gym and construct a CUDA environment. Isaac Gym Preview 4 is a
separately downloaded NVIDIA package, not a normal public pip dependency. The
current construction host has no usable Isaac Gym package, so this sub-skill
cannot verify simulator construction, native playback, or training.

Check the caller's isolated environment, import order (`isaacgym` before
`torch`), PyTorch/CUDA compatibility, `torch.cuda.is_available()`, driver
visibility, and the Preview 4 installation. Do not replace a missing simulator
with a CPU tensor smoke and call it a runtime pass. Route simulator fields and
backend preparation to [simulation-environment](../../simulation-environment/SKILL.md).

## History/observation shape failure

For the checked-in training recipe:

```text
num_observations = 70
num_observation_history = 30
num_obs_history = 30 * 70 = 2100
num_privileged_obs = 2
num_actions = 12
```

A common error is to pass a 15-frame history (`15 * 70 = 1050`) or one 70-value
frame to the CSE adaptation module. Inspect `Cfg.env.num_observation_history`,
the wrapper's `num_obs_history`, and the actor constructor arguments together.
A 70-scalar observation is not the same object as a 2100-scalar flattened
history. The simulation wrapper appends one frame per step and zeros history on
reset; selected environment resets must clear only their rows.

The CSE shape smoke should produce `(B, 2)` latent and `(B, 12)` action for
`ActorCritic(70, 2, 2100, 12)`. If it fails, print each tensor's shape before
changing the model. Do not pad/truncate silently.

## Missing or incompatible checkpoint components

Run `inspect_checkpoint_layout.py <run>` first. Require
`parameters.pkl`, `checkpoints/body_latest.jit`,
`checkpoints/adaptation_module_latest.jit`, and
`checkpoints/ac_weights_last.pt` for a complete run contract. Missing JIT files
are hard playback failures. A missing state dict blocks resume/reconstruction,
even if JIT playback might technically work.

If TorchScript loads but a forward pass rejects dimensions, compare the matching
configuration snapshot, actor variant (PPO versus PPO-CSE), hidden-layer args,
privileged width, history width, and action count. Regenerate all exports from
one effective model/config rather than substituting a zero latent or a different
run's body.

Do not unpickle `parameters.pkl` supplied by an untrusted source. The bundled
checker intentionally reports its presence without executing pickle code.

## Logger prefix, credentials, or network errors

`Runner.learn` asserts a non-empty `logger.prefix`; this protects against
writing over the whole instrument server. Configure a unique run prefix and
verify the intended root/profile before any native call. The README's optional
`ml_dash` UI/backend uses ports 3001/8081 and a `runs` profile, but this skill
never starts it or handles credentials. A blank/invalid token, wrong API host,
wrong prefix, or unavailable server should stop the run rather than trigger a
fallback to an implicit source-relative path.

For resume, the CSE/RMA runner's source branch loads weights and optional
curriculum state through an `ML_Logger` endpoint. Confirm endpoint, prefix,
checkpoint, architecture, and environment schema. Never place credentials in
logs or skill files.

## GPU memory / 4000-env exhaustion

The README cautions that default training is about 12 GB of GPU memory and the
Go1 recipe uses 4000 parallel environments. Reduce `Cfg.env.num_envs` before
construction on a smaller GPU and expect slower data collection. Keep
`num_observations`, `num_privileged_obs`, `num_observation_history`, and
`num_actions` unchanged unless intentionally retraining a new architecture.
Also consider headless rendering/video settings only as an explicit runtime
choice. Do not “fix” OOM by running the complete training script repeatedly.
Use a tiny approved backend smoke first.

## Config divergence after resume or playback

The source playback code copies nested `Cfg` values from `parameters.pkl` into
a global config and then disables many randomizers for evaluation. This is
source-coupled and can leave stale global state. Prefer an isolated config,
explicit compatibility checks, and a recorded effective override set.

Treat changes to command count, command ordering, observation feature flags,
history length, privileged observation fields, action count, hidden dimensions,
activation, or actuator/control mode as architecture/config divergence. A
checkpoint filename does not prove compatibility. Compare the saved snapshot,
current config, and exported tensor contracts before loading.

## What this skill does not repair

It does not install Isaac Gym, alter CUDA drivers, start an online logger,
contact a robot, launch deployment, fit actuator networks, or run full training.
The full native training/playback path is intentionally unverified in the
current environment. Use the route map in `SKILL.md` for other responsibilities.
