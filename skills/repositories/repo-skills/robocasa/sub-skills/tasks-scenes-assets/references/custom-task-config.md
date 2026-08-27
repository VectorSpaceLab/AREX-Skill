# Custom task and placement configuration

## Minimal task lifecycle

A custom task should subclass `Kitchen` (or a narrowly suitable existing
RoboCasa task) and implement only the behavior it owns. The kitchen metaclass
registers concrete subclasses by class name; importing the module is therefore
part of making a new task discoverable.

Typical lifecycle:

1. `__init__`: accept task-specific options, append required names to
   `enable_fixtures`, and pass the remaining keyword arguments to `Kitchen`.
   Do not discard scene, robot, split, registry, or camera kwargs.
2. `_setup_kitchen_references`: call `super()`, then resolve fixtures with
   `get_fixture(FixtureType.X)` or `register_fixture_ref(name, kwargs)`. Set
   `init_robot_base_ref` to a relevant appliance/fixture when the robot should
   start there.
3. `get_ep_meta`: call `super()` and set `ep_meta["lang"]` to the task
   instruction. Preserve existing novel-instruction behavior when the task
   supports it.
4. `_get_obj_cfgs`: return deterministic configuration dictionaries for target
   and distractor objects. Use `sample_object` through `obj_groups`, capability
   filters, object scaling, and placement constraints.
5. `_setup_scene` or `_reset_internal` (only when needed): call `super()` and
   initialize appliance state, open doors, add liquid sites, or reset
   multi-stage bookkeeping.
6. `_check_success`: return a boolean based on contacts, fixture state,
   receptacle containment, object distance, and gripper release as appropriate.

Composite tasks use the same lifecycle. They commonly create several objects,
store references in `self.fixture_refs` or episode metadata, and track stages
in `_check_success`. A composite task is not made composite by a name alone:
its success condition must require the intended sequence or final arrangement.

## Supported `Kitchen` configuration inputs

The installed signature accepts these task/scene controls in addition to the
robosuite robot and camera controls:

| Input | Use |
|---|---|
| `robots` | robot name or one-element robot list; the inspected `Kitchen` path requires one robot |
| `layout_ids`, `style_ids` | integer/list/dictionary selectors expanded by `scene_registry` |
| `layout_and_style_ids` | explicit pair list or `"5x5"`/`"5x1"`; excludes both individual selector inputs |
| `enable_fixtures` | enable named layout fixtures, including task-specific appliances |
| `update_fxtr_cfg_dict` | update fixture YAML config before construction |
| `obj_registries` | tuple/list of `objaverse`, `lightwheel`, `aigen` |
| `obj_instance_split` | `pretrain`, `target`, or `None` per object category/registry |
| `clutter_mode` | `0` disables clutter fixtures; `1` retains them |
| `randomize_cameras` | add camera pose noise |
| `generative_textures` | `None`/`False` or exact value `"100p"` |
| `use_distractors` | request distractor objects where the environment uses the flag |
| `use_novel_instructions` | select task-provided instruction variants |

The high-level `split` mapping belongs to `create_env`; when using it, do not
also provide conflicting scene selectors. See the scene reference for the
expanded target/pretrain/all behavior.

## Object configuration schema

The placement initializer validates the following top-level keys:

`type`, `name`, `model`, `obj_groups`, `exclude_obj_groups`, `graspable`,
`cookable`, `washable`, `microwavable`, `dishwashable`, `fridgable`,
`freezable`, `max_size`, `object_scale`, `placement`, `info`,
`init_robot_here`, `reset_region`, `rotate_upright`, and auxiliary-object
fields used by the package.

A normal object config looks like this conceptually:

```python
{
    "name": "obj",
    "obj_groups": "food",
    "graspable": True,
    "placement": {
        "fixture": self.counter,
        "size": (0.60, 0.30),
        "pos": ("ref", -1.0),
        "offset": (0.0, 0.10),
    },
}
```

Use a concrete source class as the final authority for dimensions and object
roles. Important fields include:

- `obj_groups`: one group/category or a tuple/list of alternatives;
- `exclude_obj_groups`: remove categories from a broad group;
- capability filters: require the selected model to support an operation;
- `max_size=(x, y, z)`: reject models exceeding the bound;
- `object_scale`: scalar or three-element scale multiplier;
- `placement.fixture`: target fixture or fixture type;
- `placement.size`: sampling region size; `"obj"`, `"obj.x"`, and `"obj.y"`
  can derive dimensions from the model;
- `placement.pos`: normalized region coordinates, with `None` for centered and
  `"ref"` to align to `sample_region_kwargs["ref"]`;
- `placement.offset`, `rotation`, `rotation_axis`, `margin`;
- `ensure_object_boundary_in_range` and `ensure_valid_placement`;
- `placement.try_to_place_in` plus optional
  `try_to_place_in_kwargs` for automatic container creation;
- `placement.object` and `placement.sample_args.reference` for nesting an
  object inside an existing container.

The initializer samples the fixture reset region, subtracts a default margin
(usually 0.04; toaster/blender use 0), and checks object boundaries and
collisions. A target region that is smaller than the object, an unavailable
fixture, or a model larger than `max_size` can produce `PlacementError` or
repeated resampling.

## Fixture customization patterns

Use `enable_fixtures` when a layout marks an appliance/accessory disabled. Use
`update_fxtr_cfg_dict` for layout-level changes, for example moving an
auxiliary blender lid into the parent fixture's region while requiring a valid
non-overlapping placement. Do not mutate the shared layout YAML in place.

Fixture configuration is style-driven. The style chooses a fixture model and
subcomponents; the layout supplies placement and attachment. For a new fixture
model, the expected package-side contract is a model directory with `model.xml`
and all referenced mesh/texture files. A Python wrapper or registry YAML
without those files is incomplete.

## Safe customization recipe

1. Start with an existing task whose fixture topology and object roles match.
2. Copy only the class-level configuration pattern into a project module; keep
   the source task's success checks as a behavioral reference.
3. Choose a fixed layout/style pair and a small explicit object registry while
   debugging. Run the bundled integer validator before construction.
4. Check the selected asset tree for every fixture and sampled object XML,
   including transitive mesh and texture references.
5. Construct and reset only after the asset gate passes. Then run a short,
   bounded success-state or placement test in the simulation workflow.
6. Generalize to pretrain/target/all only after one fixed configuration works.

Do not claim a custom task is simulation-verified from a class import alone.
The current inspected checkout allowed API inspection and a direct constructor
probe but lacked the complete downloaded fixture/object data for a full reset.
