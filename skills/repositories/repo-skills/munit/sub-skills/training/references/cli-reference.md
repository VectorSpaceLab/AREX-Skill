# Training CLI and config reference

## `train.py` arguments

| Argument | Default | Meaning | Notes |
|---|---:|---|---|
| `--config` | `configs/edges2handbags_folder.yaml` | YAML experiment config. | The filename stem becomes the model name for logs, outputs, and checkpoints. |
| `--output_path` | `.` | Root directory for run artifacts. | Training writes `logs/<model_name>` and `outputs/<model_name>` below this root. |
| `--resume` | off | Resume from the latest checkpoint in the run output directory. | Requires generator, discriminator, and optimizer checkpoint files. |
| `--trainer` | `MUNIT` | Trainer implementation. | Must be exactly `MUNIT` or `UNIT`; other values exit immediately. |

Safe dry-run equivalent:

```bash
python scripts/munit_train_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/demo_edges2handbags_folder.yaml \
  --output-path runs/demo_edges2handbags \
  --trainer MUNIT
```

## Trainer selection

### `MUNIT`

Use `MUNIT` for bundled configs and multimodal style sampling.

Training behavior distilled from `MUNIT_Trainer`:

- Builds an AdaIN generator for domain A and one for domain B.
- Builds a multi-scale discriminator for each domain.
- Reads `gen.style_dim` and creates fixed random style tensors with shape `[display_size, style_dim, 1, 1]` on CUDA for sampling.
- `dis_update(x_a, x_b, config)` samples random style tensors, encodes content, decodes cross-domain fakes, computes adversarial discriminator losses against real images, backpropagates, and steps the discriminator optimizer.
- `gen_update(x_a, x_b, config)` computes within-domain reconstruction, style reconstruction, content reconstruction, optional cycle image reconstruction, adversarial generator losses, optional VGG perceptual losses, sums them with config weights, backpropagates, and steps the generator optimizer.
- `sample(x_a, x_b)` returns eight image groups for image-grid writing: original/reconstruction/two translations in both directions.

MUNIT-specific required loss/config keys include `recon_s_w`, `recon_c_w`, and `gen.style_dim`, in addition to the common keys.

### `UNIT`

Use `UNIT` only with a config designed for UNIT.

Training behavior distilled from `UNIT_Trainer`:

- Builds a VAE-style generator for each domain and a multi-scale discriminator for each domain.
- Does not use MUNIT style encoders or `gen.style_dim` for translation diversity.
- `dis_update(x_a, x_b, config)` encodes each domain, decodes cross-domain fakes, computes discriminator losses, backpropagates, and steps the discriminator optimizer.
- `gen_update(x_a, x_b, config)` computes image reconstruction, KL regularization, cycle reconstruction, cycle KL regularization, adversarial losses, optional VGG perceptual losses, sums them with config weights, backpropagates, and steps the generator optimizer.
- `sample(x_a, x_b)` returns six image groups: original/reconstruction/one translation in both directions.

UNIT-specific required loss keys include `recon_kl_w` and `recon_kl_cyc_w`. The bundled MUNIT demo configs do not include these keys, so switching only the CLI flag to `--trainer UNIT` is not enough.

## Common config surfaces

| Surface | Keys | Effect |
|---|---|---|
| Logging and snapshots | `image_save_iter`, `image_display_iter`, `snapshot_save_iter`, `log_iter`, `display_size` | Controls tensorboard scalar cadence, image-grid writes, HTML refresh rows, fixed display batch size, and checkpoint interval. |
| Iteration budget | `max_iter` | Training exits only when the global iteration counter reaches this value. |
| Loader behavior | `batch_size`, `num_workers`, `new_size` or `new_size_a`/`new_size_b`, `crop_image_height`, `crop_image_width` | Controls both domain loaders. Loader details and dataset validation belong to `../data-and-configuration/`. |
| Optimization | `lr`, `beta1`, `beta2`, `weight_decay`, `init` | Adam optimizer and weight initialization. Supported initialization names are `gaussian`, `kaiming`, `xavier`, `orthogonal`, and `default`. |
| Scheduler | `lr_policy`, `step_size`, `gamma` | `constant` means no scheduler; `step` uses StepLR with `step_size` and `gamma`. Other policies are not implemented. |
| GAN loss | `gan_w`, `dis.gan_type` | Weights adversarial losses. Discriminator GAN type supports `lsgan` and `nsgan`. |
| Reconstruction losses | `recon_x_w`, `recon_s_w`, `recon_c_w`, `recon_x_cyc_w` | MUNIT image, style, content, and optional cycle reconstruction weights. |
| UNIT KL losses | `recon_kl_w`, `recon_kl_cyc_w` | Required only when using `--trainer UNIT`. |
| Perceptual loss | `vgg_w` | If positive, the trainer attempts to load VGG weights from `<output_path>/models`; missing files can trigger a download attempt in the legacy helper. |
| Model capacity | `gen.dim`, `gen.mlp_dim`, `gen.style_dim`, `gen.n_downsample`, `gen.n_res`, `dis.dim`, `dis.n_layer`, `dis.num_scales` | Changes memory use, checkpoint compatibility, and architecture shape. Route architecture changes to `../model-internals/`. |

## Data-mode keys consumed by training

Training uses one of two data modes:

- Folder mode: `data_root` must contain `trainA`, `trainB`, `testA`, and `testB` image folders.
- List mode: `data_folder_train_a`, `data_list_train_a`, `data_folder_test_a`, `data_list_test_a`, `data_folder_train_b`, `data_list_train_b`, `data_folder_test_b`, and `data_list_test_b` must be present. List files contain image path lines relative to their paired data folder.

The training command builder can warn about obvious missing paths and display-size mismatches, but full data repair belongs to `../data-and-configuration/`.

## Utility methods that shape the CLI behavior

- `prepare_sub_folder(output_directory)` creates `<output_directory>/images` and `<output_directory>/checkpoints` and returns both directories.
- `write_2images(image_outputs, display_size, image_directory, postfix)` writes paired `gen_a2b_<postfix>.jpg` and `gen_b2a_<postfix>.jpg` grids.
- `write_html(output_directory + "/index.html", iterations, image_save_iter, "images")` regenerates an auto-refresh HTML page for saved image grids.
- `write_loss(iterations, trainer, writer)` logs every non-callable trainer attribute whose name contains `loss`, `grad`, or `nwd`.
- `get_model_list(checkpoint_dir, key)` lists checkpoint files containing the key and `.pt`, sorts lexicographically, and returns the last filename.
- `get_scheduler(optimizer, config, iterations=-1)` supports only `constant` and `step` learning-rate policies.
