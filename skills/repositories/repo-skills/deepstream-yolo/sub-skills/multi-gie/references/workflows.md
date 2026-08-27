# Multi-GIE workflow

The commands below assume the generated skill root is the current working directory.

## 1. Decide the pipeline shape

- `deepstream-app` can only use one primary GIE in the standard path.
- Additional detectors must become secondary GIEs unless the user is writing custom application code.

## 2. Scaffold the folder layout

Use the scaffold helper to create the duplicated layout from the bundled assets:

```bash
sub-skills/multi-gie/scripts/setup-multi-gie-tree.sh --count 2 --output-dir ./deepstream-yolo-multi-gie
```

This creates `gie1/`, `gie2/`, ... and copies the bundled parser source, configs, and labels into each folder. It also prefixes model/config/library paths with `gieN/`, sets per-folder `gie-unique-id` and `process-mode`, injects default secondary `operate-on-*` keys, and updates `YOLOLAYER_PLUGIN_VERSION` for each copied parser tree.

## 3. Update the duplicated configs

For each GIE folder, review the helper-generated defaults:

- each path field should point through `gieN/`,
- each GIE should have a unique `gie-unique-id`,
- `process-mode=1` is used for `gie1` and `process-mode=2` for later GIEs,
- secondary GIEs default to `operate-on-gie-id=1`, and
- `operate-on-class-ids=0` can be widened or removed if the secondary detector should run on more classes.

## 4. Change the plugin version

The helper updates each copied `yoloPlugins.h` so every detector has a distinct `YOLOLAYER_PLUGIN_VERSION`. Recheck this file if you manually change the scaffold.

## 5. Run and verify

Point `deepstream_app_config.txt` at the duplicated primary and secondary configs, then launch `deepstream-app`.

## 6. Fix the usual errors

- If the app loads only one detector, recheck the `secondary-gieN` section names and GIE IDs.
- If an engine appears in the wrong place, move it back to the owning `gieN/` folder.
- If plugin loading fails, confirm the version bump in every copied `yoloPlugins.h`.