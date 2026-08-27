---
name: scene-configuration
description: "This skill guides authors through validated IR-SIM YAML scenes,
  object geometry, kinematics, placement, collision policy, and state APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Scene configuration

Use this sub-skill when a task needs an IR-SIM YAML scene, a robot or obstacle,
object geometry, a kinematic control vector, placement distributions, collision
policy, or object state/goal inspection. Begin with the smallest explicit scene
and run the bundled checker before constructing an environment:

```bash
python sub-skills/scene-configuration/scripts/validate_scene.py --help
python sub-skills/scene-configuration/scripts/validate_scene.py scene.yaml
```

Run those commands from the generated IR-SIM skill root, or resolve the script
path from the installed skill location. The checker uses only
`yaml.safe_load`; it does not import IR-SIM or open a GUI. It returns non-zero
for malformed YAML, unknown schema keys, unsupported shape/kinematics/behavior
combinations, ambiguous Ackermann geometry, invalid control dimensions, and
mismatched per-object lists. It is a strict preflight, not a replacement for
`irsim.make()`.

## Route by intent

- Author or diagnose `world`, `robot`, `obstacle`, or `gui` YAML with
  [the schema reference](references/yaml-schema.md).
- Choose a footprint, understand exact collision geometry, or map a control
  vector to state updates with [geometry and kinematics](references/geometry-and-kinematics.md).
- Need repeatable placement, circle formation, random shapes/goals, or central
  RNG behavior? Use [distributions and randomness](references/distributions-and-randomness.md).
- Diagnose install, parser, factory, dimension, collision, path, and optional
  dependency failures with [troubleshooting](references/troubleshooting.md).

## Minimal construction loop

1. Install the base distribution (`python -m pip install ir-sim`) and verify
   `import irsim`; use `display=False` for headless work. `pynput` is optional
   keyboard input, `pyrvo` is optional ORCA, and `imageio[ffmpeg]`/ffmpeg is
   only needed for video output.
2. Define world extents/timing and collision policy, then one robot with an
   explicit `shape`, `kinematics`, `state`, `goal`, and compatible `behavior`
   when it should move. Objects without kinematics are static.
3. Add obstacles only after checking that initial Shapely footprints do not
   overlap. Keep explicit object names unique across both sections; `group`
   and `group_name` organize objects but do not replace names.
4. Validate a tiny fixture, then use
   `irsim.make("scene.yaml", display=False, seed=7)`. The factory accepts one
   mapping or a list of object-group mappings; `number` expands a group and
   the runtime repeats short per-object lists, while the bundled checker asks
   for exact lists to prevent accidental duplication.
5. Query `obj.state`, `obj.velocity`, `obj.goal`, `obj.geometry`,
   `obj.get_info()`, `obj.get_obstacle_info()`, `obj.arrive`, and
   `obj.collision`. Use `set_state`, `set_velocity`, and `set_goal`; after
   direct state changes, let the environment refresh/rebuild its spatial data
   before relying on collision or sensor queries.

Keep this route focused on scene/object contracts. Route environment lifecycle,
`step`/render/reset, and external stepping to
[simulation-environments](../simulation-environments/SKILL.md); sensor payloads
and maps to [sensing-and-mapping](../sensing-and-mapping/SKILL.md); behavior
selection and planners to [navigation-and-planning](../navigation-and-planning/SKILL.md);
and registry or custom-controller work to
[extension-and-control](../extension-and-control/SKILL.md). Runtime files are
self-contained: the original checkout, usage files, private environments, and
review artifacts are not dependencies.
