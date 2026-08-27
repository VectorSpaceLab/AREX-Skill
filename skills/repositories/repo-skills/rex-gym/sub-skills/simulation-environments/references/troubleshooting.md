# Rex-Gym troubleshooting

Classify the failure before changing the task. Use a fresh bounded smoke with
`render=False`, `terrain_type="plane"`, and `terrain_id="plane"` to separate
installation from task/terrain behavior.

## Install and import

**`ModuleNotFoundError: rex_gym`, Gym, NumPy, or PyBullet**

1. Install the public package in the same interpreter that will run the test:
   `python -m pip install rex_gym`.
2. Prefer the legacy Python 3.7-era dependency set; this project pins old Gym,
   NumPy, and PyBullet versions in its requirements.
3. Verify with `python -c "import rex_gym, gym, pybullet; print('ok')"`.
4. If only `train` or `policy` fails while environment imports work, inspect
   the optional TensorFlow 1.x/TensorFlow Probability 0.8 compatibility. Do not
   add TensorFlow just to run the environment smoke.

**TensorFlow/protobuf errors during `rex-gym train` or `policy`**

The CLI imports PPO/TensorFlow lazily, but those commands do need the old
TensorFlow surface and may encounter protobuf incompatibilities. First confirm
that direct class construction works. Then repair the legacy ML dependency set
or route the request to [training-policy](../../training-policy/SKILL.md); do not
claim that a policy ran because a PyBullet reset succeeded.

## Assets and URDFs

**`FileNotFoundError`, `pybullet.error` while loading `plane.urdf`, Rex URDF,
meshes, cube, or textures**

- Confirm the package was installed with data files, not only copied Python
  modules. Reinstall the wheel/package in the active interpreter.
- Use `terrain_id="plane"` and `mark="base"` first.
- For `mark="arm"`, confirm the arm URDF and its referenced meshes are present
  in the installed `rex_gym` data directory.
- For hills/mounts/maze, confirm the standard PyBullet heightmap search path;
  these files are not interchangeable with the Rex robot assets.
- Do not hard-code a checkout or machine-specific data path. The package's
  `rex_gym.util.pybullet_data.getDataPath()` is the supported packaged lookup.

## Terrain and key errors

**`KeyError: None` or a terrain lookup error at construction**

Pass both `terrain_type` and `terrain_id`; for the default plane use
`terrain_type="plane", terrain_id="plane"`. The CLI already creates this pair.

**PNG filename/key error**

Only `mounts` and `maze` are valid ids for `terrain_type="png"`. Use the
[terrain mapping](terrain-and-assets.md) rather than passing `png` as the user
terrain name.

**Random terrain fails on reset with `createCollisionShape failed` or a
not-connected client error**

This is a known legacy `update_terrain()` client mismatch. Reproduce once,
report it as an environment limitation, and use plane/hills/mounts/maze when a
repeatable smoke is required. Do not run unbounded reset retries.

## Invalid API or CLI values

**Unsupported env, signal, terrain, or mark**

Use task names `poses`, `gallop`, `walk`, `turn`, `standup`; signals `ik` or
`ol`; terrains `plane`, `random`, `hills`, `mounts`, `maze`; marks `base` or
`arm`. The CLI uses Click choices for these named flags. The mapper also lists
`go`, but this package build has no usable `go_env` implementation; avoid it.

**Constructor `TypeError` after `--arg`**

`--arg KEY VALUE` is converted to a float keyword without task-specific
validation. Remove keywords not accepted by that class. Use
`target_position` only for gallop/walk, `init_orient` and `target_orient` for
turn, and pose keywords for poses. Use the direct API for a Python boolean
such as `backwards=False`.

**Both `-ol` and `-ik` were supplied**

The parser chooses open loop (`ol`) because it checks that flag first. Supply
one flag explicitly for reproducible runs.

## Action and observation shape

**`ValueError` or a failed step due to action length**

Inspect `env.action_space.shape` and use the task matrix. Expected shapes for
base mark are poses `(1,)`, gallop IK `(2,)`, gallop OL `(4,)`, walk IK `(2,)`,
walk OL `(8,)`, turn `(2,)`, and standup `(1,)`. Low-level `RexGymEnv` expects
12 base or 18 arm motor values. Task action values are compact signal
feedbacks, not raw motor angles.

**`action_space.sample()` produces an invalid gallop action**

The gallop source declares Box low/high in reverse order. Use an explicit zero
vector of the right length (or a controller-produced vector) for inspection;
the legacy step path transforms by length and returns the transformed action in
`info["action"]`.

## Rendering and cleanup

**GUI fails with display/connection errors or hangs in a server**

Set `render=False`; the constructor chooses `pybullet.DIRECT` through the
Bullet client. Only pass `render=True` after explicitly choosing a GUI and
verifying a display. The smoke script is headless unless `--render` is used.

**`render()` gives no human image**

The legacy implementation returns an RGB array only for
`render(mode="rgb_array")` and returns an empty array for other modes. GUI
visibility is controlled by construction-time `render=True`, not by assuming
that a later `render("human")` call opens a window.

**Bullet connections or processes remain after a failure**

Wrap construction and stepping in `try/finally` and call `env.close()`. Avoid
creating many environments in a loop; the bundled Bullet client disconnects
through object cleanup, while the Rex termination hook itself does not perform
long-running shutdown work.

## Goal and fall termination

`done=True` is not necessarily success. Gallop and walk set a goal flag and
brake near the target; turn sets a goal and delays final termination; standup
terminates using roll/pitch fall checks; the base environment also checks its
orientation/height fall test and task-specific lateral trajectory checks.

Inspect `info`, `env.env_goal_reached` where present, task goal flags, and
`env.is_fallen()` before labeling a run successful. Poses intentionally
overrides the fall check and returns a constant running reward, so use its
pose/observation values rather than a goal flag. A terrain collision or early
fall can therefore be a valid diagnostic `done`, not evidence of a reached
position/orientation.
