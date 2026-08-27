# Data Preparation Troubleshooting

## Purpose

Read this when raw metadata validation, latent extraction, or processed-dataset checks fail.

## Raw metadata list fails validation

**Symptoms**

- `meta_file.list` cannot be opened
- a listed JSON file is missing
- `video_path` or `raw_caption.long caption` is missing

**Fix**

- Fix the raw JSON schema first.
- From the checkout root, re-run `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode raw --meta-file-list ...`.

## `decord` cannot read a video

**Symptoms**

- `decord.VideoReader` errors
- invalid codec or unreadable path

**Fix**

- Confirm that `video_path` resolves from the process working directory.
- Use a small known-readable `.mp4` fixture to isolate codec issues.
- Do not proceed to training with silently skipped videos.

## VAE checkpoint missing

**Symptoms**

- `VAE checkpoint not found`
- `pytorch_model.pt` missing under the VAE folder

**Fix**

- Run `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode extraction` from the checkout root.
- Read [`../../../references/checkpoints.md`](../../../references/checkpoints.md).

## Everything is skipped

**Symptom**

- Extraction prints progress but writes no new `.npy` files.

**Cause**

The extractor skips videos when `{output_base_dir}/{video_id}.npy` already exists.

**Fix**

- Use a fresh output directory or remove the intended stale cache files after confirming they are safe to replace.

## Processed JSON does not train

**Symptoms**

- training loader fails on `latent_shape`
- `.npy` path in processed JSON is stale
- `latent_shape` has fewer than five dimensions

**Fix**

- Validate the processed layout with `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode processed --json-dir ...`.
- If the checker reports a stale `npy_save_path` or malformed `latent_shape`, regenerate the latent cache and processed JSONs before training.

## Debug Order

Run from `$CHECKOUT_ROOT`; `$SKILL_ROOT` is the generated-skill directory:

1. `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode raw --meta-file-list ...`
2. `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode extraction`
3. `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/run_hyvae_extract.py" --repo-root "$CHECKOUT_ROOT" --dry-run ...`
4. run extraction
5. `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode processed --json-dir ...`
