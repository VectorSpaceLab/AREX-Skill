# MJX acceleration troubleshooting

Use the smallest safe reproduction first: import, device probe, model/data
construction, one reset, and one step. Do not jump to PPO or a benchmark while
the backend contract is unresolved.

## Import and package failures

**Symptom: `No module named jax`, `mujoco_playground`, `brax`, or `ml_collections`.**

- **Cause:** the base package is installed without the `mjx` extra, or the
  optional install is incomplete.
- **Recovery:** run `python scripts/mjx_probe.py` to capture the missing
  components, then request/perform an explicit `MyoSuite[mjx]` installation.
  Rerun the probe. Keep the result `optional-unverified` until the import and
  one lifecycle check pass.

**Symptom: `No module named mjx` or an MJX API attribute is missing.**

- **Cause:** MuJoCo/JAX versions do not match the package's declared optional
  range, or a different `mjx` package shadows MuJoCo's MJX APIs.
- **Recovery:** inspect `mujoco.__version__`, `jax.__version__`, and the
  installed distribution metadata. Prefer the project-declared MuJoCo 3.6
  range and a compatible `mujoco-mjx` package. Do not patch imports in the
  skill; resolve the environment and rerun the probe.

**Symptom: the probe imports but `make(...)` cannot load a model.**

- **Cause:** package model assets are absent/incomplete, or a model name is
  not one of the factory's registered names.
- **Recovery:** first run import-only mode, then try one documented built-in
  factory name. Use the package's supported, explicit asset setup procedure
  if needed. Do not copy checkout paths or make the probe initialize mutable
  assets. Report an asset block separately from a JAX block.

## Device and CUDA failures

**Symptom: `--require-cuda` reports only CPU devices.**

- **Cause:** CPU JAX is installed, CUDA JAX is not selected, the driver is not
  visible, or the process is constrained to CPU.
- **Recovery:** preserve `backend-blocked`; inspect the JAX/JAXLIB variant,
  driver/runtime compatibility, and device visibility. Install the
  `mjx-cuda` extra only with approval, then rerun
  `python scripts/mjx_probe.py --require-cuda`. A CPU rerun may validate
  semantics but is not a CUDA result.

**Symptom: CUDA import fails with a plugin, driver, or XLA error.**

- **Cause:** incompatible JAX CUDA wheel, driver/runtime mismatch, unavailable
  GPU, or an environment variable selecting an unsupported platform.
- **Recovery:** capture the full first import error and the versions reported by
  the probe. Do not suppress the error or force CPU while retaining a CUDA
  label. Use `--platform cpu` only for a separate semantic diagnostic.

**Symptom: execution is unexpectedly slow or the first call hangs.**

- **Cause:** JAX compilation/warm-up, host-device transfers, too many configured
  environments, or a contact-heavy model. A benchmark README's hardware result
  is not a baseline for another host.
- **Recovery:** run exactly one reset/step with a small configuration, exclude
  compilation from any later timing, keep data on the target device, and only
  then design a bounded benchmark. Do not report acceleration from one cold
  call.

## Model and state failures

**Symptom: `TypeError` or shape errors in `reset`/`step`.**

- **Cause:** a NumPy key/action was supplied where a JAX array is expected, the
  action width differs from `env.action_size`, or a config override changes
  static dimensions inconsistently.
- **Recovery:** use `jax.random.PRNGKey(seed)`, `jnp.asarray(action,
  dtype=jnp.float32)`, inspect `env.action_size`, and start with
  `jnp.zeros((env.action_size,))`. Keep state transitions functional:
  `next_state = env.step(state, action)`.

**Symptom: observation keys or dimensions differ from a CPU Gym environment.**

- **Cause:** MJX returns a Playground-style `State` with dictionary
  observations; fatigue wrappers can append MA/MR/MF blocks; pose and reach
  tasks have different observation layouts.
- **Recovery:** inspect `state.obs.keys()` and each array shape after reset.
  Treat the observation contract as task/backend-specific. Do not unpack an
  MJX state as a Gymnasium five-tuple.

**Symptom: model contact behavior or results differ from CPU MuJoCo.**

- **Cause:** JAX preprocessing changes some cylinder contacts and mesh/
  heightfield margins, and MJX implementation details can differ for contacts,
  solver settings, precision, and batching.
- **Recovery:** compare model options, implementation, initial state, action,
  and one-step outputs. Report `semantic-mismatch` if the difference matters.
  Do not use a matching observation shape as proof of physics equivalence.

## Quaternion parity failures

**Symptom: NumPy and JAX quaternion arrays differ by sign.**

- **Cause:** quaternions have a double-cover representation: `q` and `-q` are
  the same rotation, and conversion routines may choose different signs.
- **Recovery:** compare `quat2mat(q)` outputs or normalize sign by the dot
  product before comparing raw components. Check the scalar-first convention
  `[w, x, y, z]`; do not silently reorder to `[x, y, z, w]`.

**Symptom: small parity drift or dtype mismatch.**

- **Cause:** NumPy math uses float64-oriented intermediates while JAX helper
  functions cast to float32; JIT/device execution can change last bits.
- **Recovery:** print input/output dtype, shape, device, norm, and finite status.
  Compare with an explicit tolerance such as `rtol=1e-5`/`atol=1e-5` for the
  source test scale, then tighten only after measuring. Check round trips
  through matrices rather than comparing Euler angles at singularities.

**Symptom: NaN, Inf, or a strange axis for a zero quaternion/rotation.**

- **Cause:** a zero-norm quaternion is not a valid rotation; `quat2mat` falls
  back to identity, while `quat2Vel` stabilizes the axis denominator but cannot
  infer a physical axis.
- **Recovery:** reject non-finite or near-zero quaternions at the boundary,
  define an application-level zero-rotation convention, and test that
  convention separately.

## Fatigue helper failures

**Symptom: fatigue state length or action indexing fails.**

- **Cause:** `target_load` is not restricted to muscle actuator entries, or a
  reset vector length does not equal the model's muscle actuator count.
- **Recovery:** derive the expected count from the constructed MuJoCo model,
  pass only muscle activation entries to `compute_act`, and validate
  `MA/MR/MF` shapes before stepping.

**Symptom: wrapper observations or actions no longer match the unwrapped env.**

- **Cause:** `FatigueWrapper` adds three `nu`-sized userdata blocks, disables
  base action normalization, applies its own normalization, and may append
  selected fatigue vectors to `state`.
- **Recovery:** record wrapper order and config, inspect `fatigue_obs_keys`,
  and update policy input/action contracts. Do not compare wrapped and
  unwrapped observations without accounting for these intentional changes.

**Symptom: random fatigue reset is not reproducible.**

- **Cause:** different JAX keys were used, a key was reused unexpectedly, or a
  NumPy and JAX RNG was compared as if they shared a stream.
- **Recovery:** use a fixed JAX key for an exact JAX repeat, split keys
  explicitly for independent samples, and compare state invariants
  `MA + MR + MF == 1` rather than cross-RNG sample identity.

## Reference-motion failures

**Symptom: `Missing key (time)` or an assertion about a reference shape.**

- **Cause:** the input dict lacks `time`, trajectory arrays are not rank 2, or
  init vectors do not match the trajectory width.
- **Recovery:** validate `time`, `(frames, joints)` trajectory shapes, and
  `(joints,)` init shapes before constructing `ReferenceMotion`. Include
  `robot_vel` when callers require velocity output.

**Symptom: fixed/random/track classification is surprising.**

- **Cause:** classification is based on row count: one frame is fixed, two are
  random bounds, and more than two are track data.
- **Recovery:** inspect `reference.type`, `robot_horizon`, `object_horizon`,
  and `horizon`; do not use two actual motion frames when a track is intended.

**Symptom: JAX random references repeat or differ from NumPy samples.**

- **Cause:** the inspected JAX implementation creates a fixed PRNG key inside
  `get_reference`, whereas the NumPy implementation uses its configured RNG.
- **Recovery:** treat this as an implementation/version behavior, not a device
  failure. Test the installed version, document reproducibility expectations,
  and do not claim matching random streams.

**Symptom: interpolation disagrees at an in-between time.**

- **Cause:** rounding to four decimal places, a stale local index cache, endpoint
  extrapolation settings, or a backend implementation difference.
- **Recovery:** call `reset()`, test exact timestamps first, inspect the
  `find_timeslot_in_reference` pair, compare both implementations on a tiny
  synthetic trajectory, and report the first divergent frame. Do not hide the
  discrepancy by widening tolerances indefinitely.
