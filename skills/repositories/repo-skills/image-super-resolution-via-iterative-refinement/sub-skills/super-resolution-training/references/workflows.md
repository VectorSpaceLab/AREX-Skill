# Super-Resolution Training Workflows

This reference is grounded in the repository's README training and validation sections, `sr.py`, `core/logger.py`, `model/model.py`, `model/networks.py`, and the bundled SR config files.

## Command shape

`sr.py` accepts a config path plus a phase selector:

```bash
python sr.py -p train -c <config>
python sr.py -p val -c <config>
```

GPU selection is a command-line override of the config's `gpu_ids` field:

```bash
CUDA_VISIBLE_DEVICES=0 python sr.py -p train -c <config> -gpu 0
CUDA_VISIBLE_DEVICES=0,1 python sr.py -p train -c <config> -gpu 0,1
```

`Logger.parse` strips `//` comments from the config, builds an experiment root under `experiments/<name>_<timestamp>/`, and places the runtime log, tensorboard, result, and checkpoint directories beneath that root. The config's relative paths are resolved from the current working directory, so the command should be run from the repository root or from another directory with matching relative paths.

## Phase map

| Intent | `sr.py` phase | Config state | What happens |
|---|---|---|---|
| New training | `train` | `path.resume_state` empty or unset | Optimizes the diffusion model, runs periodic validation, and saves checkpoints. |
| Resume training | `train` | `path.resume_state` points to a checkpoint prefix | Loads generator and optimizer state, restores `begin_step` / `begin_epoch`, and continues training. |
| Validation only | `val` | `path.resume_state` points to a checkpoint prefix | Loads the generator, runs the validation loader, saves images, and reports PSNR/SSIM. |
| Debug run | `train` or `val` | Same config plus `-d` | Shrinks batch sizes, data lengths, and diffusion timesteps for a quick smoke run. |

## Debug behavior

When `-d` is present, `Logger.parse` changes the runtime config instead of requiring a special JSON file:

- prepends `debug_` to the run name
- sets training `val_freq` to 2
- sets `print_freq` to 2
- sets `save_checkpoint_freq` to 3
- sets training batch size to 2
- sets both train and val beta schedules to 10 timesteps
- sets train `data_len` to 6
- sets val `data_len` to 3

This is a runtime shrinkage mode only. It is useful for command validation and wiring checks, not for benchmark claims.

## Bundled SR config families

| Config family | Best for | Key settings |
|---|---|---|
| `sr_ddpm_16_128.json` | 16→128 DDPM super-resolution | `which_model_G=ddpm`, `datatype=lmdb`, train `mode=HR`, val `mode=LRHR`, `image_size=128`, `in_channel=6`, `out_channel=3`, `gpu_ids=[0]`, `batch_size=12`, `lr=1e-4`. |
| `sr_sr3_16_128.json` | 16→128 SR3 super-resolution | `which_model_G=sr3`, `datatype=lmdb`, train `mode=HR`, val `mode=LRHR`, `image_size=128`, `in_channel=6`, `out_channel=3`, `gpu_ids=[0]`, `batch_size=4`, `lr=1e-4`. |
| `sr_sr3_64_512.json` | 64→512 SR3 super-resolution | `which_model_G=sr3`, `datatype=img`, train `mode=HR`, val `mode=LRHR`, `image_size=512`, `in_channel=6`, `out_channel=3`, `gpu_ids=[0,1]`, `batch_size=2`, `lr=3e-6`, `norm_groups=16`. |

All super-resolution configs keep `model.diffusion.conditional: true`. If you change that flag, make sure the input concatenation path in the diffusion model and the dataset mode stay in sync.

## Model and config rules

- `model.networks.define_G` picks the DDPM or SR3 backbone from `which_model_G`.
- `model.diffusion.image_size` must match the high-resolution size expected by the dataset and the U-Net.
- `model.unet.in_channel` / `out_channel` stay at `6` / `3` for the conditional super-resolution path.
- `norm_groups` must divide every channel width reached by the U-Net blocks. The 64→512 config drops to 16 for this reason.
- `attn_res` should be aligned with a resolution the U-Net actually visits.
- The training loop is step-based, not epoch-based. `n_iter`, `val_freq`, `print_freq`, and `save_checkpoint_freq` all count optimizer steps.

## Checkpoint and resume rules

- `save_network` writes `checkpoint/I<iter>_E<epoch>_gen.pth` and `checkpoint/I<iter>_E<epoch>_opt.pth`.
- `path.resume_state` must point to the checkpoint prefix without the `_gen.pth` or `_opt.pth` suffix.
- In `train` phase, `load_network` restores both generator and optimizer state.
- In `val` phase, `load_network` restores only the generator state.
- A resumed run continues from the stored `begin_step` and `begin_epoch` counters.

## W&B flags

- `-enable_wandb` turns on `WandbLogger`.
- `-log_wandb_ckpt` saves checkpoints as W&B artifacts during training.
- `-log_eval` records validation tables in `sr.py` validation mode.
- W&B requires the package to be installed and a logged-in account/token before the run starts.

## Output layout

### Training mode

During `train`, periodic validation writes files under the epoch-specific result directory:

- `results/<epoch>/<step>_<idx>_hr.png`
- `results/<epoch>/<step>_<idx>_sr.png`
- `results/<epoch>/<step>_<idx>_lr.png`
- `results/<epoch>/<step>_<idx>_inf.png`

The run also writes:

- `train.log`
- `val.log`
- `tb_logger/`
- `checkpoint/`

### Validation mode

During `val`, the script writes the full evaluation set under the result root:

- `results/<step>_<idx>_sr_process.png`
- `results/<step>_<idx>_sr.png`
- `results/<step>_<idx>_hr.png`
- `results/<step>_<idx>_lr.png`
- `results/<step>_<idx>_inf.png`

It then reports mean PSNR and SSIM over the validation set.

## Bundled helper contract

[`build_sr_command.py`](../scripts/build_sr_command.py) reads a config with `//` comments, validates the requested phase, optional GPU-id override, debug flag, and W&B flags, and prints:

1. prerequisite notes
2. a shell command that invokes `sr.py`

The helper also forwards the repo's W&B checkpoint and evaluation flags when requested. It never launches training or validation.
