# train.py CLI Reference

## When To Read

Read this when you need exact flag names, defaults, or option groups for `train.py`.

## Verified Argument Groups

`train.py` assembles its command line from three groups defined in `arguments/__init__.py` plus a small set of training-only flags.

### Loading Parameters

| Flag | Default | Notes |
|---|---:|---|
| `--sh_degree` | `3` | Maximum spherical-harmonics degree. |
| `--source_path` / `-s` | required | Scene root containing COLMAP or Blender-style data. |
| `--model_path` / `-m` | empty | Output directory; random if omitted. |
| `--images` / `-i` | `images` | Alternate COLMAP image folder. |
| `--depths` / `-d` | empty | Depth-map folder relative to source. |
| `--resolution` / `-r` | `-1` | 1/2/4/8 or a target width. |
| `--white_background` / `-w` | `False` | White background instead of black. |
| `--train_test_exp` | `False` | Split-aware exposure training mode. |
| `--data_device` | `cuda` | Device for loading source image tensors. |
| `--eval` | `False` | Use a train/test split. |

### Pipeline Parameters

| Flag | Default | Notes |
|---|---:|---|
| `--convert_SHs_python` | `False` | Compute SH colors in Python. |
| `--convert_cov3D_python` | `False` | Compute covariance in Python. |
| `--debug` | `False` | Enables rasterizer debug mode. |
| `--antialiasing` | `False` | Enables EWA/Mip-Splatting-style antialiasing. |

### Optimization Parameters

| Flag | Default | Notes |
|---|---:|---|
| `--iterations` | `30000` | Total optimization iterations. |
| `--position_lr_init` | `0.00016` | Initial XYZ LR. |
| `--position_lr_final` | `0.0000016` | Final XYZ LR. |
| `--position_lr_delay_mult` | `0.01` | LR warmup multiplier. |
| `--position_lr_max_steps` | `30000` | LR schedule steps. |
| `--feature_lr` | `0.0025` | SH feature LR. |
| `--opacity_lr` | `0.025` | Opacity LR. |
| `--scaling_lr` | `0.005` | Scale LR. |
| `--rotation_lr` | `0.001` | Rotation LR. |
| `--exposure_lr_init` | `0.01` | Exposure LR start. |
| `--exposure_lr_final` | `0.001` | Exposure LR end. |
| `--exposure_lr_delay_steps` | `0` | Exposure LR warmup steps. |
| `--exposure_lr_delay_mult` | `0.0` | Exposure LR warmup multiplier. |
| `--percent_dense` | `0.01` | Densification threshold. |
| `--lambda_dssim` | `0.2` | DSSIM loss weight. |
| `--densification_interval` | `100` | Densify cadence. |
| `--opacity_reset_interval` | `3000` | Opacity reset cadence. |
| `--densify_from_iter` | `500` | Start densification. |
| `--densify_until_iter` | `15000` | Stop densification. |
| `--densify_grad_threshold` | `0.0002` | Gradient threshold. |
| `--depth_l1_weight_init` | `1.0` | Initial depth-loss weight. |
| `--depth_l1_weight_final` | `0.01` | Final depth-loss weight. |
| `--random_background` | `False` | Random background color. |
| `--optimizer_type` | `default` | Use `sparse_adam` only with accelerated rasterizer support. |

### Training-Only Flags

| Flag | Default | Notes |
|---|---:|---|
| `--ip` | `127.0.0.1` | Viewer socket IP. |
| `--port` | `6009` | Viewer socket port. |
| `--debug_from` | `-1` | Iteration that turns on debug mode. |
| `--detect_anomaly` | `False` | Enables autograd anomaly detection. |
| `--test_iterations` | `7000 30000` | Iterations at which test metrics are computed. |
| `--save_iterations` | `7000 30000` | Iterations at which the model is saved. |
| `--quiet` | `False` | Suppress log chatter. |
| `--disable_viewer` | `False` | Disable the network viewer server. |
| `--checkpoint_iterations` | `[]` | Save checkpoints at the listed iterations. |
| `--start_checkpoint` | `None` | Resume from a checkpoint path. |

## Behavior Notes

- `--model_path` is optional; if omitted, `train.py` creates a randomized directory inside `./output/`.
- `args.save_iterations.append(args.iterations)` means the final iteration is always saved.
- The loader turns `--source_path` into an absolute path.
- If `--disable_viewer` is not set, the network viewer binds to `--ip` and `--port` and waits for a connection.
- If `--debug_from` is reached, the rasterizer debug flag turns on.
- `train.py` uses `--eval` to construct a train/test split and then logs L1/PSNR on the requested iterations.
