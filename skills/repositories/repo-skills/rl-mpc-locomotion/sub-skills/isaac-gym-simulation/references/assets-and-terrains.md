# Assets and terrains

## Supported robot mapping

The operating launcher and MPC robot enum support exactly three names:

| CLI robot | URDF relative to the asset root | Expected controller body |
|---|---|---|
| `Aliengo` | `aliengo_description/urdf/aliengo.urdf` | `trunk` |
| `A1` | `a1_description/urdf/a1.urdf` | `trunk` |
| `Go1` | `go1_description/urdf/go1.urdf` | `trunk` |

The assets directory also contains a Mini Cheetah URDF and OBJ meshes, but its
robot enum entry and loader branch are commented out. Treat Mini Cheetah as an
asset archive, not a supported `--robot` choice. Do not infer support merely
because a model file exists.

The A1, Aliengo, and Go1 models each contain four quadruped legs with hip,
thigh, calf, and fixed foot structures and use DAE mesh files. Go1 additionally
contains camera-related links/meshes. The Mini Cheetah URDF uses OBJ meshes and
different joint/link names. A robot/controller mismatch can therefore fail at
asset loading, body lookup, DOF ordering, or controller kinematics even when
the URDF parses.

Keep the asset root and URDF path separate when calling `load_asset` or
`load_urdf`: pass the asset root as the root and the relative URDF path as the
file argument. Resolve paths from the application project root or an explicit
configured root rather than relying on the process's current directory. Check
that every mesh referenced by the selected URDF exists under the same asset
root and that package-style mesh references are accepted by the installed
loader. Do not patch a missing model by silently selecting another robot.

## Asset options and actor construction

The project-facing defaults are:

- floating base: `fix_base_link = False`;
- `use_mesh_materials = True`;
- `flip_visual_attachments = True` in the project helpers;
- `angular_damping = 0.0`, `linear_damping = 0.0`;
- `armature = 0.01` to improve inertia conditioning/stability;
- RL task default DOF mode initially `DOF_MODE_NONE`, followed by explicit
  effort properties.

After loading, query DOF and rigid-body counts and names. Identify body handles
by name instead of assuming that a body index from one robot is valid for
another. The vector tasks collect names containing `foot`, `thigh`, and `hip`,
and resolve the base as `trunk`; these names drive contact penalties and
resets. Store handles from the first actor only as template indices only when
the same asset is instantiated in every environment.

Create one actor per environment at the configured base pose. The direct helper
starts at height `0.5`; the RL task configuration starts A1 at `0.3` and
Aliengo/Go1 at `0.4`. Use the task's configured `envSpacing` (normally `2.0` in
RL) for vector training. The interactive launcher uses `0.5` spacing and a
square-grid estimate from `num-envs`; that is a display/demo convention, not a
training default.

## Ground and terrain choices

### Flat ground

Set a Z-up plane normal. The task configs use static friction `1.0`, dynamic
friction `1.0`, and restitution `0.0`. The RL task's `flat_ground` switch
chooses between this plane and a random-uniform triangle mesh. The interactive
launcher explicitly adds this plane before its demo meshes. Avoid overlapping
planes and meshes unless the experiment deliberately requires them.

### Project helper terrains

The procedural helpers convert a NumPy `int16` height field to a triangle mesh
with horizontal and vertical scale and add it to the simulation:

- `slope`: one terrain of width `2 m`, configurable length (default `2.8 m`),
  horizontal scale `0.05 m`, vertical scale `0.005 m`; the slope is derived
  from a `0.07 m` step over `0.3 m` nominal width.
- `stair`: the same small field with `0.3 m` step width and `0.07 m` step
  height; its mesh is shifted down by `0.09 m`.
- `pyramid`: pyramid stairs with the same nominal step parameters; its mesh is
  shifted up by `0.01 m`.
- `random uniform`: a `50 m` by `50 m` field at `0.1 m` horizontal and
  `0.005 m` vertical scale, with random heights from `-0.2` to `0.0`, step
  `0.05`, and downsampled scale `0.3`.
- `uneven`: a four-row field at `12 m` by `12 m`, `0.25 m` horizontal and
  `0.005 m` vertical scale. It combines random uniform, a negative slope,
  reversed stairs, and pyramid stairs.

The interactive flow demonstrates `add_terrain(..., "slope")` and a reversed
stair mesh at an x offset near `3.95`; it then creates actors. The RL path
uses the random-uniform helper when `flat_ground` is false and does not use the
interactive offsets. Record terrain name, scales, transform, and seed when
comparing runs.

### API terrain families

The underlying Isaac Gym terrain utilities support random uniform, sloped,
pyramid sloped, discrete obstacles, wave, stairs, pyramid stairs, and stepping
stones terrain. The project documentation shows how to compose these into a
height field and convert it to a triangle mesh, but the project helpers expose
only the named variants above. A future terrain must define resolution,
vertical quantization, slope threshold, mesh transform, and collision behavior
before it is considered a reproducible task.

## Caveats that affect results

- The uneven-terrain helper writes the stairs row and then immediately writes a
  reversed version to the same row range. The resulting field contains the
  reversed stairs row, not two independent stairs variants. Preserve that
  behavior only when reproducing an existing run; fix it deliberately when
  designing a new terrain and record the change.
- The demo adds terrain before env creation. Adding a mesh after actors have
  started can change contacts unexpectedly and is not the documented lifecycle.
- Height-field dimensions are computed from `int(width / scale)`. Changing
  scales without changing allocated dimensions can truncate or misalign data.
- Triangle arrays must be flattened in the format expected by the installed
  Gym API, and vertex/triangle counts must match the arrays. A malformed mesh
  commonly appears as a failed sim or missing collision rather than a useful
  Python exception.
- `fix_base_link=True` makes a robot static and invalidates locomotion control;
  use it only for an intentional asset inspection.
- Four-foot contact assumptions and `trunk` lookup belong to these quadruped
  assets. Do not reuse them for Mini Cheetah or a custom URDF without checking
  names, DOFs, body ordering, and controller kinematics.

## Terrain/asset validation checklist

Before a required-backend run, verify:

1. The selected CLI robot is one of `Aliengo`, `A1`, or `Go1` and maps to the
   intended URDF.
2. All referenced DAE/OBJ meshes are present and loadable under the asset root.
3. Asset DOF names and count match the controller/task's twelve-action
   contract; body lookups for `trunk`, feet, thighs, and hips are nonempty.
4. Exactly one intended plane/mesh configuration is added, with recorded
   friction, scales, offsets, and terrain variant.
5. The actor base height, environment bounds, spacing, and collision group /
   filter are recorded for reproducibility.
6. State tensors are acquired only after `prepare_sim`, and the simulator is
   stepped once before judging contact or velocity values.
