# Assets, export, and variants

## Asset-zoo robots

mjlab ships common robot/entity factories that are used by built-in tasks and
scene export aliases. The installed `export-scene` command recognizes:

| Alias | Meaning |
|---|---|
| `g1` | Unitree G1 robot entity config |
| `go1` | Unitree Go1 robot entity config |
| `yam` | Yam manipulation robot entity config |

Use task IDs when exporting the whole task scene, aliases for bundled robots,
and `package.module:factory` for a custom entity factory that returns an
`EntityCfg`.

## Scene export

API pattern:

```python
from pathlib import Path
from mjlab.scene import Scene, SceneCfg

scene = Scene(scene_cfg, device="cpu")
scene.write(Path("exported_scene"), zip=False)
scene.write(Path("exported_scene_zip"), zip=True)
```

The export package contains a scene XML plus referenced assets. When `zip=True`,
the directory is compressed and the directory is removed after archive creation.
The exporter works on a copy of the spec to avoid mutating the active runtime.

Installed CLI pattern:

```bash
uv run export-scene g1 --output-dir /tmp/g1
uv run export-scene Mjlab-Velocity-Flat-Unitree-Go1 --output-dir /tmp/task
uv run export-scene my_pkg.robots:get_robot_cfg --output-dir /tmp/custom --zip True
```

Do not run export into a directory that contains important unrelated files: the
installed command clears the destination directory before writing.

## Variant entities

`VariantEntityCfg` represents heterogeneous mesh variants across parallel
worlds. It merges compatible variant specs into a single model while preserving
per-world mesh/data selection.

Use variants when:

- worlds should contain different mesh assets for the same logical entity
- topology is otherwise compatible
- training should expose policies to shape/appearance diversity without
  rebuilding separate simulations

Variant constraints to check before debugging policy behavior:

- variants must agree on required topology and inertial representation
- reserved names are not allowed
- assignment weights or assignment functions determine world-to-variant mapping
- collision/render geoms may differ only in supported ways

If a variant build fails, inspect the failure as a model compatibility issue
first, not as a training bug.

## Custom entity factories

A factory passed to `export-scene` or used in config should return an `EntityCfg`:

```python
def get_robot_cfg():
    return EntityCfg(spec_fn=lambda: mujoco.MjSpec.from_file("robot.xml"))
```

For reusable packages, prefer importable factories over local path closures.
If XML/assets live outside the package, package them or pass paths explicitly in
the user's project rather than relying on a deleted source checkout.

## Export smoke helper

Use `scripts/export_scene_smoke.py` when you want a bounded check that export
works for an installed task or entity alias. It writes to a temporary directory
by default and validates that a scene XML exists.
