# Training Workflows

This reference distills MyoSuite's public training and policy-loading surfaces
into bounded operating procedures. The source's training launchers are evidence
of interfaces, not runtime dependencies of this skill.

## Framework Boundaries

### Stable-Baselines3 (SB3)

The supported tutorial pattern is:

```python
from stable_baselines3 import PPO
from myosuite.utils import gym

env = gym.make("myoElbowPose1D6MRandom-v0")
model = PPO("MlpPolicy", env, verbose=0, device="cpu")
# model.learn(total_timesteps=...)  # explicit, human-controlled operation
model.save("ElbowPose_policy")
```

The saved artifact is normally `ElbowPose_policy.zip`. Loading and predicting
are distinct operations:

```python
model = PPO.load("ElbowPose_policy.zip", env=env, device="cpu")
obs, info = env.reset(seed=123)
action, state = model.predict(obs, deterministic=True)
```

Use `SAC.load` for a SAC artifact and preserve the algorithm, policy class,
policy kwargs, and normalization state from the training run. `PPO.load` or
`SAC.load` validates the attached environment's observation/action spaces; treat
that validation as a required gate rather than forcing a mismatch.

MyoSuite's agent configs use `MlpPolicy`, CPU device defaults, `n_env`,
`n_eval_env`, `learning_rate`, `batch_size`, `gamma`, `total_timesteps`,
`eval_freq`, `restore_checkpoint_freq`, `save_freq`, `policy_kwargs`, and
`alg_hyper_params`. The repository's SB3 job surface accepts `PPO` or `SAC` and
constructs a vectorized environment, then `VecNormalize` with normalized
observations, unnormalized rewards, and `clip_obs=10.0`. A reproducible
restoration must preserve the normalization statistics, not just the model zip.

The base package does not require SB3. A current package's tutorials extra is a
convenience boundary for SB3 and related tutorial tools; the historical
`requirements_train.txt` is primarily an MJRL/Hydra/Torch list and is not a
complete SB3 or TorchRL lock. Check the actual environment instead of treating
that file as a universal install recipe.

### MJRL / NPG

The MJRL handoff is a different artifact contract. Its configuration records an
environment, `algorithm` (`NPG`, `NVPG`, `VPG`, or `PPO`), `sample_mode`
(`samples` or `trajectories`), seed, policy/value hidden sizes, RL iteration or
sample counts, CPU count, save frequency, evaluation rollouts, and a `job_name`.
The job code constructs `mjrl.utils.gym_env.GymEnv`,
`mjrl.policies.gaussian_mlp.MLP`, an `MLPBaseline`, and an algorithm object.
Do not load a MJRL pickle with SB3 or assume its action method is `predict`.

The optional dependency set includes MJRL, PyTorch, Hydra, and Submitit-related
packages. The MJRL repository dependency is external and must be approved and
pinned separately. This skill never installs it or resumes a job.

### DEP-RL

DEP-RL uses a run configuration with an environment expression, a trainer,
`parallel` and `sequential` worker counts, checkpoint policy, working directory,
and algorithm-specific values. The baseline evidence uses `deprl.load_baseline`
for a packaged/prepared baseline and `deprl.load(path, env)` for a user-owned
run. A policy is called as `policy(obs)`, not as an SB3 model. A run directory
normally needs its checkpoints and configuration together.

DEP-RL defaults in the evidence can create many environments and consume tens
of gigabytes of RAM. Never reproduce those worker counts automatically. Require
a reduced, explicitly bounded plan and a local resource check. Do not fetch
baseline checkpoints, contact experiment tracking services, or invoke
`deprl.play` from an agent session.

### TorchRL and MJX/JAX

The repository's TorchRL example is a standalone PPO implementation driven by a
Hydra YAML configuration. It uses nested `env`, `collector`, `logger`, `optim`,
and `loss` sections, a `SyncDataCollector`, `LazyMemmapStorage`, GAE, and
`ClipPPOLoss`. It is not the SB3 launcher and its policy is not an SB3 zip.
`config_mujoco.yaml` uses `HalfCheetah-v3` as an example; replace it with a
registered MyoSuite environment only after checking the wrapper and tensor
specification.

MJX/JAX is an optional accelerator path. Its model/data objects and action
specifications differ from ordinary Gymnasium environments. A CPU MyoSuite
reset/step proves neither JAX nor CUDA availability. Route MJX dependency and
backend checks separately, and never substitute a benchmark for a functional
policy evaluation.

## Policy Evaluation

### Examine-environment policy choices

The `examine_env` concept supports three choices:

1. **No policy:** a seeded random policy samples `env.action_space`; the mode is
   exploration. This is the safest behavior check.
2. **Module-qualified class:** pass a dotted class name such as
   `package.module.PolicyClass`. The class is constructed as `PolicyClass(env,
   seed)` and must provide `get_action(obs)`, returning an action as its first
   item. The module must be importable in the user's environment.
3. **Pickled object:** pass a trusted pickle whose object provides
   `get_action(obs)`. Loading is arbitrary code execution; require a trusted
   local artifact and never accept an untrusted download.

The utility then calls the environment's policy examination routine with a
horizon from `env.spec.max_episode_steps`, an episode count, mode, and render
choice. It can save traces or plots and can create rendering output, so use
`render="none"`, a small episode count, and a temporary output directory for a
bounded inspection.

An SB3 zip is not one of these choices. Do not point `examine_env --policy_path`
at it: the fallback path is pickle loading, while SB3 requires `PPO.load` or
`SAC.load`. If a project needs examine-style behavior, write a reviewed adapter
that translates `model.predict(obs, deterministic=...)` to `get_action(obs)` and
make its trust, seed, and return-shape contract explicit. A direct SB3 loop is
usually clearer and avoids inventing a loader path.

### Bounded SB3 evaluation contract

A safe evaluator should accept:

- `env_id`, local model path, algorithm, seed, episode count, max steps,
  deterministic flag, and `render` (`none` by default);
- optional `VecNormalize` statistics and an output directory only when saving
  is explicitly requested.

It should return, without training, a record containing per-episode reward and
length, termination/truncation status, environment id, model path label,
algorithm, seed, and package versions. It must close the environment in a
`finally` block and reject action shapes or bounds that do not match the space.
Treat video, trace, and plot output as opt-in side effects.

The Gymnasium loop must handle both termination flags:

```python
obs, info = env.reset(seed=seed)
for step in range(max_steps):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

If a wrapper returns a legacy four-tuple, stop and identify the wrapper/API
version instead of silently assigning `done` to the wrong value.

## Launch And Callback Contracts

The evidence names these launcher/job surfaces: `hydra_sb3_launcher.py`,
`hydra_mjrl_launcher.py`, `sb3_job_script.py`, `mjrl_job_script.py`,
`torchrl_job_script.py`, and `train_myosuite.sh`. They illustrate integration
contracts but are deliberately not copied here: they assume a source checkout,
optional packages, current-working-directory outputs, and potentially local or
Slurm execution.

The safe conceptual launch sequence is:

1. Resolve one config and print it; do not use Hydra `--multirun`.
2. Validate `env`, algorithm, sample mode/policy, numeric budgets, and all
   dependency groups.
3. Create the environment only for a reset/space probe if requested.
4. Record output, checkpoint, normalization, logging, and worker locations.
5. Present a human-controlled command template; do not execute it here.

Hydra output concepts in the evidence are `local` and `slurm`. Local output is
under a project-relative `outputs/<job>/<timestamp>` concept; Slurm output uses
an explicitly configured checkpoint filesystem. A handoff must replace these
with user-approved paths and must not assume a scheduler or a private
filesystem. `hydra-submitit-launcher` is required for the launcher plugin, and
Submitit/Slurm credentials and cluster policy are outside this skill.

SB3 callback interfaces are `stable_baselines3.common.callbacks.BaseCallback`:

- `_on_step(self) -> bool`: called during learning; return `False` to stop.
- `_on_rollout_end(self) -> None`: called after a rollout.
- `self.model`, `self.n_calls`, `self.num_timesteps`, `self.locals`, and
  `self.logger` are runtime callback state, not stable config fields.

The evidence callbacks have these behaviors:

- `InfoCallback` aggregates episode info except `r`, `t`, and `l` and records
  `env/<key>` means.
- `FallbackCheckpoint(checkpoint_freq=1)` saves `restore_checkpoint` at the
  configured cadence and on the first call; it writes to the current directory.
- `SaveSuccesses(timesteps, check_freq, log_dir, env_name)` expects
  `infos[0]["solved"]`, maintains a 200-item rolling mean, and writes a NumPy
  successes file. It is incompatible with environments that do not emit
  `solved` and has a preallocated timestep-sized result array.
- `EvalCallback(eval_freq, eval_env, verbose=0, n_eval_episodes=25)` calls
  `evaluate_policy`, records reward/length and numeric info values, and creates
  an `eval_videos/` directory in its constructor in the source implementation.

Use callbacks only after declaring their output directories and stop behavior.
Prefer a reviewed, project-owned callback when the source callback's implicit
current-directory writes or `infos[0]` assumption is not acceptable. If using
`VecNormalize`, keep training/evaluation statistics synchronized and set the
evaluation wrapper to non-training mode before reporting results.

## Reproducibility Handoff

Preserve the resolved config, environment id, package versions, algorithm and
policy class, policy kwargs, seeds, worker counts, normalization state,
checkpoint cadence, evaluation settings, git/source identity supplied by the
user, and a list of generated artifacts. State whether rendering, W&B,
TensorBoard, CUDA, JAX/MJX, or a scheduler was used. A checkpoint without its
config and normalization state is not a complete reproducible handoff.
