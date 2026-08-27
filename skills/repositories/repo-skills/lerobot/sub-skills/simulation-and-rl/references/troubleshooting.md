# Troubleshooting and intentional limits

Use the first matching category. Preserve the original exception and report
which stage failed: `config`, `dispatch`, package import, worker reset,
rendering, policy action, reward model, or actor/learner service.

## Missing optional extra or package

**Symptoms:** `ModuleNotFoundError`, an unavailable Gym ID, or a probe reports a
missing package.

1. Confirm the selected `env.type` and exact benchmark package name.
2. Install only the documented LeRobot extra or the benchmark's isolated
   external package set.
3. Re-run the dispatch-only probe; it is safe and does not prove a rollout.
4. If the package is intentionally absent from pyproject metadata, do not use
   `pip install lerobot[<invented-name>]`; use the external-package gate in
   `compatibility.md` and stop if the user did not approve that environment.

A package import that succeeds under a test mock does not satisfy this gate.

## NumPy/Gymnasium version conflict

**Symptoms:** resolver failure, import-time ABI error, MetaWorld render-mode
assertion, or RoboMME/ManiSkill rejection.

- For MetaWorld's documented render assertion, inspect the actual Gymnasium
  version and consider the isolated `1.1.0` repair. Do not downgrade a shared
  base environment without a compatibility decision.
- For RoboMME, do not mix the benchmark's NumPy 1.x/Gymnasium 0.29.x tree with
  the core NumPy 2.x/Gymnasium 1.1.x environment. Use a separate container or
  environment.
- For binary errors from SciPy, MuJoCo, placo, SAPIEN, or OpenCV, report the
  package and ABI/driver error rather than retrying an unrelated configuration.

The bounded scripts report versions when packages are already installed, but
they do not mutate or resolve environments.

## Config succeeds but simulator is unavailable

**Symptoms:** dataclass construction is fine, but `make_env`, `reset`, or the
first worker step fails with missing assets, import errors, or task lookup.

This is expected for lazy wrappers. Classify the result as `config` or
`dispatch`, then check the relevant matrix row:

- LIBERO: task suite files, initial-state files, and Linux MuJoCo rendering;
- LIBERO-plus: plus fork and extended assets, with no vanilla namespace mix;
- RoboTwin: external tree on `PYTHONPATH`, task YAML/config, SAPIEN/CuRobo,
  and downloaded assets;
- VLABench: package imports, dm-control/MuJoCo versions, and meshes;
- RoboCasa: macros, fixture/texture/object registries, and task horizon;
- RoboMME: isolated ManiSkill/SAPIEN/Vulkan environment and episode data;
- IsaacLab Arena: trusted Hub module, IsaacLab runtime, and requested device.

Do not replace a missing benchmark with PushT and call the requested benchmark
verified. A bounded CPU synthetic or state-only check is a partial substitute.

## Render, display, and process-start failures

**Symptoms:** EGL/GLFW errors, blank/incorrect images, MuJoCo physics errors,
Vulkan initialization failures, dead async workers, or crashes only with
`n_envs > 1`.

1. Set the simulator's documented headless backend before process creation
   (`MUJOCO_GL=egl` is the usual MuJoCo server setting).
2. Retry one environment with `use_async_envs=false` and a single task.
3. Verify the image shape/dtype and close the vector environment.
4. Only then increase workers or enable async. If the error is backend-specific,
   record it as a runtime gate, not a policy failure.

VLABench may retry unstable MuJoCo layout construction internally, but an
exhausted retry is still a simulator failure. Do not extend episode or retry
budgets without user approval.

## Policy feature or action mismatch

**Symptoms:** key errors, normalization failures, wrong tensor rank, or action
space shape errors.

Compare, in order:

1. raw wrapper keys (`pixels` camera names, `agent_pos`, `robot_state`);
2. `features_map` and `env_to_policy_features(cfg)`;
3. policy `input_features` and `output_features`;
4. dataset columns and any explicit `rename_map`;
5. action mode (`relative`/`absolute`, `joint`/`ee`, `joint_angle`/`ee_pose`).

Do not solve a key mismatch by changing the feature shape alone. Visual names
are part of dataset normalization and checkpoint compatibility.

## Reward model failures

**Symptoms:** model config works but `make_reward_model` fails, processor
cannot find a key, or inference exhausts memory.

- Check the reward type against the four built-in names.
- Confirm local `config.json` and `model.safetensors`, or approve Hub access
  and revision resolution.
- Check `image_key`, `state_key`, task text, frame history, camera count, and
  dataset statistics.
- Use a tiny synthetic tensor batch and the correct pre/post processor before
  attaching the reward to HIL transitions.
- Lower resource demand only with an explicit experiment decision; do not
  report a zero-shot VLM output as a trained reward model.

`PreTrainedRewardModel.from_pretrained` loads safetensors and sets evaluation
mode. A model is trainable only when its subclass overrides `forward`; the
base inference contract is `compute_reward(batch)`.

## SAC, replay, or trainer failures

**Symptoms:** algorithm factory rejects the config, replay allocation fails,
empty-buffer sampling, or a trainer update has shape/device errors.

- Ensure the algorithm is registered as `sac` and its `policy_config` is set.
- Ensure replay capacity is positive and the first transition has stable state
  and action shapes.
- Add enough transitions before sampling; learner online training waits for
  `online_step_before_learning`.
- Keep `online_ratio` in `[0,1]`; the mixer needs an online buffer and an
  optional offline buffer.
- Match batch state keys to the Gaussian actor policy and keep storage device
  separate from learner device if memory is limited.
- For image replay augmentation, disable DrQ in the bounded state-only smoke;
  do not infer visual RL correctness from a state-only pass.

Run the repository's narrow RL tests only when the installed test extra and
backend are approved. A synthetic trainer update proves wiring, not learning
quality.

## HIL-SERL actor/learner service failure

**Symptoms:** gRPC import errors, actor cannot connect, stale weights, queues
stall, or no learning begins.

- Install/verify the `hilserl` extra and `grpcio` import before starting either
  process.
- Start the learner first, and ensure host/port match the actor config.
- Confirm the actor's environment is simulation-only if no physical-control
  approval was given.
- Check that online steps exceed the learner warmup threshold and that replay
  transitions carry reward/done/truncated fields.
- Keep the same policy/environment/algorithm config on both sides; inspect
  weight push frequency and queue timeouts.
- Shut down both processes cleanly; do not leave child processes or hardware
  connections running after a failed experiment.

A service connectivity check is not a successful RL run.

## Intentional omissions and uncertainty notes

- No reference here downloads benchmark assets, model weights, datasets, or
  remote Python files.
- No tool here discovers credentials, starts a learner/actor service, performs
  a long training run, or actuates a robot.
- Exact simulator commits, GPU driver versions, Vulkan/EGL support, and asset
  completeness are environment-specific and must remain unresolved until
  explicitly checked by the user-approved runtime.
- External benchmark task lists and upstream success implementations can
  change. Treat the LeRobot wrapper's current task surface as routing evidence,
  then verify the installed external revision before reporting scores.
- A passing import, mocked native test, CPU state smoke, or synthetic RL update
  is not evidence of full visual GPU benchmark recovery.
