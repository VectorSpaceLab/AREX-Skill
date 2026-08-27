# Terrain and packaged assets

Use the CLI terrain name or pass the equivalent pair directly. The CLI mapping
is implemented by the legacy flag mapper:

| User name | `terrain_type` passed to `Terrain` | `terrain_id` | Generator |
|---|---|---|---|
| `plane` | `plane` | `plane` | The ordinary Bullet plane loaded during environment reset |
| `random` | `random` | `random` | A 256x256 procedurally generated heightfield, perturbed on reset |
| `hills` | `csv` | `hills` | Bullet's `heightmaps/ground0.txt` with a grass texture |
| `mounts` | `png` | `mounts` | `heightmaps/wm_height_out.png`, high vertical scale, and overlay texture |
| `maze` | `png` | `maze` | `heightmaps/Maze.png` |

The accepted CLI choices are exactly `mounts`, `maze`, `hills`, `random`, and
`plane`. A direct constructor must keep the pair consistent, for example:

```python
from rex_gym.envs.gym.walk_env import RexWalkEnv

env = RexWalkEnv(render=False, terrain_type="hills", terrain_id="hills")
```

## The explicit `terrain_id` rule

Pass `terrain_id="plane"` even when `terrain_type="plane"` for direct class
construction. The base reset creates `Rex` before the requested custom terrain
is installed, and `Rex` indexes the initial robot position by `terrain_id`.
Leaving it as `None` produces a lookup `KeyError` before a useful Gym object is
available. The CLI avoids this because `_parse_terrain()` supplies both
values. The same rule applies to `random`, `hills`, `mounts`, and `maze`.

Do not pass a filename as `terrain_id`; it is a semantic id used by the
initial-position table. Do not pass `terrain_type="png"` with an arbitrary id:
the PNG generator only maps `mounts` and `maze` to known filenames.

## What is packaged

The installed package carries its own data directory resolved at runtime by
`rex_gym.util.pybullet_data.getDataPath()`. The bundled data includes:

- `assets/urdf/rex.urdf` for the 12-motor base mark;
- `assets/urdf/rex_arm.urdf` plus the arm meshes for the 18-motor arm mark;
- the URDF mesh/STL files referenced by those robot models;
- Bullet plane, cube, material, object, and grass assets used by the base and
  turn visual marker.

Robot loading uses the package data path rather than an original source
checkout. The base environment also uses the installed `pybullet_data` search
path for the ordinary plane and the standard heightmap files. Therefore an
installation that can import the package but has incomplete package data can
still fail during `reset()` with an asset or URDF error.

The mark mapping is:

| `mark` | URDF | Motors | Base action length |
|---|---|---:|---:|
| `base` | `rex.urdf` | 12 | 12 |
| `arm` | `rex_arm.urdf` | 18 (12 legs + 6 arm) | 18 |

Task controllers produce the quadruped leg command. The base transformer
appends the packaged arm rest pose when the selected mark requires it. This
skill does not describe arm kinematics; route modeling details to
[locomotion-modeling](../../locomotion-modeling/SKILL.md).

## Terrain limitations worth checking

- `random` is generated initially, but the current `update_terrain()` path
  uses the global PyBullet module rather than the environment's client. In a
  fresh DIRECT-client probe, a second reset can fail with `createCollisionShape
  failed`/not-connected behavior. Treat random terrain as a known source quirk,
  report the failure, and do not mask it by retrying forever.
- `hills`, `mounts`, and `maze` depend on heightmap files found through the
  standard PyBullet data search path. If those files are absent, use `plane`
  to isolate package installation from terrain-data availability.
- The robot's start height differs by terrain: plane/random/maze use about
  `0.21`, hills about `1.98`, and mounts about `0.85` in the source position
  table. Do not compare early rewards across terrain without accounting for
  this initialization.
- GUI textures and reflections are visual conveniences; headless DIRECT mode
  still exercises collision and reset paths, but it does not provide a visible
  display.

For a bounded check, start with `plane`, then try one non-plane terrain and
record whether the package's standard data files are present. See
[troubleshooting](troubleshooting.md) for recovery by error class.
