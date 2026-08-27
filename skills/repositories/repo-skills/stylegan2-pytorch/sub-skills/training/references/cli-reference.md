# CLI Reference

## When to read

Read this when converting a user's training or generation request into exact
`stylegan2_pytorch` flags. Defaults were verified from the installed package's
`train_from_folder` signature and Fire help.

## Fire spelling note

Fire help displays underscore names such as `--image_size`. The README examples
also use hyphenated names such as `--image-size`. When debugging parser issues,
prefer the exact underscore spelling shown by:

```bash
stylegan2_pytorch -- --help
```

## Paths and project identity

| Flag | Default | Use |
| --- | --- | --- |
| `--data` | `./data` | Image folder to train from; recursive `.jpg`, `.jpeg`, `.png`. |
| `--results_dir` | `./results` | Base directory for generated images, GIFs, and FID score file. |
| `--models_dir` | `./models` | Base directory for checkpoints and `.config.json`. |
| `--name` | `default` | Project/run name; subdirectory under results/models. |
| `--new` | `False` | Clear current project outputs/checkpoints before training. |
| `--load_from` | `-1` | Checkpoint number to load; `-1` means latest available. |

## Model size, data, and training loop

| Flag | Default | Use |
| --- | --- | --- |
| `--image_size` | `128` | Must be a power of two. Larger sizes need more memory. |
| `--network_capacity` | `16` | Increases model capacity and memory use. |
| `--fmap_max` | `512` | Maximum feature-map count. |
| `--transparent` | `False` | Use RGBA data and write `.png` outputs. |
| `--batch_size` / `-b` | `5` | Batch size before multi-GPU splitting. |
| `--gradient_accumulate_every` | `6` | Number of gradient accumulation micro-steps. |
| `--num_train_steps` | `150000` | Total trainer steps. |
| `--learning_rate` | `0.0002` | Generator learning rate (`Trainer` stores it as `lr`). |
| `--lr_mlp` | `0.1` | Mapping-network LR multiplier. |
| `--ttur_mult` | `1.5` | Discriminator LR multiplier. |
| `--num_workers` | `None` | DataLoader workers; defaults to CPU count except DDP uses 0. |
| `--save_every` | `1000` | Checkpoint interval and checkpoint-number denominator. |
| `--evaluate_every` / `-e` | `1000` | Sample image evaluation interval. |
| `--seed` | `42` | Seed set in DDP worker path. |

## Generation flags

| Flag | Default | Use |
| --- | --- | --- |
| `--generate` | `False` | Load checkpoint and write generated still samples. |
| `--num_generate` | `1` | Number of sample grids to generate in `--generate` mode. |
| `--generate_interpolation` | `False` | Load checkpoint and write interpolation GIF. |
| `--interpolation_num_steps` | `100` | Number of interpolation frames. |
| `--save_frames` | `False` | Save each GIF frame as an image directory. |
| `--num_image_tiles` | `8` | Rows/columns in generated grids; total images is tiles squared. |
| `--trunc_psi` | `0.75` | Truncation strength; lower is sharper but less varied. |
| `--mixed_prob` | `0.9` | Probability of mixed-style generation during training. |

## Regularization, augmentation, and experimental flags

| Flag | Default | Use |
| --- | --- | --- |
| `--fp16` | `False` | Requires NVIDIA Apex; otherwise raises an assertion. |
| `--no_pl_reg` | `False` | Disable path-length regularization. |
| `--rel_disc_loss` | `False` | Use relativistic discriminator loss. |
| `--dual_contrast_loss` | `False` | Use dual contrastive loss. |
| `--cl_reg` | `False` | Use contrastive discriminator regularization; not transparent/multi-GPU safe in this source. |
| `--fq_layers` | `[]` | Layers with feature quantization, e.g. `'[1,2]'`. |
| `--fq_dict_size` | `256` | Vector-quantization dictionary size. |
| `--attn_layers` | `[]` | Layers with self-attention, e.g. `'[1,2]'`. |
| `--no_const` | `False` | Learn the 4x4 block from style vector instead of a constant. |
| `--aug_prob` | `0.0` | Differentiable augmentation probability before discriminator. |
| `--aug_types` | `['translation', 'cutout']` | DiffAugment type list; include no spaces inside list strings. |
| `--dataset_aug_prob` | `0.0` | Dataset transform random-resized-crop probability. |
| `--top_k_training` | `False` | Use top-k generator training. |
| `--generator_top_k_gamma` | `0.99` | Top-k decay schedule. |
| `--generator_top_k_frac` | `0.5` | Minimum top-k fraction. |

Supported `--aug_types` keys from the source augmentation map are:
`brightness`, `lightbrightness`, `contrast`, `lightcontrast`, `saturation`,
`lightsaturation`, `color`, `lightcolor`, `offset`, `offset_h`, `offset_v`,
`translation`, and `cutout`.

## Optional evaluation, logging, and distributed flags

| Flag | Default | Use |
| --- | --- | --- |
| `--multi_gpus` | `False` | Spawn one process per visible CUDA device using NCCL. |
| `--calculate_fid_every` | `None` | Every N steps, calculate FID; requires `pytorch-fid`. |
| `--calculate_fid_num_images` | `12800` | Generated/real image count for FID batches. |
| `--clear_fid_cache` | `False` | Clear cached real FID images before recalculating. |
| `--log` | `False` | Create an Aim tracking session. |

## Command-building checklist

1. Decide whether the command trains, resumes, restarts, generates stills, or
   generates interpolation.
2. Choose stable `--name`, `--results_dir`, and `--models_dir` paths.
3. For new/restart training, validate data and choose `--image_size`, batch,
   accumulation, and model capacity.
4. For generation, confirm a checkpoint exists and use the same project layout.
5. Add optional FID/logging/fp16/multi-GPU flags only when dependencies and
   backend constraints are explicit.
