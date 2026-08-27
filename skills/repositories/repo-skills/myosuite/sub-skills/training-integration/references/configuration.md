# Configuration

Use configuration files as reviewable inputs, not as commands. The historical
MyoSuite training surfaces use Hydra YAML for SB3/MJRL/TorchRL and JSON/YAML
run descriptions for DEP-RL. Preserve the source format when handing a config
to a human, but validate it with a parser that does not compose, launch, or
write Hydra output.

## SB3 Configuration Contract

A minimal SB3 plan has these fields:

| Field | Contract | Safety/reproducibility note |
| --- | --- | --- |
| `env` | registered MyoSuite environment id | Must be checked against the installed registry. |
| `algorithm` | `PPO` or `SAC` | Selects loader and algorithm-specific fields. |
| `policy` | e.g. `MlpPolicy` | Must match the saved model. |
| `seed` | integer | Record environment and learner seeds separately if wrappers require it. |
| `n_env`, `n_eval_env` | positive worker counts | Bound CPU/RAM before approval. |
| `learning_rate`, `batch_size`, `gamma` | numeric learner parameters | Validate finite/positive ranges. |
| `total_timesteps` | positive integer | Never execute merely because it parses. |
| `eval_freq`, `save_freq`, `restore_checkpoint_freq` | positive integers | Checkpoint/evaluation side effects and cadence. |
| `policy_kwargs` | framework-specific mapping | Preserve architecture and activation choices. |
| `alg_hyper_params` | mapping passed to the algorithm | Resolve `device`; default to CPU for a portable plan. |
| `job_name` | output label only | Do not use it as an unreviewed filesystem path. |

The evidence includes PPO and SAC variants. A PPO configuration can also carry
`clip_range`, `ent_coeff`, `n_epochs`, and `n_steps`; a SAC configuration can
carry replay/buffer and `tau` values. Do not copy a PPO field into SAC or rely
on a missing field's implicit framework default without recording that fact.

The source implementation wraps both training and evaluation environments in
`VecNormalize`. For a valid evaluation handoff, save and restore the same
normalization statistics, set `training=False`, and set `norm_reward=False` for
reported raw rewards. Check the number and order of observation features after
all wrappers.

## MJRL Configuration Contract

The MJRL/NPG plan requires:

- `env`, `algorithm`, `seed`, and `job_name`;
- `sample_mode`, exactly `samples` or `trajectories`;
- `rl_num_samples` when sampling samples, or `rl_num_traj` when sampling
  trajectories;
- `num_cpu`, `rl_num_iter`, `save_freq`, and `eval_rollouts`;
- `policy_size`, `vf_hidden_size`, `init_log_std`, `min_log_std`,
  `vf_batch_size`, `vf_epochs`, `vf_learn_rate`, `rl_step_size`, `rl_gamma`,
  and `rl_gae`;
- optional `alg_hyper_params`, including a CPU device choice.

The launcher normalizes the unused sample/traj field to zero and writes a job
config as a side effect during an actual run. A dry-run validator must not
reproduce that write. `policy_size` and `vf_hidden_size` are commonly tuple-like
strings in the source configs; parse and review them as data, not arbitrary
Python expressions.

## TorchRL Configuration Contract

The TorchRL PPO example uses these nested groups:

- `env.env_name`;
- `collector.frames_per_batch` and `collector.total_frames`;
- `logger.backend`, `exp_name`, `test_interval`, and `num_test_episodes`;
- `optim.lr`, `weight_decay`, and `anneal_lr`;
- `loss.gamma`, `mini_batch_size`, `ppo_epochs`, `gae_lambda`,
  `clip_epsilon`, annealing, critic/entropy coefficients, and critic loss type.

This is an implementation recipe using TensorDict/TorchRL modules, not a
portable saved-policy format. Validate that the chosen environment wrapper
provides the expected observation/action tensor specs before considering a run.
The example selects CUDA when available; a reproducible handoff should make
`device=cpu` or the exact CUDA/JAX device an explicit decision.

## DEP-RL Configuration Contract

A DEP-RL plan is normally a JSON object containing a `tonic` section and
algorithm settings. Important fields include environment expression, trainer
step/epoch/save intervals, `parallel`, `sequential`, `seed`, `working_dir`,
checkpoint selection, and optional `env_args`. `parallel * sequential` is a
resource multiplier, not a cosmetic setting. Reject or redesign an unbounded
plan before execution. The environment and trainer expressions are executable
code in the external framework; structural JSON validation cannot prove them
safe or importable.

## Launcher Selection

The source concepts are:

- `local`: a local Hydra/Submitit launcher with finite CPU/memory/time fields;
- `slurm`: a Submitit Slurm launcher with cluster-specific output and partition
  requirements;
- no launcher: direct, project-owned Python evaluation or training code.

Use one environment and one resolved config for a dry run. Do not combine
Hydra `--multirun`, a scheduler, baseline download, and a model resume in the
same agent action. `hydra-core`, `hydra-submitit-launcher`, `submitit`, and the
selected learner are separate optional dependencies.

## Reproducible Handoff Manifest

Write this manifest in the review or experiment workspace, not inside a
bundled skill and not in an implicit Hydra output directory:

```yaml
source:
  package: MyoSuite
  version: <resolved version>
  environment_id: <registered id>
  mujoco_version: <resolved version>
learner:
  framework: <sb3|mjrl|torchrl|deprl|custom>
  algorithm: <algorithm>
  policy_class: <class or adapter>
  config_file: <trusted local artifact label>
  seed: <integer>
artifacts:
  policy: <trusted local artifact label>
  normalization: <path or none>
  checkpoints: <directory or none>
evaluation:
  episodes: <small bounded integer>
  max_steps: <bounded integer>
  deterministic: true
  render: none
resources:
  device: cpu
  workers: <bounded integer>
  wall_time_limit: <explicit limit>
side_effects:
  writes: <declared files/directories>
  network: false
  credentials: none
  scheduler: none
status:
  dependency_check: <pass|missing|not-run>
  config_check: <pass|invalid|unbounded>
  training_started: false
```

The manifest is a handoff record, not a license to execute. Include unresolved
items such as a missing policy, unavailable optional framework, unknown wrapper
space, or unverified CUDA/MJX backend.
