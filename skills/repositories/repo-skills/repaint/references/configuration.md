# Shared configuration terms

These terms are shared by the RePaint inpainting and schedule workflows.
For inpainting-specific examples, see `../sub-skills/inpainting-inference/references/configuration.md`.
For resampling-shape questions, use the schedule-visualization sub-skill.

## Core runtime keys

| Key | Meaning | Runtime note |
| --- | --- | --- |
| `model_path` | Diffusion checkpoint loaded before sampling | Required for every inference run |
| `classifier_path` | Optional classifier checkpoint for classifier guidance | Used only when `classifier_scale > 0` **and** the path is set |
| `class_cond` | Enables class-conditioned model inputs | ImageNet-style configs set this to `true` |
| `cond_y` | Optional fixed class id | If omitted while `class_cond: true`, the sampler draws random labels |
| `schedule_jump_params` | Resampling schedule parameters | Tuning details belong in schedule-visualization |
| `image_size` | Square resolution for the loader and model | GT and mask are center-cropped / resized to this value |
| `data.eval.<name>.mask_loader` | Switches the eval loader to the inpainting path | Must stay `true` for RePaint inference |
| `data.eval.<name>.gt_path` | Directory of ground-truth images | Paired with `mask_path` by sorted recursive listing |
| `data.eval.<name>.mask_path` | Directory of keep masks | Masks are read as RGB, then scaled by `1/255` |
| `data.eval.<name>.paths.srs` | Output directory for inpainted samples | Created automatically when the run writes outputs |
| `data.eval.<name>.paths.lrs` | Output directory for masked inputs | Same basenames as the GT files |
| `data.eval.<name>.paths.gts` | Output directory for copied GT images | Optional; if omitted, GT copies are skipped |
| `data.eval.<name>.paths.gt_keep_masks` | Output directory for written keep masks | Useful for checking mask polarity and coverage |
| `batch_size` | Loader batch size | Read from the selected eval entry |
| `max_len` | Sample cap for the eval loader | Limits how many pairs are produced |
| `offset` | Skip the first N sorted pairs | Useful when resuming from the middle of a dataset |
| `random_crop` | Crop mode requested by the dataset entry | The shipped inpainting loader does not implement random crop |
| `random_flip` | Optional horizontal flip | Example configs keep it false for deterministic runs |
| `return_dataloader` | Return a PyTorch DataLoader | Example inference expects `true` |
| `return_dict` | Return dicts with `GT`, `GT_name`, `gt_keep_mask` | Example inference expects `true` |

## Example family mapping

| Family | Typical config | Notes |
| --- | --- | --- |
| Face | face-family config | Aligned face example with `class_cond: false` |
| ImageNet | `test_inet256_*` family | Class-conditioned runs with classifier guidance available |
| Places2 | `test_p256_*` family | Diverse natural-image runs without classifier guidance |

## Metadata-only keys in the sample configs

The current inference path does not consume these keys directly:

- `num_samples`
- `n_jobs`
- `latex_name`
- `method_name`
- `lr_kernel_n_std`
- `print_estimated_vars`
- `ds_conf.name` (passed through as a label, not used by `load_data_inpa`)

Keep them as provenance metadata, but do not rely on them to change sampling behavior.
