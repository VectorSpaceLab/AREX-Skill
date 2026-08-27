# Gallery Workflow

The Menagerie README model table is generated. Do not hand-edit rows inside the generated model section. Use this reference to decide when to run gallery rendering and what to inspect afterward.

## What `make gallery` does

From a Menagerie checkout root:

```bash
make gallery
```

The target runs:

```bash
uv run --no-project generate_gallery.py
```

The gallery script:

1. Defines a `MODEL_MAP` from `model_dir/xml_stem` entries to model categories.
2. Sorts gallery XMLs by category and XML stem.
3. Compiles each mapped XML with MuJoCo.
4. Applies gallery visual settings and auto-camera logic, plus per-model keyframe/camera/preview overrides where needed.
5. Renders transparent PNG thumbnails into top-level `assets/`.
6. Detects a compact license label from each model directory's `LICENSE`.
7. Rewrites only the README section between the generated model markers.

The generated README rows include preview link target, display name, DoF count, and model license link text.

## Why full gallery rendering is not a default check

Gallery rendering is write-heavy and dependency-heavy. It can rewrite many PNG thumbnails and the README gallery even for small category/camera/script changes. It requires MuJoCo, Python image/rendering dependencies, and a runtime environment that can render offscreen.

Use targeted formatter/license/structural/loading checks for ordinary XML or license edits. Run `make gallery` when the expected output includes README gallery rows or thumbnails.

## Run gallery when

- A model is added to or removed from the README gallery.
- `generate_gallery.py` changes.
- `MODEL_MAP`, category ordering, display-name overrides, preview overrides, keyframe overrides, camera overrides, or gallery visual settings change.
- A gallery-facing XML changes in a way that should alter thumbnail pose, DoF count, preview target, or display name.
- A model license changes and the README gallery license label should update.
- The generated README model section was edited or appears stale.

## Usually skip gallery when

- Only non-gallery docs changed.
- XML formatting changed but geometry, DoFs, display name, preview target, and category are unchanged.
- A license file changed but the README table entry is not in the gallery or the rendered table is not part of the requested validation budget.
- The user explicitly asks for a quick targeted check and no generated-gallery files are part of the change.

State the skip explicitly: "Skipped `make gallery` because no gallery-facing files or metadata changed."

## New model directory gallery checklist

For a model that should appear in the README gallery:

1. Choose the gallery key as `model_dir/xml_stem` and route category judgment to `model-catalog` if uncertain.
2. Add that key to the gallery model map with the correct category.
3. Ensure the model directory has a readable `README.md`; the gallery extracts the first Markdown heading and strips suffixes such as "Description (MJCF)".
4. Add a display-name override only when the README title is missing, too verbose, or describes a different variant.
5. Ensure default preview path `model_dir/scene.xml` is correct; add a preview override when a different scene or direct XML should be opened.
6. Add a keyframe override when the default pose is poor; add a camera override only when auto-camera fails.
7. Ensure `LICENSE` uses text detectable as Apache-2.0, BSD-3-Clause-Clear, BSD-3-Clause, BSD-2-Clause, MIT, or expect `Unknown` in the generated table.
8. Run `make gallery` and inspect the diff in README and generated PNG files.
9. Run selected loading validation for the gallery XML if rendering or compile fails.

## Validation after `make gallery`

After rendering:

```bash
git diff -- README.md assets/
```

Check that:

- only the generated model section changed in README unless other docs were intentionally edited
- new/changed thumbnails correspond to the intended model entries
- live preview paths point at the intended `scene*.xml` or direct model XML
- category order remains consistent with the gallery categories
- DoF counts look plausible for the model type
- license labels match the model directory `LICENSE`

Then run the normal contribution checks:

```bash
make check
make test   # or selected loading/structural checks if the user asked for a scoped plan
```

## Failure triage

- **MuJoCo compile failure:** route the specific XML to `model-loading`; inspect include paths, mesh paths, required MuJoCo version, and scene-vs-model selection.
- **Rendering/OpenGL failure:** confirm the environment can import MuJoCo and render offscreen; if not, document that gallery rendering is blocked by runtime rendering support rather than by the model edit itself.
- **Missing README markers:** restore the generated section markers before rerunning gallery.
- **Unexpected `Unknown` license:** inspect the model `LICENSE` text and the gallery license detector expectations.
- **Bad thumbnail framing:** prefer keyframe or camera override in the gallery script after verifying the model compiles and the visual issue is reproducible.
