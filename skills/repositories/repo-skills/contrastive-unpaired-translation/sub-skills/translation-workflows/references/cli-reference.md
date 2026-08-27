# CLI reference

This page lists the verified command-line options that matter for CUT, FastCUT, and SinCUT workflows. It is intentionally narrower than the raw `--help` output.

## Shared options from `BaseOptions`

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--dataroot` | Root directory for the dataset | CUT/FastCUT expect `trainA/trainB` and usually `testA/testB`. SinCUT expects `trainA` and `trainB` with one image each. |
| `--name` | Experiment name | Drives checkpoint and result directory names. |
| `--gpu_ids` | GPU list or CPU selector | Use comma-separated GPU ids or `-1` for CPU. |
| `--checkpoints_dir` | Checkpoint root | Training writes here; test-time loading also uses it. |
| `--model` | Model family | `cut`, `sincut`, or other repo-supported model names. |
| `--dataset_mode` | Dataset family | `unaligned` for CUT/FastCUT; `singleimage` for SinCUT. |
| `--direction` | Domain direction | `AtoB` by default; `BtoA` is supported. |
| `--preprocess` | Input preprocessing | Common values include `resize_and_crop`, `scale_width`, `scale_shortside_and_crop`, `none`, and the SinCUT-specific `zoom_and_patch`. |
| `--load_size` | Resize size before crop | SinCUT rewrites this default. |
| `--crop_size` | Crop size | Used by the dataset transforms. |
| `--epoch` | Checkpoint epoch | `latest` is the default. |
| `--suffix` | Experiment-name suffix | Appended to `--name`. |
| `--stylegan2_G_num_downsampling` | StyleGAN2 generator depth | Used by the SinCUT defaults. |

## Training-only options from `TrainOptions`

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--display_freq` | Visdom/HTML display frequency | Set to a large value if you want fewer updates. |
| `--display_ncols` | Number of images per visdom row | Visual aid only. |
| `--display_id` | Visdom window id | `None` disables visdom allocation; `-1` in test disables display. |
| `--display_server` | Visdom server URL | Default is `http://localhost`. |
| `--display_env` | Visdom environment | Default is `main`. |
| `--display_port` | Visdom port | Default is `8097`. |
| `--update_html_freq` | HTML save frequency | Controls how often intermediate pages are updated. |
| `--print_freq` | Console logging frequency | Loss printing interval. |
| `--no_html` | Disable HTML output | Useful for minimal smoke runs. |
| `--save_latest_freq` | Latest checkpoint frequency | Iteration-based checkpointing. |
| `--save_epoch_freq` | Epoch checkpoint frequency | End-of-epoch saves. |
| `--continue_train` | Resume training | Loads latest checkpoint behavior. |
| `--epoch_count` | Starting epoch number | Used in learning-rate scheduling and checkpoint naming. |
| `--phase` | Train/val/test label | Affects output subdirectory naming. |
| `--pretrained_name` | Alternate checkpoint root | Used for transfer or warm start. |
| `--n_epochs` | Constant-LR epochs | Default 200 for CUT, lower for FastCUT and SinCUT. |
| `--n_epochs_decay` | LR decay epochs | Default 200 for CUT. |
| `--beta1`, `--beta2`, `--lr` | Adam settings | SinCUT overrides these defaults. |
| `--gan_mode` | GAN objective | `lsgan` by default, `nonsaturating` for SinCUT. |
| `--pool_size` | Image pool size | Set to 0 by CUT model defaults. |
| `--lr_policy` | LR schedule | `linear` by default. |
| `--lr_decay_iters` | Step schedule interval | Only used by step LR. |

## Test-only options from `TestOptions`

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--results_dir` | Result root | Test output lands here. |
| `--eval` | Use eval mode | Calls `model.eval()` after loading. |
| `--num_test` | Number of test images | `50` by default. |

## CUT-specific options from `CUTModel`

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--CUT_mode` | CUT vs FastCUT | Accepts `CUT` or `FastCUT` (case-insensitive in code). |
| `--lambda_GAN` | GAN loss weight | Default `1.0`. |
| `--lambda_NCE` | NCE loss weight | Default `1.0` for CUT, `10.0` for FastCUT. |
| `--nce_idt` | Identity NCE branch | Enabled by CUT defaults, disabled by FastCUT defaults. |
| `--nce_layers` | Layers for contrastive loss | Default `0,4,8,12,16`. |
| `--nce_includes_all_negatives_from_minibatch` | Cross-sample negatives | Used by SinCUT single-image training. |
| `--netF` | Feature sampler | `mlp_sample` by default. |
| `--netF_nc` | Feature projection width | Default `256`. |
| `--nce_T` | Temperature | Default `0.07`. |
| `--num_patches` | Number of sampled patches | FastCUT/CUT default `256`; SinCUT defaults to `1`. |
| `--flip_equivariance` | Flip regularization | Enabled by FastCUT defaults. |

## SinCUT-specific options from `SinCUTModel`

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--lambda_R1` | R1 gradient penalty weight | Default `1.0`. |
| `--lambda_identity` | Identity preservation weight | Default `1.0`. |

## Option interactions worth remembering

- `--model sincut` rewrites the dataset, network, preprocessing, batch-size, and epoch defaults.
- `--model cut` plus `--CUT_mode FastCUT` changes the NCE weight and training schedule.
- `--gpu_ids -1` is the CPU path.
- `--load_size` and `--crop_size` are still relevant even when the helper script uses a fixed output size.
- `--results_dir` matters only for testing; training does not write there.

## Verified source of truth

These option groups were confirmed from:
- `options/base_options.py`
- `options/train_options.py`
- `options/test_options.py`
- `models/cut_model.py`
- `models/sincut_model.py`
- `train.py --help`
- `test.py --help`
