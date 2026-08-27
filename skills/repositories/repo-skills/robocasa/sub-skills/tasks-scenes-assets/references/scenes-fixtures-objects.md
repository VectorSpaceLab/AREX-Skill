# Scene, fixture, and object selection

## Scene identity: `(layout, style)`

RoboCasa defines a kitchen scene by one layout and one style. Layout YAMLs
specify the floor plan and fixture arrangement; style YAMLs select fixture
models, cabinet panels/handles, and textures. `scene_registry.py` resolves
integer ids to the packaged YAML paths and expands group sentinels.

Current `LayoutType` group values in the source are:

| Selector | Expanded layout ids | Meaning |
|---|---:|---|
| `-1` / `TEST` | 1–10 | target/test layouts |
| `-2` / `TRAIN` | 11–60 | pretraining layouts |
| `-3` / `ALL` | 1–60 | all layouts |
| `-4` / `NO_ISLAND` | 1, 3, 5, 6, 8 | layouts without island group |
| `-5` / `ISLAND` | 2, 4, 7, 9, 10 | layouts with island group |
| `-6` / `DINING` | 2, 4, 7, 8, 9, 10 | layouts with dining area |

`StyleType` expands `-1` to styles 1–10, `-2` to styles 11–60, and `-3` to
styles 1–60. Positive integer ids are 1–60. A selector can be an integer, a
list of integers, or a custom dictionary accepted by the scene builder. This
sub-skill's bundled validator intentionally checks only integer selectors; it
does not mutate or fetch custom dictionaries.

The `Kitchen` constructor supports either:

- `layout_ids` plus `style_ids`: the Cartesian product of the expanded lists;
- `layout_and_style_ids`: an explicit list of `(layout, style)` pairs, or the
  built-in `"5x5"`/`"5x1"` presets; or
- neither selector family: all layout/style pairs after task exclusions.

`layout_and_style_ids` is mutually exclusive with **both** `layout_ids` and
`style_ids`; the constructor asserts this. Prefer explicit pairs when the
layout/style correlation matters. A target split's ten pairs are deliberately
`(1,1), ..., (10,10)`, not the full 10×10 Cartesian product.

## `split` and object-instance mapping

The public `create_env` helper maps the high-level split as follows. This table
is a selection contract, not a substitute for the simulation workflow's
constructor/rollout instructions.

| `split` | layout/style selection | object-instance selection |
|---|---|---|
| `"pretrain"` | layout `-2` × style `-2` = 50 × 50 = 2,500 pairs | `obj_instance_split="pretrain"` |
| `"target"` | explicit pairs `(1,1)` through `(10,10)` | `obj_instance_split="target"` |
| `"all"` | layout `-3` × style `-3` = 60 × 60 pairs | no object split (`None`) |
| `None` | caller's explicit selectors, otherwise normal defaults | caller's explicit object split |

Do not pass a conflicting explicit layout/style selector with a high-level
split. The helper overwrites the scene selectors for `pretrain`, `target`, and
`all`; the bundled validator rejects that ambiguous combination before it can
silently select a different scene. Likewise, if `split` determines the object
split, do not request the opposite `obj_instance_split`.

The object sampler's `pretrain`/`target` split is per category and per registry:
it uses the first `max(len(paths)-5, ceil(len(paths)/2))` instances for
pretrain and the remainder for target. `None` uses all available paths. This
is not a scene split and it does not create missing files.

## Fixtures and placement surfaces

`KitchenArena` loads the selected layout/style, optionally enables named
fixtures, applies per-fixture configuration updates, and uses `clutter_mode`:
`0` disables entries marked `is_clutter`; `1` leaves them enabled. Useful
constructor controls are:

- `enable_fixtures=[...]` to turn on fixtures disabled by a layout;
- `update_fxtr_cfg_dict={fixture_name: {...}}` to update a layout fixture,
  commonly an auxiliary fixture placement;
- `clutter_mode=0|1` to disable or retain clutter;
- `generative_textures=None|False|"100p"`; only `"100p"` activates generated
  textures;
- `randomize_cameras=True` to add camera pose noise; this is independent of
  scene identity.

The source `FixtureType` enum covers microwave, stove, oven, sink, coffee
machine, toaster, toaster oven, fridge, dishwasher, blender, stand mixer,
electric kettle, stool, counters/islands/dining counters, cabinet variants,
shelf/drawer variants, window, and dish rack. Use `get_fixture` or
`register_fixture_ref` instead of assuming a generated fixture name. Layout
names receive group suffixes during scene construction, so exact names may
look like `sink_main_group` rather than simply `sink`.

Fixture configs are backed by `models/assets/fixtures/fixture_registry/*.yaml`
and style YAMLs. A selected config may point to a model directory containing
`model.xml`; the XML may in turn reference visual meshes, collision meshes,
and textures. A packaged YAML or Python fixture class is not proof that every
style-specific model file is installed.

## Objects and registries

`Kitchen` accepts `obj_registries` and `obj_instance_split`. The supported
public registry choices are:

- `"objaverse"` — Objaverse-sourced models;
- `"lightwheel"` — LightWheel models;
- `"aigen"` — AI-generated objects (the object loader maps this to the
  `aigen_objs` asset directory internally).

The default `Kitchen` tuple is `("objaverse", "lightwheel")`. The model
metadata defines object categories and groups, including `all`, `food`,
`in_container`, `container`, `cookware`, `pots_and_pans`, `oven_ready`,
`fruit`, `vegetable`, `meat`, `receptacle`, `tool`, and `utensil`. Task classes
usually sample with a group plus capability filters such as `graspable=True`,
`washable=True`, `cookable=True`, `microwavable=True`, `fridgable=True`,
`freezable=True`, or `dishwashable=True`.

A sampler can accept a concrete XML path, but it must be discoverable in the
selected registry metadata. For a normal group sample, the selected category
must have at least one installed model in one of the requested registries. A
successful import of `kitchen_objects.py` with empty external asset folders
only proves metadata/API readiness; it does not prove object sampling or
reset readiness.

## Asset boundary and opt-in download

The checkout contains scene YAMLs and some small/core XML assets, but not the
full downloaded fixture and object collections. A complete simulation reset
may therefore fail while resolving fixture XML, object `model.xml`, meshes, or
textures. Treat these as external data prerequisites and report them clearly.

RoboCasa ships an opt-in downloader as the package script
`robocasa.scripts.download_kitchen_assets`. Its registry covers textures,
generative textures, LightWheel fixtures, and Objaverse/AI-generated/LightWheel
objects. Invoking it prompts before downloading approximately **10 GB** and
extracting archives. Do not invoke it as a validation step; ask the user to
make that data decision first and validate file presence afterward.

The following are deliberately outside this operating sub-skill: the
`asset_scripts` conversion workflow, Blender import/export, VHACD or COACD
collision decomposition, generated asset documentation, and any destructive
or multi-gigabyte command. `demo_kitchen_scenes.py` and `demo_objects.py` are
reference-only interactive viewers. Their safe native candidate is `--help`,
not opening a viewer or sampling a random missing object.
