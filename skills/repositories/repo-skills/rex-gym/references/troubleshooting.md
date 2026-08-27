# Rex-Gym cross-cutting troubleshooting

Read this when a package import, legacy dependency, package-data, or workflow
error spans more than one sub-skill. Keep the first failing layer visible:
interpreter/dependencies, package import, CLI parsing, environment/model, or
PPO/checkpoint runtime.

## Installation and imports

- **Symptom:** modern pip reports that Gym 0.17.1 wants `cloudpickle>=1.2,<1.4`
  while TensorFlow Probability 0.8 wants `cloudpickle==1.1.1`.
  **Recovery:** use an isolated legacy Python 3.7 environment, install the
  repository's compatibility family with a controlled resolver, verify imports,
  and record the chosen cloudpickle behavior. Do not upgrade only one package
  to a current major version.
- **Symptom:** TensorFlow fails with `Descriptors cannot not be created
  directly` while importing generated protobuf modules. **Recovery:** use
  protobuf 3.20.x or earlier for the TensorFlow 1.15 stack, then rerun
  `import tensorflow as tf` and `import tensorflow_probability as tfp`.
  `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` is a slower diagnostic
  fallback, not a reason to hide a broken installation.
- **Symptom:** `ModuleNotFoundError` for `pybullet`, `gym`, NumPy, Click, or
  `ruamel.yaml`. **Recovery:** verify that `python`, `pip`, and `rex-gym` use
  the same isolated interpreter; install the public package and its documented
  legacy runtime dependencies there; rerun the minimal `import rex_gym` check.

## Package data and direct constructors

- **Symptom:** direct construction raises `KeyError: None` in the robot terrain
  lookup. **Cause:** the class defaults `terrain_id=None` even though the robot
  model indexes a terrain-init table. **Recovery:** pass both
  `terrain_type="plane"` and `terrain_id="plane"` (or the matching supported
  terrain id). The CLI supplies both automatically.
- **Symptom:** URDF, heightmap, or texture load fails. **Recovery:** use an
  installed package that includes package data; do not point a future agent at
  a vanished checkout. Start with plane/DIRECT, then validate the requested
  terrain and mark. Keep `base`/`arm` consistent with the available URDF and
  action width.
- **Symptom:** the `arm` mark gives unexpected shapes. **Recovery:** it has 18
  motors: the 12 leg commands plus six arm-rest values. Compact task observations
  remain task-specific, while base-level motor observations/actions grow with
  the mark.

## CLI and API misuse

- **Symptom:** Click rejects `--env`, `--terrain`, or `--mark`. **Recovery:**
  use the documented choices; `go` appears in the mapper but is not a usable
  task/policy in this checkout. Use the task matrix before constructing a
  command.
- **Symptom:** command accepts both `--open-loop` and `--inverse-kinematics`
  unexpectedly. **Recovery:** treat the combination as invalid in preflight;
  the current parser silently gives open loop precedence.
- **Symptom:** repeated `--arg`/`--flag` keys do not preserve both values.
  **Recovery:** the parser writes pairs into one dictionary and later values
  overwrite earlier ones. Use one occurrence per keyword and verify the target
  constructor accepts it.
- **Symptom:** a step raises a shape or unpacking error. **Recovery:** use the
  task matrix's signal-specific action shape, the old four-return Gym API, and
  a zero/known-safe action. Gallop's legacy `Box` bounds are reversed; do not
  rely on `action_space.sample()` for that task.

## Runtime and GUI

- **Symptom:** GUI construction fails on a server or hangs. **Recovery:** use
  `render=False` and PyBullet DIRECT. GUI requires a display and is for
  interactive sliders or visualization, not bounded CI validation.
- **Symptom:** `done` appears before the requested step count. **Recovery:**
  inspect fall, target-goal, and lateral out-of-trajectory rules for the chosen
  task; stop stepping after `done`, retain `info["action"]`, and close the env.
- **Symptom:** a rendered `rgb_array` request is empty or unexpected. **Recovery:**
  the implementation supports the legacy `render(mode="rgb_array")` path;
  other modes return an empty array. Confirm the renderer and display before
  treating an empty frame as a model error.

## PPO and policy surface

- **Symptom:** training starts unexpectedly or consumes resources. **Recovery:**
  do not use `train` as a smoke test; run the policy catalog inspector and CLI
  help, request an explicit bounded run plan, and verify a writable log parent.
- **Symptom:** config/checkpoint is absent or `go` has no policy. **Recovery:**
  inspect the packaged catalog; only the listed task/controller policy ids are
  supported. Do not fabricate a checkpoint or infer support from an environment
  name alone.
- **Symptom:** task/controller dimensions or batch shapes fail. **Recovery:**
  route back to the simulation task matrix, match the config's environment and
  signal, use a positive agent count (prefer one dividing `update_every=25`),
  and stop before increasing resources blindly.
- **Symptom:** policy playback opens no window or never returns. **Recovery:**
  confirm display and checkpoint sidecars, then treat playback as an explicit
  GUI loop. Use the bounded catalog check for verification; it does not claim
  policy quality or sim-to-real transfer.
