---
name: model-catalog
description: "Choose MuJoCo Menagerie model directories, scene XMLs, variants,
  MJX XMLs, categories, and metadata from a bundled catalog."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Catalog

Use this sub-skill when the task is to identify or inventory MuJoCo Menagerie models before loading or editing them.

## Use this for

- Choosing the relative XML path for a named robot, gripper, hand, sensor, or model directory.
- Listing model directories by gallery category such as quadrupeds, arms, hands/end-effectors, mobile manipulators, humanoids, drones, or miscellaneous assets.
- Finding MJX-specific XMLs and a non-MJX fallback XML.
- Checking whether a directory has README, LICENSE, CHANGELOG, scene XMLs, asset folders, and minimum MuJoCo version evidence.
- Producing a model inventory from the bundled snapshot or from a user-supplied Menagerie checkout.

## Do not use this for

- Compiling XMLs, opening viewers, stepping simulations, resolving mesh-load errors, or interpreting MuJoCo warnings. Route those tasks to `model-loading`.
- Editing MJCF, composing arms and grippers, generating mirrored hands, or changing MJX variants. Route those tasks to `model-editing`.
- Running maintainer checks, formatting XML, regenerating licenses, or rendering the gallery. Route those tasks to `contribution-maintenance`.

## Runtime references

- Read `references/catalog-reference.md` for selection rules, category summaries, MJX guidance, and edge cases.
- Read `references/model-index.json` for the compact generated catalog snapshot.
- Read `references/troubleshooting.md` when a directory has missing metadata, no scene XML, unknown category, stale catalog data, or `robot_descriptions` naming ambiguity.
- Use `scripts/inspect_model_catalog.py` to inspect a current Menagerie checkout without importing MuJoCo or executing repository scripts.

## Selection workflow

1. Normalize the user request into one of: named model, category search, MJX query, metadata/license query, or full inventory.
2. Look up the directory or gallery entry in `references/model-index.json` first. Return repository-relative paths such as `unitree_go2/scene.xml`, never absolute local checkout paths.
3. For ordinary simulation or preview, prefer `recommended_load_xmls` from the index. These encode gallery preview overrides such as hand-only XMLs, `scene_left.xml`, `scene_position.xml`, and the `realsense_d435i/d435i.xml` sensor asset.
4. For MJX, prefer `scene_mjx.xml` or other `*mjx*.xml` scene files when present; otherwise state that no MJX XML is listed and provide the normal scene fallback.
5. If the user needs to verify the live checkout rather than the bundled snapshot, run:

   ```bash
   python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --markdown
   python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --json /tmp/menagerie-catalog.json
   ```

6. Stop at catalog-level advice. If the next action is actually loading, debugging, editing, or checking contributions, route to the owning sub-skill named above.

## Output contract

When answering catalog questions, include the smallest useful set of fields:

- model directory and display name;
- category or `unknown in gallery`;
- recommended XML path(s);
- MJX XML path(s) and non-MJX fallback when relevant;
- minimum MuJoCo version if the per-model README stated one;
- README/LICENSE/CHANGELOG presence and SPDX license heuristic when relevant;
- any caveat, such as no standalone `scene*.xml` for sensor-only `realsense_d435i`.
