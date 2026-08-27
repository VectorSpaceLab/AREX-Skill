# CLI reference and verified defaults

This repository exposes two primary Python entry scripts in a target checkout: `train.py` for optimization and `test.py` for inference/result HTML generation. The parser is dynamic: base options load first, then the selected model injects defaults/options, then the selected dataset injects defaults/options.

## Base options shared by train and test

| Flag | Purpose / verified behavior |
| --- | --- |
| `--dataroot` | Required. Interpreted by `--dataset_mode`; validate with the data-preparation sub-skill. |
| `--name` | Experiment/checkpoint name. Training and testing use this to locate checkpoints under `--checkpoints_dir`. |
| `--checkpoints_dir` | Checkpoint root, default `./checkpoints`. |
| `--model` | Model selector: commonly `cycle_gan`, `pix2pix`, `test`, `colorization`; `template` exists for extension examples. |
| `--dataset_mode` | Loader selector: commonly `unaligned`, `aligned`, `single`, `colorization`; set by model defaults in many workflows. |
| `--direction` | `AtoB` or `BtoA`; swaps A/B meaning for paired/unpaired models. |
| `--input_nc`, `--output_nc` | Input/output channel counts. Colorization sets `1` and `2`. |
| `--netG` | Generator: `resnet_9blocks`, `resnet_6blocks`, `unet_256`, `unet_128`. |
| `--netD` | Discriminator: `basic`, `n_layers`, `pixel`. |
| `--norm` | Normalization: `instance`, `batch`, `none`, `syncbatch` in source code. Keep stable with checkpoints. |
| `--preprocess` | `resize_and_crop`, `crop`, `scale_width`, `scale_width_and_crop`, or `none`. |
| `--load_size`, `--crop_size` | Resize/crop sizes. Crop-based modes require `load_size >= crop_size`; many generator paths need dimensions divisible by 4. |
| Device environment | The current parser has no `--gpu_ids` flag. `util.init_ddp()` selects CPU when CUDA is unavailable and `cuda:0` otherwise. Use a CPU-only PyTorch build or `CUDA_VISIBLE_DEVICES=` to hide GPUs; use `CUDA_VISIBLE_DEVICES=0,1` and `torchrun` for visible-GPU/DDP selection. |
| `--use_wandb`, `--wandb_project_name` | Enable W&B logging. The dependency is import-time required by current source, but network/credentials are only needed when enabled. |

## Training-only options

| Flag | Purpose / verified behavior |
| --- | --- |
| `--display_freq`, `--update_html_freq`, `--print_freq` | Frequency for displaying/saving samples and printing losses. |
| `--no_html` | Disable training HTML sample pages under `checkpoints/<name>/web/`. |
| `--save_latest_freq`, `--save_epoch_freq`, `--save_by_iter` | Checkpoint cadence and naming. |
| `--continue_train`, `--epoch_count` | Resume training and control epoch numbering. |
| `--phase` | Defaults to `train`; determines loader folders such as `trainA/trainB` or `train/`. |
| `--n_epochs`, `--n_epochs_decay` | Defaults are `100` and `100`. Use tiny values only for smoke checks. |
| `--gan_mode` | `lsgan`, `vanilla`, or `wgangp`. Defaults differ by model. |
| `--pool_size` | Image buffer size for CycleGAN; pix2pix sets this to `0`. |
| `--lr`, `--beta1`, `--lr_policy`, `--lr_decay_iters` | Optimizer and scheduler controls. |

## Test-only options

| Flag | Purpose / verified behavior |
| --- | --- |
| `--results_dir` | Results root, default `./results/`. |
| `--phase` | Defaults to `test`; determines folder suffix or result subdirectory. |
| `--epoch`, `--load_iter` | Which checkpoint suffix to load (`latest` by default). |
| `--num_test` | Number of input images to process, default `50`. |
| `--eval` | Run modules in eval mode; relevant for dropout/batchnorm behavior. |
| `--model_suffix` | Added by `--model test`; the loader expects `latest_net_G<suffix>.pth`. |

The test script hard-codes `num_threads=0`, `batch_size=1`, `serial_batches=True`, and `no_flip=True` after parsing.

## Verified model/dataset defaults

| Mode | Key defaults |
| --- | --- |
| train `cycle_gan` | `dataset_mode='unaligned'`, `netG='resnet_9blocks'`, `norm='instance'`, `gan_mode='lsgan'`, `pool_size=50`, `no_dropout=True`, `lambda_A=10`, `lambda_B=10`, `lambda_identity=0.5`. |
| train `pix2pix` | `dataset_mode='aligned'`, `netG='unet_256'`, `norm='batch'`, `gan_mode='vanilla'`, `pool_size=0`, `lambda_L1=100`. |
| train `colorization` | pix2pix defaults plus `dataset_mode='colorization'`, `input_nc=1`, `output_nc=2`, `direction='AtoB'`. |
| test `test` | `dataset_mode='single'`, `netG='resnet_9blocks'`, `norm='instance'`, `model_suffix=''`, `load_size=256`, `crop_size=256`. |
| test `pix2pix` | `dataset_mode='aligned'`, `netG='unet_256'`, `norm='batch'`, `load_size=256`, `crop_size=256`. |
| test `cycle_gan` | `dataset_mode='unaligned'`, `netG='resnet_9blocks'`, `norm='instance'`, `no_dropout=True`, `load_size=256`, `crop_size=256`. |
| test `colorization` | `dataset_mode='colorization'`, `input_nc=1`, `output_nc=2`, `direction='AtoB'`. |

## Network factory choices

The generator factory signature is `define_G(input_nc, output_nc, ngf, netG, norm='batch', use_dropout=False, init_type='normal', init_gain=0.02)`. The discriminator factory signature is `define_D(input_nc, ndf, netD, n_layers_D=3, norm='batch', init_type='normal', init_gain=0.02)`.

Checkpoint compatibility is structural. If a saved generator was trained with `unet_256` and batch normalization, testing it as `resnet_9blocks` with instance normalization will fail even if the checkpoint filename exists.
