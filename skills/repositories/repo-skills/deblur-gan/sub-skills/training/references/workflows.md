# DeblurGAN training workflows

## Recommended portable command

Use the bundled wrapper rather than the source `train.py` when you want a reproducible command line:

```bash
python scripts/run_training.py \
  --repo-root <path-to-DeblurGAN-checkout> \
  --dataroot <path-to-paired-data> \
  --name experiment_name \
  --model content_gan \
  --gan_type wgan-gp \
  --learn_residual \
  --resize_or_crop crop \
  --fineSize 256
```

## Common flags

The source option parser exposes the following important groups:

- Data and layout: `--dataroot`, `--dataset_mode`, `--which_direction`, `--resize_or_crop`, `--fineSize`, `--input_nc`, `--output_nc`, `--batchSize`, `--nThreads`.
- Model choice: `--model`, `--which_model_netG`, `--which_model_netD`, `--ngf`, `--ndf`, `--n_layers_D`, `--learn_residual`, `--gan_type`, `--norm`, `--no_dropout`.
- Optimization: `--lr`, `--beta1`, `--lambda_A`, `--lambda_B`, `--identity`, `--pool_size`, `--niter`, `--niter_decay`, `--epoch_count`, `--continue_train`, `--which_epoch`.
- Output and logging: `--checkpoints_dir`, `--name`, `--display_id`, `--display_port`, `--display_winsize`, `--display_single_pane_ncols`, `--display_freq`, `--print_freq`, `--save_latest_freq`, `--save_epoch_freq`, `--no_html`.

## Paper-faithful configuration notes

- The repository's README describes a conditional WGAN with gradient penalty plus perceptual loss.
- The source `train.py` overrides some defaults, including `gan_type`, `fineSize`, `resize_or_crop`, and `learn_residual`.
- The bundled wrapper keeps the user's chosen flags rather than copying the source overrides.
- For the paper-style path, keep `model=content_gan` and choose the loss family explicitly.

## Checkpoint layout

Training writes into:

```text
checkpoints/<name>/
  latest_net_G.pth
  latest_net_D.pth
  opt.txt
  web/
```

The `Visualizer` helper expects the checkpoint directory to exist before it is constructed.

## Smoke mode

Use smoke mode when you only need to confirm that the wiring is healthy:

- Keep the data fixture tiny.
- Set `--display_id 0` if visdom is unavailable.
- Cap the number of optimization steps with the wrapper's smoke option.
- Avoid long runs, because the wrapper is intended to be a portable control surface, not a benchmark harness.
