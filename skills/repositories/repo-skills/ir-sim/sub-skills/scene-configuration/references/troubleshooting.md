# Scene troubleshooting

Use the checker first, then reproduce the smallest failing scene with
`display=False`, a temporary YAML file, and a fixed seed. The checker is
stricter than some runtime broadcast compatibility behavior by design.

## Install and import

- Install the base distribution with `python -m pip install ir-sim`, then
  verify `python -c "import irsim; print(irsim.__version__)"`. The covered
  release is `2.10.2` and requires Python `>=3.10`.
- Core scene construction needs the base NumPy, Shapely, PyYAML, SciPy,
  Matplotlib, and related package dependencies. No accelerator is required.
- `pynput` is optional and affects only live global keyboard input. Use
  `gui.keyboard.backend: mpl` or `display=False` for a batch-safe path.
- `pyrvo` is optional and required only for `group_behavior: {name: orca}`.
  Do not claim ORCA verification when it is unavailable; route selection to
  [navigation](../../navigation-and-planning/SKILL.md).
- `imageio[ffmpeg]` and a working ffmpeg binary are optional for video. An
  image-backed `obstacle_map` still requires a valid caller-provided path and
  readable image support.

## Parser and schema errors

**`yaml.YAMLError` or a line/column parse error**

- Check indentation, list markers, and whether `robot`/`obstacle` is a
  mapping or list of mappings. Quote strings containing YAML punctuation.
- Use finite values for coordinates and geometry. `inf` is appropriate for
  default-like `acce` limits but can be rejected by downstream tools that
  expect ordinary floats.

**Root `KeyError` / invalid top-level key**

- Only `world`, `robot`, `obstacle`, and `gui` are accepted at the YAML root.
  A sensor, shape, or arbitrary metadata section must be nested under its
  owning object or routed to the relevant sibling skill.

**Unknown object/world key**

- Compare the key to [yaml-schema.md](yaml-schema.md). IR-SIM's nested unknown
  keyword checker logs warnings, so a typo can otherwise look like a default.
  `validate_scene.py` rejects unknown keys before that point.
- Keep type selectors nested: `shape.name`, `kinematics.name`, and
  `behavior.name` select components; object-level `name` is the unique id.

## `number` and names

**Objects receive duplicated or unexpected settings**

- A flat numeric vector is shared; a nested list is per-object. For
  `number: N`, give exactly N names, states/goals, shape mappings, behavior
  mappings, or kinematics mappings when you intend heterogeneity.
- The runtime's `convert_list_length` helpers repeat the final item for short
  lists and truncate long lists. The bundled checker rejects these lengths so
  changing N cannot silently change the experiment.
- A list of sensor dictionaries is one shared sensor collection. To use
  different sensor collections per object, provide a nested list with exactly
  N collections.
- Explicit names must be unique across both root sections. Runtime creation
  raises `ValueError` such as `Duplicate object names`; a short repeated name
  list can create duplicates. Omitted names use the role/id fallback.
- `group` is an integer id and `group_name` is a label/default lookup key; they
  do not bypass name uniqueness.

## Kinematics and behavior

**State or velocity dimension errors**

- Use `[x, y, theta]` for diff/omni/omni-angular and
  `[x, y, theta, steer]` for Ackermann. The runtime pads short initial states
  and truncates long ones, but explicit dimensions are safer.
- Use exactly two controls for `diff`, `omni`, and `acker`, and exactly three
  for `omni_angular`. Match `velocity`, `vel_min`, `vel_max`, and `acce`.
- `state_dim` and `vel_dim` are advanced storage overrides, not a way to turn a
  differential model into an omnidirectional one. The checker requires a
  natural-or-larger `state_dim` and an exact `vel_dim` when they are supplied.

**Ackermann vehicle has an ambiguous footprint**

- Set both the kinematics mode and the shape wheelbase:

  ```yaml
  kinematics: {name: acker, mode: steer}
  shape: {name: rectangle, length: 2.0, width: 0.8, wheelbase: 1.4}
  state: [1, 1, 0, 0]
  velocity: [0, 0]
  ```

- `mode: steer` interprets control `[linear, steer]`; `mode: angular`
  interprets `[linear, angular]`. The state still stores four entries.
- The factory has a `1.0` fallback for missing kinematics wheelbase, but the
  geometry handler cannot align the shape meaningfully without a shape
  wheelbase. The checker rejects missing/non-positive wheelbase on Ackermann
  circle/rectangle shapes.

**Behavior lookup fails**

- Built-ins are registered per kinematics: `diff`/`omni` support `dash`,
  `rvo`, `sfm`; `omni_angular` supports `dash`; `acker` supports `dash`.
  Thus `rvo` on `acker` or `sfm` on `omni_angular` is unsupported, not a YAML
  indentation problem.
- An object without behavior remains still when no action is supplied. A
  missing goal also prevents goal-directed behavior from doing useful work.
- `group_behavior: {name: orca}` is a group-level optional `pyrvo` surface, not
  an individual `behavior` value.
- Unknown named kinematics is rejected by `ObjectFactory.create_robot` /
  `create_obstacle` with `NotImplementedError`, even though the lower-level
  `KinematicsFactory` has a stationary-compatible fallback. Treat it as an
  invalid scene and use a registered extension only through
  [extension and control](../../extension-and-control/SKILL.md).

## Geometry and collision

**Invalid or surprising shape**

- `circle` needs a positive radius when specified; `rectangle` uses positive
  length/width; `polygon` needs an ordered explicit vertex list unless you
  deliberately use random generation; `linestring` needs at least two
  vertices; `compound` needs a non-empty list of circle/rectangle/polygon
  parts.
- Compound part poses must be finite `[x, y, theta]` and parts cannot have
  individual colors. The owning object supplies the color.
- The runtime repairs invalid polygons. For safety-critical collision checks,
  use a simple valid boundary and inspect `obj.geometry.is_valid`.
- A linestring is a line geometry rather than a solid wall. Use consecutive
  segments for RVO line-obstacle handling; use polygons/circles for filled
  collision footprints.

**Collision occurs on the first step**

- Inspect initial transformed Shapely geometries and move bodies apart. Exact
  compound unions and offset circles are used, not just centers/radii.
- `world.collision_mode: stop` is the default. `unobstructed` disables global
  stopping, `unobstructed_obstacles` relaxes obstacle-obstacle stopping, and
  object `unobstructed: true` exempts an object from stopping policy without
  removing its geometry.
- `reactive` currently follows the unobstructed branch in this release; it is
  not an automatic collision-avoidance algorithm.

## Distributions and data paths

**Random placement exhausts attempts or overlaps**

- `random` uses world-derived bounds inset by `0.5`, default `min_distance`
  `1.0`, and at most 1000 attempts per point. It does not account for the
  actual footprint or obstacles. Lower the count/spacing, widen bounds, or
  use manual placement.
- `circle` uses a default radius of `min(width,height)/2 - 0.5`, but a custom
  radius can put bodies outside the world. Check shape extents.
- `uniform` and distribution `3d: true` are not implemented. Use `manual`,
  `random`, or `circle`.
- Call `irsim.make(..., seed=42)` or
  `irsim.util.random.set_seed(42)` before construction. Compare generated
  state/goal/geometry properties after resetting the seed; do not use global
  `numpy.random.seed` as a substitute.

**Image/map file not found**

- A string `obstacle_map` is interpreted as an image path relative to the
  caller's working context. Use a real user-provided path, not a path from an
  example or source checkout.
- Prefer a generator mapping with an explicit `name` and required parameters
  for portable scenes. Map generator details belong to
  [sensing and mapping](../../sensing-and-mapping/SKILL.md).

## API sequencing and safe checks

- `set_state` refreshes the object's geometry, but a direct mutation does not
  by itself rebuild the environment-wide Shapely spatial tree. Use the
  environment's `refresh`/step path before querying synchronized collisions or
  sensors.
- `set_velocity` updates stored control input and does not advance the object.
  `set_goal` changes the active goal; `init=True` also changes its reset copy.
- `obj.get_info()` is an `ObjectInfo` snapshot used by behaviors/planners;
  `get_obstacle_info()` is the geometry/motion snapshot for collision-aware
  consumers. Neither replaces live `state`/`velocity` properties.
- Run only the safe checker checks during drafting:

  ```bash
  python sub-skills/scene-configuration/scripts/validate_scene.py --help
  python sub-skills/scene-configuration/scripts/validate_scene.py good.yaml
  python sub-skills/scene-configuration/scripts/validate_scene.py bad.yaml
  ```

Native tests and original usage examples are evidence candidates for integrated
verification, not runtime dependencies of this sub-skill.
