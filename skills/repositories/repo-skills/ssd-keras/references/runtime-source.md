# Bundled Runtime Source

The generated skill bundles a self-contained copy of the Python runtime modules that the smoke scripts need. The smoke helpers resolve imports from `runtime-src/` inside the skill tree, so they do not depend on the original repository checkout.

## Bundled module layout

- `runtime-src/bounding_box_utils/`
- `runtime-src/data_generator/`
- `runtime-src/eval_utils/`
- `runtime-src/keras_layers/`
- `runtime-src/keras_loss_function/`
- `runtime-src/misc_utils/`
- `runtime-src/models/`
- `runtime-src/ssd_encoder_decoder/`

## Why this exists

The repository's workflow scripts need the live package modules to inspect signatures, build models, create synthetic batches, decode predictions, and run evaluation smokes. Copying the small Python source tree into the skill keeps those scripts self-contained and prevents them from importing from a local checkout path.

## License note

The bundled Python source is copied from the Apache-2.0-licensed repository snapshot recorded in `references/repo-provenance.md`. The original `LICENSE.txt` is included as `runtime-src/LICENSE.txt`, and `runtime-src/README.md` provides a local self-contained anchor for source docstrings that mention `README.md`.

## What is not bundled here

- Large example images
- Notebook files
- Training summaries
- External pretrained weights
- Repo-local review or verification artifacts
