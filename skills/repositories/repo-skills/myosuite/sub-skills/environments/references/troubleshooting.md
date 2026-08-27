# Environment troubleshooting

Read this when import, registration, task creation, reset/step, or deterministic
rollout checks fail.

## Import and registration

**Symptom:** `ModuleNotFoundError` says neither `gymnasium` nor legacy `gym` is
available, or `import myosuite` fails before registration.

**Cause and recovery:** Install the base MyoSuite distribution in the active
isolated environment. Prefer Gymnasium below the package's supported upper
bound; do not mix an unrelated legacy Gym API with a Gymnasium reset/step
recipe. Then run `python -c "import myosuite; print(len(myosuite.myosuite_env_suite))"`.

**Symptom:** import succeeds, but the expected task ID is absent.

**Cause and recovery:** MyoSuite registers environments as an import side
 effect. Import `myosuite` before querying `gym.envs.registry`. Use the bundled
`environment_smoke.py --list` helper or filter registry keys beginning with
`myo`; do not guess IDs from a model filename. A missing task can also mean the
installed package version differs from the task catalog.

## Missing model assets

**Symptom:** `gym.make(...)` raises a MuJoCo XML error such as `Error opening
file ... myoelbow_assets.xml` or an include path cannot be found.

**Cause:** the package was installed from a source checkout whose MuJoCo asset
submodules were not initialized, or package data was omitted from a custom
build. This is not fixed by changing the task ID.

**Recovery:** use the release package, or initialize the repository's documented
model assets before reinstalling editable source. Confirm that the selected
model's XML include tree is present, then rerun a tiny `gym.make` + `reset` smoke
with `--render none`. Do not fetch or mutate optional assets automatically from
an agent workflow; treat asset download/init as an explicit operator action.

## Task creation and API shape

**Symptom:** `gym.make` raises `NameNotFound` or an unknown environment error.

**Recovery:** check the exact registered ID and version suffix. Call
`gym.spec(task_id)` first, then create the environment. Use the task catalog
reference for fixed/random variants and for `Sarc`, `Fati`, and `Reaf` prefixes.

**Symptom:** unpacking `reset()` or `step()` fails.

**Cause:** Gym API generations differ. The verified base route uses Gymnasium:
`reset(seed=...) -> (observation, info)` and `step(action) -> (observation,
reward, terminated, truncated, info)`. Inspect the installed API before
adapting code for a legacy Gym deployment; do not silently discard truncation.

**Symptom:** action shape/range error or unstable simulation after hand-written
controls.

**Recovery:** inspect `env.action_space`, seed it if reproducibility matters,
and start with `env.action_space.sample()` or a zero/bounded action of the same
shape and dtype. Keep controls in the declared bounds. Muscle environments
normalize controls internally, so a control vector that is numerically valid
for one task is not necessarily valid for another.

## Reset, determinism, and lifecycle

**Symptom:** two random rollouts do not match even with the same reset seed.

**Recovery:** seed both the environment (`reset(seed=seed)`) and the action
space (`action_space.seed(seed)`). Compare copied observations/rewards rather
than references held by `info`. The `--check-determinism` mode of
`environment_smoke.py` performs this bounded check; differences can still arise
if the action policy, optional wrapper, or environment version changes.

**Symptom:** process hangs or crashes after a failed rollout.

**Recovery:** always call `close()` in a `finally` block. Avoid `mj_render()` and
onscreen viewer creation in headless jobs. Use the bundled helper or the
upstream CLI with `--render none`, a small episode count, and trusted inputs.

## Optional observation and policy features

**Symptom:** a visual observation, policy file, or `env_args` option fails while
basic reset/step works.

**Cause:** visual encoders, policy loaders, and task-specific arguments are
optional surfaces with their own files or dependencies.

**Recovery:** first reproduce the task with plain sampled actions and vector
observations. Inspect the task's unwrapped observation keys and declared spaces,
then add one optional feature at a time. Do not pass arbitrary strings or paths
to a policy loader, and do not treat a policy-file failure as a core package
failure.

## Rendering boundary

For display, camera, offscreen output, raw XML, or native `launch_passive`
errors, route to `simulation-rendering`. A successful CPU environment smoke is
not proof that a windowing stack or a GPU/MJX backend is available.
