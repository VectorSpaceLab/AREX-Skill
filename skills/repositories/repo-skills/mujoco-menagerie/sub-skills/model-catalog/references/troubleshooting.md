# Model Catalog Troubleshooting

Use this when a catalog answer is ambiguous or a model directory does not match the usual Menagerie pattern. Keep fixes at catalog level; route loading/runtime failures to `model-loading`, editing to `model-editing`, and maintainer checks to `contribution-maintenance`.

## A directory has no `scene*.xml`

Expected structural rule: every model directory should have at least one `scene*.xml`, except `realsense_d435i`.

Catalog response:

1. Check `model-index.json` fields `scene_xmls`, `scene_required`, and `scene_exception`.
2. If the directory is `realsense_d435i`, use `realsense_d435i/d435i.xml` and state that it is a sensor-only asset, not a robot scene.
3. If any other directory has no scene, report it as a catalog/layout problem. Do not invent a scene path. If the user wants to repair it, route to `contribution-maintenance` for structural checks and `model-editing` for MJCF creation.

## The user asks whether `realsense_d435i` is standalone

Answer: `realsense_d435i` is cataloged as Miscellaneous and is explicitly exempt from the scene requirement. It should be treated as a sensor/component XML with recommended path `realsense_d435i/d435i.xml`, not as a full robot scene with plane and lighting. If the user wants to mount it on another robot, route to `model-editing`.

## Category is unknown

Some top-level XML directories are present but absent from the gallery `MODEL_MAP`. In the bundled snapshot these are:

- `dynamixel_2r`
- `franka_fr3_v2`
- `rainbow_robotics_rby1`
- `robotiq_2f85_v4`
- `robotstudio_so101`
- `tetheria_aero_hand_open`
- `trossen_wxai`

Catalog response:

1. Say `unknown in gallery` rather than assigning a category from the name.
2. Use README title, XML names, and `scene*.xml` files for selection.
3. If the user is maintaining the repo, route to `contribution-maintenance` to update gallery/category metadata.

## The bundled catalog may be stale

Symptoms:

- user-provided checkout contains directories not in `model-index.json`;
- model XML lists differ from the bundled snapshot;
- gallery categories changed;
- minimum MuJoCo version or license text changed.

Safe refresh command:

```bash
python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --json /tmp/menagerie-catalog.json
python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --markdown
```

The script is read-only unless an explicit output path is supplied. It parses `generate_gallery.py` and `test/model_dir_test.py` with `ast`; it does not import MuJoCo or execute repository scripts.

## Multiple scene XMLs exist

Choose by name and task:

- MJX tasks: `scene_mjx.xml` or `scene_hfield_mjx.xml`.
- Handed hands: `scene_left.xml` or `scene_right.xml`.
- Control variants: `scene_position.xml`, `scene_velocity.xml`, or `scene_motor.xml`.
- Environment variants: `scene_arm.xml`, `scene_base.xml`, `scene_box.xml`, `scene_locomotion.xml`, or `scene_manipulation.xml`.
- If no variant is requested, use `recommended_load_xmls` from the index, then `scene.xml` if present.

If a selected scene fails to compile or has missing assets, route to `model-loading`.

## MJX is absent for the requested model

Catalog response:

1. Check `mjx_xmls` in `model-index.json`.
2. If empty, state that the snapshot lists no MJX-specific XML for that directory.
3. Provide the non-MJX fallback, usually `<dir>/scene.xml`, or the directory's `recommended_load_xmls` if a gallery override exists.
4. Do not promise MJX compatibility from a normal MJCF file.

For quadrupeds, the MJX-capable entries in this snapshot are `anybotics_anymal_c`, `google_barkour_v0`, `google_barkour_vb`, and `unitree_go2`.

## README minimum MuJoCo version is missing

Four snapshot directories did not expose a `Requires MuJoCo X.Y.Z or later` line in README evidence: `dynamixel_2r`, `rainbow_robotics_rby1`, `robot_soccer_kit`, and `tetheria_aero_hand_open`.

Catalog response:

- Report `minimum MuJoCo version not stated in indexed README evidence`.
- Do not guess from neighboring models.
- If the user needs runtime compatibility, route to `model-loading` for a compile smoke test against the user's MuJoCo version.

## README, LICENSE, or CHANGELOG is missing

The model directory structural test expects all three files for every model directory. Catalog response:

1. Report which boolean field is false: `has_readme`, `has_license`, or `has_changelog`.
2. Treat `license_spdx: null` as license file missing; treat `license_spdx: Unknown` as present but not recognized by the gallery heuristic.
3. Route any fix or validation to `contribution-maintenance`.

## License label differs from expectations

The catalog uses the same simple SPDX heuristic as the gallery generator. It is useful for inventory, not legal review.

If the license is `Unknown` or the user changed license text:

- identify the model directory and current `license_spdx` field;
- route to `contribution-maintenance` for license regeneration/check workflow;
- do not rewrite license text from this sub-skill.

## `robot_descriptions` name does not match Menagerie directory

Catalog response:

1. Identify the Menagerie-relative XML first, e.g. `franka_emika_panda/scene.xml` or `franka_emika_panda/hand.xml`.
2. Mention that `robot_descriptions` module names can differ; the README example uses `panda_mj_description` for Franka Panda.
3. Route import/module details to `model-loading`.

## Asset folder is missing or nonstandard

Most model directories use `assets/`; `iit_softfoot` uses `meshes/`. The index lists `asset_dirs` and `asset_file_extensions` to help detect layout differences. If an XML compile fails because meshes moved or were not copied with the XML, route to `model-loading` for path-resolution debugging.
