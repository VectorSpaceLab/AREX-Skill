# Planning and Preprocessing Troubleshooting

## Dataset integrity fails

Likely causes:

- Raw dataset ID or dataset folder name does not match the nnU-Net convention.
- `dataset.json` has wrong `channel_names`, `labels`, `numTraining`, or `file_ending`.
- Image/label shapes differ, labels contain unexpected values, or cases are missing modalities.
- Environment variables for nnU-Net raw/preprocessed/results roots are not set in the shell that runs the command.

Recommended response:

1. Route raw data layout questions to `data-preparation`.
2. Run `nnUNetv2_plan_and_preprocess -d DATASET_ID --verify_dataset_integrity` only after raw layout is corrected.
3. Use `--clean` if the dataset changed after a fingerprint was already written.

## Fingerprint is stale

Rerun fingerprint extraction with `--clean` when any of these changed:

- training cases, labels, spacings, image contents, or file endings
- `dataset.json` channel names or label metadata
- fingerprint extractor class
- dataset conversion or cropping-relevant raw input behavior

Command pattern:

```bash
nnUNetv2_extract_fingerprint -d DATASET_ID --verify_dataset_integrity --clean
nnUNetv2_plan_experiment -d DATASET_ID
nnUNetv2_preprocess -d DATASET_ID -c 2d 3d_fullres
```

## Plans changed but preprocessing is stale

If the plans file changed in a way that affects prepared data, rerun preprocessing for every affected configuration. Examples include target spacing, preprocessor name, normalization scheme, resampling functions, or a changed `data_identifier`.

Command pattern:

```bash
nnUNetv2_preprocess -d DATASET_ID -plans_name PLANS_NAME -c CONFIG_NAME -np WORKERS
```

Do not assume old preprocessed folders are compatible just because the configuration name is unchanged. Check `data_identifier` and the data-affecting fields in the plans file.

## Target spacing or planner changed

Changing `-overwrite_target_spacing`, `-pl`, or `-gpu_memory_target` changes planning assumptions. Use a new plans identifier for experimental variants:

```bash
nnUNetv2_plan_experiment -d DATASET_ID -pl PLANNER -gpu_memory_target 24 -overwrite_plans_name MY_PLANS_24G
nnUNetv2_preprocess -d DATASET_ID -plans_name MY_PLANS_24G -c 3d_fullres
```

Target spacing overrides are limited to `3d_fullres` and `3d_cascade_fullres`. If low-resolution planning changes as a consequence, inspect the generated configurations before preprocessing.

## Wrong configuration choice

Symptoms:

- `nnUNetv2_preprocess` prints that a configuration is not found and skips it.
- Training later cannot find the expected preprocessed data folder.
- A cascade stage is requested as if it had independent preprocessed data.

Fix:

- Inspect `configurations` in the plans JSON and choose exact keys.
- Preprocess `2d`, `3d_fullres`, or `3d_lowres` when available.
- Do not preprocess `3d_cascade_fullres` unless a plans variant explicitly gives it independent prepared data; it usually reuses `3d_fullres`.
- Pass the same plans identifier to preprocessing and later training/prediction.

## Workers exhaust RAM

Symptoms include killed worker processes, stalled preprocessing, or errors indicating a background worker disappeared. Resampling large 3D cases is memory intensive.

Fix:

- Reduce `-np`, especially for `3d_fullres`.
- Prefer `--no_pbar` for scheduler logs but do not expect it to reduce memory use substantially.
- Run one configuration at a time to isolate the memory-heavy stage.
- Start with `-np 1` or `-np 2` for very large volumes, then increase after success.

## Missing nnU-Net paths

Planning and preprocessing require nnU-Net environment variables in the process environment:

- `nnUNet_raw`
- `nnUNet_preprocessed`
- `nnUNet_results`

If commands cannot find datasets or outputs appear in unexpected locations, check these variables in the same shell or job script that runs nnU-Net.

## API used for combined workflow

There is no combined `plan_and_preprocess` Python API helper. The all-in-one workflow is the `nnUNetv2_plan_and_preprocess` CLI. In Python, call the separate functions in order: `extract_fingerprints`, `plan_experiments`, then `preprocess`.

## Rerun decision checklist

- Raw dataset changed: rerun integrity check, fingerprint extraction with `--clean`, planning, and preprocessing.
- Fingerprint fresh, plans missing: run `nnUNetv2_plan_experiment`, then preprocessing.
- Plans fresh, preprocessed arrays stale or deleted: run `nnUNetv2_preprocess` only.
- Only batch size changed while reusing the same `data_identifier`: preprocessing is usually not needed.
- Target spacing, normalization, resampling, preprocessor, or `data_identifier` changed: rerun preprocessing for affected configurations.
