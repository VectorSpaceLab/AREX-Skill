# Tasks, scenes, and assets troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `layout_and_style_ids` assertion | `layout_ids` or `style_ids` was also supplied | Use one explicit pair selector family only. |
| `split="target"` appears to ignore a requested layout | The high-level helper intentionally maps target to `(1,1)` … `(10,10)` | Remove the conflicting explicit selector or omit `split` and pass the pair directly. Use `scripts/validate_scene_selection.py` to catch this before construction. |
| Invalid layout/style id or a missing YAML | Positive id is outside 1–60, or a custom dictionary is malformed | Use the integer groups documented in `scenes-fixtures-objects.md`; for custom dictionaries validate the YAML/config separately. |
| `ValueError` for `split` or `obj_instance_split` | Unsupported spelling/value | Allowed high-level splits are `None`, `pretrain`, `target`, `all`; object-instance values are `None`, `pretrain`, `target`. |
| `ValueError`, zero-probability sampling, or no candidate object | Requested registry/category has no installed `model.xml` paths, often because external assets are absent | Check the registry folders and choose an installed registry/category. Do not treat the category metadata import as proof of files. |
| `aigen` cannot be sampled | AI-generated object archive is not installed, or the internal `aigen_objs` path is empty | Install the opt-in AI-generated object data or use `objaverse`/`lightwheel` only when their files are present. |
| `FileNotFoundError` for fixture XML, mesh, or texture during reset | Scene YAML selected a style-specific model whose external asset is missing | Install the relevant asset archive and verify transitive XML references. A constructor/import probe cannot clear this gate. |
| `PlacementError` / repeated model reload | Region too small, object exceeds `max_size`, required fixture is absent, or distractors collide | Fix the fixture/layout choice, reduce object size/scale, adjust a documented placement region, or disable optional clutter/distractors. Do not disable validity checks merely to hide a bad task. |
| `get_fixture` finds the wrong instance | Multiple fixtures share a type/name after layout suffixing | Use `register_fixture_ref` with `ref`, `full_name_check`, or a task-specific fixture id; do not assume the bare type is unique. |
| `enable_fixtures` has no effect | The name does not match the layout config after the expected group context, or the fixture is not present in that layout | Inspect the layout YAML's fixture names and select a layout that contains the required appliance. |
| Fixture override mutates later episodes | A layout/style dictionary was changed in place | Pass a copied update dictionary through `update_fxtr_cfg_dict`; avoid editing packaged YAMLs. |
| `generative_textures` assertion | Value is not `None`, `False`, or exact `"100p"` | Use `"100p"` only after the generated texture archive is installed; otherwise leave it disabled. |
| Demo `--help` fails before printing help on a headless host | Interactive demos import `pynput` and may require an X/display backend before argparse runs | Treat demos as interactive/viewer references. Run help on a display-capable host or with a compatible headless input backend; do not open the viewer as a smoke test. |
| Custom MJCF object is rejected | The XML path is not registered in the chosen registry, lacks sibling `model.xml`, or references missing meshes/textures | Add a complete model directory and registry metadata, then use a concrete path only after the registry lookup can reverse-resolve it. |
| Custom task imports but is not selectable | The module was not imported, the class is a base/helper class, or the class name collides | Import the module through the package's task registration path and use a unique concrete class name. Check the registered environment names in the simulation workflow. |
| Full task validity test is slow or fails in bulk | Hundreds of environments multiply asset and placement costs | Start with one fixed pair, one task, and a bounded reset. Defer the full validity matrix until all assets are installed. |

## Current verification boundary

The inspected environment verified RoboCasa 1.0.1 import compatibility with
robosuite 1.5.2, MuJoCo 3.3.1, NumPy 2.2.5, and the package's related runtime
packages. It registered 374 kitchen environments. `demo_kitchen_scenes.py
--help` and `demo_objects.py --help` passed only when a compatible dummy input
backend was supplied; without a display, `pynput` failed before argparse.
Scene registry expansion and signatures were checked without downloading data.
A direct `Kitchen`/`create_env` constructor could be reached, but reset was
blocked by missing downloaded fixture XML. No claim of a complete simulation
pass, random object sample, visual render, or full fixture/layout test is made.

## Excluded repair paths

Do not automatically run `robocasa.scripts.download_kitchen_assets`: it prompts
for an approximately 10 GB download. Do not run asset conversion scripts or
install Blender, VHACD, or COACD as part of task selection. Those are deliberate
user-approved asset-production workflows, not safe validation helpers.
