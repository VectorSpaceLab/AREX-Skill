# Safe simulation and RL workflows

These workflows are intentionally staged. Commands that create a simulator or
run an episode are marked as runtime actions and require the dependency, asset,
and backend gates from the environment matrix. No workflow here downloads
benchmark assets or starts a real robot.

## A. Dispatch-only environment check

Use this before any simulator command:

```bash
python skills/disco/lerobot/sub-skills/simulation-and-rl/scripts/environment_probe.py \
  --env-type pusht --task PushT-v0
```

The script reports whether the registered config can be constructed, its
factory metadata, declared feature keys/shapes, and a non-invasive package
presence check. It does not import a benchmark package, call `make_env`, reset
a vector environment, access assets, contact the Hub, or create a render
context. Repeat with `--env-type libero`, `metaworld`, `robotwin`, `vlabench`,
`robocasa`, `robomme`, or `isaaclab_arena` to classify the requested route.

A result with `config_status=ok` and `package_status=missing` is a valid
configuration finding but not a runnable environment. A custom benchmark may
have `package_status=unknown` because its wrapper does not use the default
`gym_<type>` package name; inspect the matrix and external package gate rather
than forcing an import.

## B. Bounded local Gym smoke

Only after the requested extra is installed and the task package is approved,
start with one environment and synchronous workers. A minimal Python smoke is:

```python
from lerobot.envs.factory import make_env, make_env_config
from lerobot.envs.utils import preprocess_observation

cfg = make_env_config("pusht", task="PushT-v0")
envs = make_env(cfg, n_envs=1, use_async_envs=False)
try:
    vec = next(iter(next(iter(envs.values())).values()))
    observation, info = vec.reset(seed=0)
    converted = preprocess_observation(observation)
    print(sorted(converted), getattr(vec, "single_action_space", vec.action_space))
finally:
    for suite in envs.values():
        for vec in suite.values():
            vec.close()
```

This is a real simulator reset, so classify the result as `CPU smoke` only if
it resets, produces expected observation keys/shapes, and closes. For a
camera-based benchmark, a CPU reset may still be partial if the image backend
is not exercised or if the wrapper deferred rendering until the first step.
Never describe a successful `make_env_config` call as a rollout.

## C. Benchmark evaluation

For a compatible policy and a previously proven environment, use one task and
one episode first:

```bash
lerobot-eval \
  --policy.path=<compatible-policy> \
  --env.type=<benchmark> \
  --env.task=<one-task> \
  --eval.batch_size=1 \
  --eval.n_episodes=1
```

Add benchmark-specific options only after the one-task smoke:

- LIBERO: `--env.control_mode=relative` or `absolute`, matching the policy;
  use `--env.task_ids=[0]` for one task and keep `init_states` explicit.
- MetaWorld: use one explicit task before a difficulty group; repair the
  documented Gymnasium mismatch before importing a rollout.
- RoboTwin: choose `joint` (14-D) or `ee` (16-D) and keep the camera list
  aligned with the policy; avoid known-broken upstream tasks such as
  `open_laptop` until its success check is fixed.
- VLABench: map `image`, `second_image`, and `wrist_image` to the checkpoint's
  camera names with `--rename_map` when needed; begin with a primitive task.
- RoboCasa: begin with a task using only the installed `lightwheel` registry;
  do not request `objaverse` unless its pack is present.
- RoboMME: use its isolated environment, `dataset_split=test`, one task ID,
  and `joint_angle` or `ee_pose` matching the policy.
- IsaacLab Arena: pass `trust_remote_code=true` only after explicit approval;
  otherwise report a remote-code refusal, not a simulator failure.

Set the appropriate MuJoCo headless variable before MuJoCo benchmarks, for
example `MUJOCO_GL=egl` on a server with EGL. This setting does not install a
driver or prove that the selected renderer works.

After the first episode, verify `info["is_success"]`, accumulated reward,
terminal/truncated flags, horizon, observation shapes, and clean vector-env
closure. Increase `n_episodes`, `batch_size`, or async workers separately so a
regression can be attributed to one change.

## D. RL core smoke without an environment

The RL core can be exercised with synthetic tensors and no simulator:

1. Validate the JSON/value surface with `rl_config_check.py`.
2. Build a Gaussian actor policy and `SACAlgorithmConfig` for synthetic state
   and action dimensions.
3. Create a small CPU `ReplayBuffer` with `use_drq=false` for state-only data.
4. Add enough transitions for one batch, create an `OnlineOfflineMixer`, and
   construct `RLTrainer`.
5. Run exactly one `training_step`; inspect `TrainingStats.losses` and then
   discard the in-memory buffer.

The repository tests establish this wiring: SAC creates actor, critic, and
temperature optimizers; `update` returns losses; actor-side weights serialize
and load; the trainer consumes a mixer iterator. This proves algorithm wiring,
not environment reward quality or learning progress.

## E. HIL-SERL simulation topology

HIL-SERL is a distributed actor/learner workflow, not the RL-core smoke.
Prepare a `gym_manipulator` config with an external `gym_hil` task and a
simulated control device. Then, only after the `hilserl` extra and gRPC gates
pass:

```bash
python -m lerobot.rl.learner --config_path=<approved-train-config>
python -m lerobot.rl.actor --config_path=<same-approved-train-config>
```

Start the learner first. The learner owns the replay buffer, waits for
`online_step_before_learning`, trains the configured algorithm, checkpoints,
and sends policy weights. The actor owns environment interaction, optional
human intervention, transition construction, queues, and weight reception.
The learner service is a network/process boundary; configure host, port,
queue timeout, weight push frequency, multiprocessing mode, devices, and
shutdown behavior explicitly.

For a simulation-only first pass, use the external Panda pick-cube task and a
bounded online step count. Do not use this path with `RobotConfig`/teleop
hardware values without switching to the physical-control route and obtaining
operator authorization.

## F. Reward integration

Choose a reward model only after feature and resource checks:

1. Construct `RewardModelConfig` by name and set `device` explicitly.
2. Confirm input image/state/task keys and dataset normalization statistics.
3. For a local checkpoint, verify `config.json` and `model.safetensors` exist;
   for a Hub checkpoint, obtain approval for network, credentials, and model
   size. Use local-files-only behavior when offline.
4. Call the corresponding reward pre/post processor factory and inspect its
   keys with a synthetic batch.
5. Evaluate `compute_reward` on a tiny tensor batch before attaching it to an
   environment transition pipeline.

`reward_classifier` can be trained; its classifier processor can convert
predictions using a success threshold and success reward. SARM is temporal and
needs histories. Robometer and TOPReward are VLM-based; TOPReward is zero-shot
in this release. Reward inference can be GPU- or network-bound even when the
environment itself is CPU-capable. Record the model revision and reward scale.

## Status vocabulary

Use one of these in handoffs:

- `config`: dataclass/static validation only;
- `dispatch`: factory path returned metadata or a nested mapping;
- `CPU smoke`: reset/limited step succeeded without GPU rollout claims;
- `GPU rollout`: requested simulator, renderer, and policy executed on the
  intended GPU/backend and produced metrics;
- `partial`: only a subset of required tasks/assets/backends was proven;
- `none`: a required gate prevented any meaningful runtime check.
