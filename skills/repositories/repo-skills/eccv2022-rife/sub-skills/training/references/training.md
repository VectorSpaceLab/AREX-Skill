# Training and reproduction reference

This reference distills ECCV2022-RIFE training behavior for safe planning. It is meant for preflight checks and command construction first; actual training should be treated as an explicit, long-running CUDA job.

## What training requires

- A source checkout with the training entry point available from the repository root.
- A CUDA-enabled PyTorch/torchvision install. The training code sets `device = torch.device("cuda")`, initializes `torch.distributed` with the `nccl` backend, and calls `torch.cuda.set_device(args.local_rank)`.
- TensorBoard installed in the Python environment. `train.py` imports `torch.utils.tensorboard.SummaryWriter`, but TensorBoard is not included in the base requirements file.
- Vimeo90K triplet data arranged under `vimeo_triplet/`.
- Enough GPU memory, CPU workers, disk space for event files, and a wall-time budget. The README training note reports 16 CPUs, 4 GPUs, and about 20G memory.

A minimal dependency pattern is:

```bash
python -m pip install -r requirements.txt tensorboard
```

Use a CUDA-enabled `torch` build for training. CPU-only PyTorch can import parts of the project, but it is not a substitute for this training workflow.

## Vimeo triplet data layout

The data loader expects a fixed relative layout from the repository working directory:

```text
vimeo_triplet/
  tri_trainlist.txt
  tri_testlist.txt
  sequences/
    <clip-or-scene/subclip>/
      im1.png
      im2.png
      im3.png
```

Each non-empty list line is a relative sequence key under `vimeo_triplet/sequences/`, for example `00001/0001`. For a listed key, the loader reads:

- `im1.png` as the first input frame (`img0`),
- `im2.png` as the middle ground-truth frame (`gt`),
- `im3.png` as the second input frame (`img1`).

`VimeoDataset` always opens both `tri_trainlist.txt` and `tri_testlist.txt` during initialization. In the default `train.py` flow:

- `VimeoDataset('train')` uses the first `int(len(tri_trainlist) * 0.95)` entries.
- `VimeoDataset('validation')` uses the remaining entries from `tri_trainlist.txt`.
- `tri_testlist.txt` is loaded by the dataset class, but `train.py` does not use `VimeoDataset('test')` by default.

Run the bundled validator before launching a job:

```bash
python skills/disco/eccv2022-rife/sub-skills/training/scripts/check_vimeo_triplet_layout.py --root vimeo_triplet
```

For a full dataset scan instead of a bounded sample:

```bash
python skills/disco/eccv2022-rife/sub-skills/training/scripts/check_vimeo_triplet_layout.py --root vimeo_triplet --all
```

The validator only checks files and PNG headers; it does not download data, import the model, or start training.

## Loader transforms and returned tensors

For each sample, `dataset.VimeoDataset` reads images with OpenCV, so arrays are in OpenCV channel order before conversion to tensors. The returned item is:

```text
(torch.cat((img0, img1, gt), dim=0), timestep)
```

where the image tensor has 9 channels arranged as `img0` (3), `img1` (3), and `gt` (3), and `timestep` is a tensor shaped `1 x 1 x 1` with value `0.5` for triplet training.

For `dataset_name == 'train'`, the loader applies:

- random `224 x 224` crop,
- random channel reversal,
- random vertical flip,
- random horizontal flip,
- random input-frame swap with `timestep = 1 - timestep`,
- random rotation by 0, 90, 180, or 270 degrees.

Validation samples are read without those training augmentations. The class has nominal `h = 256` and `w = 448` fields, matching the Vimeo triplet image scale, but the actual training crop is `224 x 224`.

## Launch commands and arguments

Default training arguments are:

| Argument | Default | Meaning |
| --- | ---: | --- |
| `--epoch` | `300` | Number of training epochs. |
| `--batch_size` | `16` | Per-process mini-batch size used by each distributed worker. Effective global batch is approximately `batch_size * world_size`. |
| `--local_rank` | `0` | CUDA device index for the worker. The launcher normally injects this per process. |
| `--world_size` | `4` | Number of distributed processes. Must match the launcher process count. |

The README training command is:

```bash
python3 -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4
```

Before launching, create the checkpoint directory because the training code saves into it:

```bash
mkdir -p train_log
python3 -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4
```

For a planned one-GPU run, keep the process count and `world_size` aligned and reduce per-process batch size if memory is limited:

```bash
CUDA_VISIBLE_DEVICES=0 python3 -m torch.distributed.launch --nproc_per_node=1 train.py --world_size=1 --batch_size=4
```

This is still a real training run, not a cheap smoke test. Ask for explicit approval before executing it.

### Batch size and learning-rate scaling

The training loop computes:

```text
learning_rate = schedule(step) * world_size / 4
```

Thus the default 4-GPU run uses the base schedule, while `world_size=1` uses one quarter of that learning rate unless the source is changed. `--batch_size` is passed to each worker's `DataLoader`; lowering it is the first response to CUDA OOM.

## Training loop, evaluation loop, and outputs

At startup, training:

1. Initializes NCCL distributed processing.
2. Sets the current CUDA device from `--local_rank`.
3. Seeds Python, NumPy, and CUDA RNGs.
4. Wraps the model with DDP when constructed with a non-negative local rank.
5. Builds a distributed training loader and a validation loader.

During each training step, the loop moves data to CUDA, normalizes pixel values by `255`, splits the 9-channel tensor into `imgs = img0 + img1` and `gt = im2`, and calls:

```text
model.update(imgs, gt, learning_rate, training=True)
```

The public training contract of `Model.update` returns a prediction and an info dictionary containing losses, masks, flows, and teacher-merge outputs. The source comment notes that RIFEm training would need timestep handling, but the default triplet training call does not pass timestep into `Model.update`; architecture or RIFEm changes are outside this sub-skill.

Rank 0 writes TensorBoard scalars every 200 steps and image/flow/mask summaries every 1000 steps. Every 5 epochs, validation runs and writes validation images plus PSNR scalars. After every epoch, the model saves:

```text
train_log/flownet.pkl
```

TensorBoard event directories are:

```text
train/
validate/
```

To inspect them after or during a run:

```bash
tensorboard --logdir_spec train:train,validate:validate
```

## Side-effect and approval checklist

Before running actual training, confirm:

- The user has provided or mounted `vimeo_triplet/` in the expected layout.
- The validator passes for at least a representative sample; use `--all` for a full preflight when time allows.
- CUDA devices are visible, and the number of visible GPUs equals `--nproc_per_node` / `--world_size`.
- The job scheduler permits multi-process NCCL jobs and enough CPU workers.
- `train_log/` exists and overwriting `train_log/flownet.pkl` after each epoch is acceptable.
- Existing `train/` and `validate/` TensorBoard event directories may be appended to or mixed with prior runs unless moved aside.
- The user explicitly approves a long-running, mutating training command.
