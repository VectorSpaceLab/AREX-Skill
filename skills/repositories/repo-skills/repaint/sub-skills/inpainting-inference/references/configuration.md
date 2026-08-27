# Inpainting configuration

This doc is the inpainting-specific companion to `../../../references/configuration.md`.
It focuses on the three supported config families, the fields that the runtime actually reads, and the edits needed for custom images and masks.

## Supported config families

| Family | Example family | Model / guidance setup | Dataset style |
| --- | --- | --- | --- |
| Face | face-family config | `model_path: ./data/pretrained/celeba256_250000.pt`, `class_cond: false`, no classifier path | Aligned face images and face masks |
| ImageNet | `test_inet256_*` family | `model_path: ./data/pretrained/256x256_diffusion.pt`, `classifier_path: ./data/pretrained/256x256_classifier.pt`, `class_cond: true`, `use_fp16: true` | Diverse ImageNet-style content |
| Places2 | `test_p256_*` family | `model_path: ./data/pretrained/places256_300000.pt`, `class_cond: false`, no classifier path | Natural-image scenes and masks |

## Fields the inference path reads

| Key | How the runtime uses it |
| --- | --- |
| `model_path` | Loaded before sampling with `dist_util.load_state_dict` |
| `classifier_path` | Optional; loaded only when `classifier_scale > 0` and the path is present |
| `class_cond` | Switches the model call between class-conditioned and unconditional inputs |
| `cond_y` | Optional fixed ImageNet class label; if omitted, the script samples random labels when `class_cond: true` |
| `use_fp16` | Converts the model to fp16 before sampling |
| `use_ddim` | Reserved in this checkout; the bundled helper treats `true` as unsupported because the snapshot does not expose a DDIM sampler |
| `clip_denoised` | Clips predicted `x_0` to `[-1, 1]` |
| `show_progress` | Enables the tqdm progress bar |
| `timestep_respacing` | Sets the effective number of diffusion steps |
| `schedule_jump_params` | Controls the resampling schedule; use schedule-visualization for tuning |
| `data.eval.<name>.mask_loader` | Must be `true` to activate the inpainting loader |
| `data.eval.<name>.gt_path` | Ground-truth image directory |
| `data.eval.<name>.mask_path` | Keep-mask directory |
| `data.eval.<name>.image_size` | Target square size for center-crop / resize |
| `data.eval.<name>.batch_size` | Loader batch size |
| `data.eval.<name>.max_len` | Number of examples to emit at most |
| `data.eval.<name>.offset` | Skip the first N sorted pairs |
| `data.eval.<name>.random_crop` | Must stay `false`; the loader does not implement random crop |
| `data.eval.<name>.random_flip` | Optional augmentation; the sample configs keep it `false` |
| `data.eval.<name>.return_dataloader` | Keep `true` for the example pipeline |
| `data.eval.<name>.return_dict` | Keep `true`; the example pipeline expects `GT`, `GT_name`, and `gt_keep_mask` |
| `data.eval.<name>.paths.srs` | Inpainted outputs |
| `data.eval.<name>.paths.lrs` | Masked inputs |
| `data.eval.<name>.paths.gts` | Copied ground-truth images |
| `data.eval.<name>.paths.gt_keep_masks` | Saved keep-mask visualizations |

## Pairing and mask semantics

- The loader scans `gt_path` and `mask_path` recursively.
- Pairing follows sorted order, not filename matching.
- The loader rescales GT images to `[-1, 1]` and masks to `[0, 1]`.
- The documented mask convention is **known = 255, unknown = 0**.
- Because the mask is divided by `255.0`, non-255 known pixels become soft weights instead of a hard binary keep region.

## Custom-image recipe

1. Copy the closest sample config.
2. Change `model_path` if you are using a different pretrained checkpoint.
3. Point `data.eval.<name>.gt_path` and `mask_path` at your own directories.
4. Keep `mask_loader: true`, `return_dict: true`, `return_dataloader: true`, and `random_crop: false`.
5. Keep the file counts aligned and the sorted order stable.
6. Run the bundled helper with `--dry_run` before you launch a full inference pass.

## Example-only metadata

These keys appear in the shipped YAML files but do not control the current inference path:

- `num_samples`
- `n_jobs`
- `latex_name`
- `method_name`
- `lr_kernel_n_std`
- `print_estimated_vars`
- `ds_conf.name`

Treat them as labels or provenance notes rather than runtime switches.
