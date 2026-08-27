# Training workflow

This is the source-backed workflow for the PPO-CSE/RMA recipe in
`scripts/train.py`. It is an operating guide and preflight checklist, not a
request to run the expensive native job.

## Before any native attempt

1. Use an environment compatible with the repository's old stack: the README
   calls for PyTorch 1.10.0 with CUDA 11.3 and Isaac Gym Preview 4 installed
   from NVIDIA's separately downloaded archive. Import `isaacgym` before
   importing `torch`, as the source scripts do.
2. Confirm the actual CUDA device and available VRAM. The README says the
   default run needs about 12 GB and the default Go1 configuration uses 4000
   parallel environments (the generic config starts at 4096, while
   `config_go1` and the training script set 4000). Reduce `Cfg.env.num_envs`
   for a smaller GPU, understanding that throughput and memory change; do not
   silently change the observation dimensions.
3. Confirm the environment field contract separately with
   [simulation-environment](../../simulation-environment/SKILL.md). This
   reference intentionally does not duplicate terrain, domain-randomization,
   reward, or asset field tables.
4. Choose a new, explicit run label/root outside this skill tree. Do not use
   source-relative `../runs` discovery from `scripts/play.py` in a reusable
   caller.

## Cfg override checklist from `scripts/train.py`

After `config_go1(Cfg)`, the script applies these policy-relevant overrides.
Keep a run record of every override and the final effective value:

- command bins: `num_lin_vel_bins=30`, `num_ang_vel_bins=30`,
  `distributional_commands=True`, `num_commands=15`, and stricter tracking
  thresholds (`0.7`, `0.8`, `0.90`, `0.90`);
- observation/policy shape: `num_privileged_obs=2`,
  `num_observation_history=30`, `num_observations=70`,
  `num_scalar_observations=70`, `observe_two_prev_actions=True`,
  `observe_gait_commands=True`, `observe_clock_inputs=True`,
  `observe_yaw=False`, and `observe_timing_parameter=False`;
- control/randomization: `control_type="actuator_net"`, lag of 6 with random
  lag enabled, friction/restitution/base-mass/gravity/motor-strength/motor-
  offset randomization as set in the script, and the corresponding privileged
  observations (`priv_observe_friction` and `priv_observe_restitution` true,
  most other listed factors false);
- terrain and termination: 30 by 30 terrain rows/columns, 5 m tiles, zero
  border/tile-height range, centered robots, and terminal body-height /
  roll-pitch checks as explicitly set;
- gait/command ranges: velocity, body-height, frequency, phase, offset, bound,
  duration, foot-swing, pitch, roll, stance-width, and stance-length ranges;
- normalization: friction and ground-friction ranges `[0, 1]`, yaw init range
  `3.14`, and action clipping `10.0`;
- rewards: the explicit `CoRLRewards` container and each reward scale override,
  including shaped contact terms, orientation control, collision, jump, and
  smoothness terms. Do not infer unspecified values from this list; preserve
  the source script as the authority.

The script constructs `VelocityTrackingEasyEnv(sim_device='cuda:0',
headless=False, cfg=Cfg)`, wraps it in the simulation `HistoryWrapper`, creates
a CSE `Runner` on `cuda:0`, logs `AC_Args`, `PPO_Args`, `RunnerArgs`, and `Cfg`,
and calls:

```text
runner.learn(num_learning_iterations=100000,
             init_at_random_ep_len=True,
             eval_freq=100)
```

That call is deliberately outside the safe default boundary here.

## Logger safety and metrics

The script configures `ml_logger` with a UTC path under the caller's runs root
and writes `.charts.yml`. `Runner.learn` asserts `logger.prefix` before any
learning because an empty prefix could overwrite the entire instrument server.
The README's dashboard path additionally starts `ml_dash.app` and
`ml_dash.server` and uses a profile with username `runs`; the API defaults to
port 8081 and the UI to 3001. This sub-skill does not start those processes,
contact the logger, handle credentials, or validate a network dashboard.

Use a non-empty, unique logger prefix and verify the destination before
starting. Treat credentials/tokens as caller-owned secrets; never put them in a
skill, command transcript, or generated configuration. Log the effective
configuration and git/package version beside the run so playback can restore
matching shapes.

## Rollout and export cadence

Each iteration collects 24 steps per training environment by default. The
runner logs every 10 iterations (`log_freq=10`), records video every 100
iterations (`save_video_interval=100`), and checks checkpoint export every 400
iterations (`save_interval=400`). At a save point, it:

1. saves `checkpoints/ac_weights_{it:06d}.pt`;
2. duplicates it as `checkpoints/ac_weights_last.pt`;
3. scripts a CPU copy of `adaptation_module` to
   `checkpoints/adaptation_module_latest.jit`;
4. scripts a CPU copy of `actor_body` to
   `checkpoints/body_latest.jit`;
5. uploads the two JIT files to the logger's `checkpoints/` target.

The same three artifacts are saved again after the learning loop. In CSE/RMA,
`body_latest.jit` expects the concatenated history-plus-latent input, while the
adaptation module produces the latent. See
[checkpoint-format.md](checkpoint-format.md) for exact contracts.

## Resume caveats

`RunnerArgs.resume` defaults to false. When enabled in CSE/RMA, the runner
loads `checkpoints/ac_weights_last.pt` through an `ML_Logger` rooted at the
source logger endpoint and optionally restores curriculum distribution state
when `resume_curriculum` is true. This requires a matching logger endpoint,
prefix, checkpoint, package/model architecture, and compatible environment
shape. The ordinary PPO runner declares resume fields but its checked-in
constructor does not implement the same weight-loading branch; do not assume
resume parity between the two variants.

A resumed state dict is not a substitute for the two exported JIT components.
After a model/config change, regenerate and inspect all exports. If observation
history, privileged width, action count, hidden layers, or command schema
changed, treat the old checkpoint as incompatible until proven otherwise.

## Expensive-run boundary

Do not run `scripts/train.py` as a validation shortcut. A full 100000-iteration
run is intentionally unverified, potentially long-running, GPU-intensive, and
requires Isaac Gym Preview 4. Do not start `ml_dash`, online logger traffic,
network credential flows, or video recording merely to test static claims.
First validate dimensions and checkpoint layout with the bundled safe scripts,
then obtain explicit approval and a prepared compatible CUDA/Isaac Gym runtime
for any bounded native smoke. Even a successful CPU model forward or shape
check does not prove simulator execution, training stability, or policy quality.
