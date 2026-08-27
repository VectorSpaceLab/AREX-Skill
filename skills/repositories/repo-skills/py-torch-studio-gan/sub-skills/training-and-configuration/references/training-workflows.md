# StudioGAN training workflows

This reference converts StudioGAN's script-first training interface into safe planning patterns. Use the bundled command builder when possible; it prints commands only and never executes training.

## Common command shape

Run from a StudioGAN checkout:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t \
  -cfg /path/to/PyTorch-StudioGAN/src/configs/CIFAR10/ContraGAN.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -metrics fid
```

Core flags:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-cfg`, `--cfg_file` | YAML config path | Config files set `DATA`, `MODEL`, `LOSS`, `OPTIMIZATION`, `PRE`, `AUG`, and `STYLEGAN`. |
| `-data`, `--data_dir` | Dataset root | Required for training unless generating/saving fake images only. CIFAR roots are download/cache roots; custom datasets use ImageFolder layout. |
| `-save`, `--save_dir` | Output root | StudioGAN creates folders such as checkpoints, logs, samples, figures, moments, and values below this root. |
| `-t`, `--train` | Enable training | Without `-t`, metric or analysis modes need a checkpoint. |
| `-ckpt`, `--ckpt_dir` | Checkpoint folder | Used for resume/eval/freezeD. Should contain StudioGAN `model=G-*` and `model=D-*` checkpoint files. |
| `-best`, `--load_best` | Load best checkpoint | Selects best checkpoint naming instead of current checkpoint naming. |
| `--print_freq` | Logging interval | `save_freq` must be divisible by `print_freq`. |
| `--save_freq` | Checkpoint/evaluation interval | Drives periodic fake image visualization, metrics, and checkpoint writes during training. |

Metric flags during training:

| Flag | Meaning | Training notes |
| --- | --- | --- |
| `-metrics fid` | Compute FID only | This is the default if metrics are not specified. |
| `-metrics is fid prdc` | Compute IS, FID, and PRDC family | Requires evaluation model weights and a reference dataset. |
| `-metrics none` | Skip training-time metrics | Useful for DDP smoke runs or to avoid weight downloads. |
| `-ref train` / `-ref valid` / `-ref test` | Reference split for metrics | CIFAR10/100 support `train` or `test`; most ImageFolder datasets use `train` or `valid`. |
| `--pre_resizer` | Preprocess resize before dataset tensors | Allowed values: `wo_resize`, `nearest`, `bilinear`, `bicubic`, `lanczos`. |
| `--post_resizer` | Evaluation resize policy | Allowed values: `legacy`, `clean`, `friendly`. |
| `--eval_backbone` | Metric backbone | Allowed values: `InceptionV3_tf`, `InceptionV3_torch`, `ResNet50_torch`, `SwAV_torch`, `DINO_torch`, `Swin-T_torch`. |

## Single GPU

Use one device when debugging configs or training small datasets:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t \
  -cfg /path/to/config.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -metrics fid
```

Checks:

- If only one GPU is visible, do not pass `-DDP`; `check_compatability` rejects DDP with world size 1.
- You may pass `-mpc` for mixed precision if the model and CUDA stack support it.
- `-sync_bn` is mainly useful with multi-GPU runs; it is not a fix for missing CUDA.

## DataParallel multi-GPU

StudioGAN enters DataParallel when multiple GPUs are visible and `-DDP` is not set:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t \
  -cfg /path/to/config.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -metrics fid
```

Checks:

- `OPTIMIZATION.batch_size` must divide evenly by the visible GPU count.
- For StyleGAN2/3, generator mapping/synthesis modules and discriminator are wrapped separately.
- DataParallel can be used for checkpoint analysis paths that DDP rejects, but those paths belong to the sampling/analysis sub-skill.

## DistributedDataParallel

DDP uses one process per visible GPU and requires rendezvous environment variables:

```bash
export MASTER_ADDR="localhost"
export MASTER_PORT="2222"
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -DDP \
  -cfg /path/to/config.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -metrics none
```

Multi-node DDP adds node flags:

```bash
# node 0
export MASTER_ADDR="node0-host-or-ip"
export MASTER_PORT="2222"
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -DDP -tn 2 -cn 0 \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save

# node 1
export MASTER_ADDR="node0-host-or-ip"
export MASTER_PORT="2222"
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -DDP -tn 2 -cn 1 \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

DDP constraints:

- Use `--backend nccl` for CUDA training unless the environment requires `gloo`.
- `world_size = visible_gpus * total_nodes`; `OPTIMIZATION.batch_size` must be divisible by this value.
- DDP rejects visualization, KNN, interpolation, frequency, TSNE, SeFa, Langevin/DDLS, and CAS flags. Train with DDP first, then run analysis later with single GPU or DataParallel.
- DDP with mixed precision prints a standing-statistics reminder for reliable evaluation.

## Mixed precision and synchronized batch norm

Mixed precision:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -mpc \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Synchronized batch norm:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -sync_bn \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Combined DDP example:

```bash
export MASTER_ADDR="localhost"
export MASTER_PORT="2222"
CUDA_VISIBLE_DEVICES=0,1,2,3 python src/main.py -t -DDP -sync_bn -mpc \
  -metrics none \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Checks:

- `batch_statistics` cannot be combined with synchronized BN when `world_size > 1`.
- StyleGAN2/3 mixed precision enables StyleGAN custom-op code paths; failures usually indicate CUDA toolkit/compiler compatibility rather than a YAML syntax error.

## HDF5 and in-memory loading

Training can preprocess the train split into HDF5 for faster I/O:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -hdf5 \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Load the HDF5 into host memory:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -hdf5 -l \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Checks:

- `-l` requires `-hdf5`.
- HDF5 creation writes a dataset-specific `*_train.hdf5` file under `-data`; this can be large.
- iFID with HDF5 requires loading HDF5 into memory. Route iFID command details to the metrics or sampling sub-skills, depending on the task.

## Resume from checkpoint

Resume training from current checkpoint naming:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t \
  -cfg /path/to/config.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -ckpt /path/to/checkpoint
```

Resume/load best checkpoint:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -best \
  -cfg /path/to/config.yaml \
  -data /path/to/data \
  -save /path/to/save \
  -ckpt /path/to/checkpoint
```

Behavior to expect:

- Generator and discriminator weights are loaded from `model=G-current-*`/`model=D-current-*` or best equivalents.
- Optimizer state is loaded for normal training resume, but not for eval-only or freezeD transfer.
- For StyleGAN2/3 resume, EMA ramp-up is disabled after loading; StyleGAN3-r blur ramp-up may also be disabled.
- If ADA is active after checkpoint load, ADA adaptation is made more responsive at the beginning of the resumed run.

## FreezeD transfer training

FreezeD requires a source checkpoint:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t --freezeD 2 \
  -ckpt /path/to/source_checkpoint \
  -cfg /path/to/target_config.yaml \
  -data /path/to/target_data \
  -save /path/to/save
```

Checks:

- `--freezeD` must be greater than `-1` and must be paired with `-ckpt`.
- Checkpoint model parameters are loaded non-strictly for FreezeD; mismatch names can appear when transferring across related configurations.
- FreezeD resets the run bookkeeping rather than continuing the source run's step count.

## Standing statistics after training

Standing statistics are an evaluation-time batch-norm update trick. During training, StudioGAN warns that standing statistics are not used until after training finishes.

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -std_stat -std_max 64 -std_step 200 \
  -cfg /path/to/config.yaml \
  -ckpt /path/to/checkpoint \
  -data /path/to/data \
  -save /path/to/save
```

Do not combine `-batch_stat` and `-std_stat`.

## W&B logging policy

The training path imports W&B and calls finish at the end. Before executing training, decide one of:

- Login using an approved API key in the runtime environment.
- Set offline/disabled W&B mode according to the environment policy.
- Run only dry-run validators and command builders if credentials are unavailable.

Common W&B symptoms and remedies are listed in [troubleshooting](troubleshooting.md).

## Dataset-family command patterns

These are planning templates, not guaranteed optimal hyperparameters:

| Dataset family | Typical flags | Rationale |
| --- | --- | --- |
| CIFAR10/100 non-StyleGAN | `-hdf5 -l -std_stat -metrics is fid prdc -ref train -mpc --post_resizer friendly` | CIFAR auto-download path, no external ImageFolder validation split, fast HDF5/in-memory I/O. |
| CIFAR StyleGAN2/3 | `-hdf5 -l -metrics is fid prdc -ref train -mpc --post_resizer friendly` | StyleGAN compatibility excludes standing statistics. |
| ImageNet family | `-hdf5 -l -sync_bn -std_stat -metrics is fid prdc -ref train -mpc --pre_resizer lanczos --post_resizer friendly` | Large ImageFolder datasets use crop/resize and benefit from multi-GPU/sync-BN. |
| AFHQv2/FFHQ | `-metrics is fid prdc -ref train -mpc --pre_resizer lanczos --post_resizer friendly` | High-resolution ImageFolder training; verify folder layout and memory before HDF5. |

## Safe command builder

```bash
python sub-skills/training-and-configuration/scripts/build_studiogan_train_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --data-dir /path/to/data \
  --save-dir /path/to/save \
  --gpus 0,1,2,3 \
  --metrics none --ddp --sync-bn --mixed-precision --hdf5 --load-in-memory
```

Use the printed command as a starting point, then run the config validator with matching flags before launching expensive training.
