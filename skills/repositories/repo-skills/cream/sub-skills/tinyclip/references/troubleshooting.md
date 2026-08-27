# TinyCLIP Troubleshooting

## Missing package or editable install

**Symptom:** `ModuleNotFoundError: open_clip` or missing auxiliary dependencies.

**Likely cause:** The package was not installed into the inspection environment.

**Recovery:**

- Install the package with `python -m pip install -e <tinyclip-checkout>` or the equivalent project install path.
- Use `../scripts/inspect_tinyclip_models.py` to confirm the package imports cleanly.

## Checkpoint not found

**Symptom:** Evaluation says the checkpoint does not exist or cannot be loaded.

**Likely cause:** The user pointed at the wrong model-zoo file or a stale local path.

**Recovery:**

- Re-check the model name in `references/api-reference.md`.
- Make sure the checkpoint matches the chosen TinyCLIP variant or pruning path.

## ImageNet layout errors

**Symptom:** Zero-shot evaluation cannot find `imagenet-val` or the dataset split is wrong.

**Likely cause:** The validation root does not contain a standard ImageNet-1k layout.

**Recovery:**

- Run `../../../scripts/check_dataset_layout.py --kind imagenet1k --root <imagenet-root>`.
- Pass that same root to `--imagenet-val`.

## Pruning flag confusion

**Symptom:** Auto-weight-inheritance checkpoints are loaded with the wrong model name.

**Likely cause:** The auto checkpoints require `ViT-B-32` plus pruning flags, not the final compressed model name.

**Recovery:**

- Use the auto checkpoint command shape in `references/workflows.md`.
- Keep `--prune-image` and `--prune-text` together when evaluating those checkpoints.

## Stage / multi-node launch issues

**Symptom:** The training stage fails before the first epoch.

**Likely cause:** The multi-node environment variables or node count are missing.

**Recovery:**

- Treat the stage workflows as advanced and make sure the data loader and distributed settings match the doc.
- If you only need a reproducible command, use the bundled command-builder script instead of the original stage shell wrappers.
