# Training troubleshooting

Use this page to distinguish safe preflight failures from failures that occur only after a real distributed training launch.

## Training should not start automatically

Do not run `train.py` merely to answer a setup question. It is a long-running CUDA/NCCL job, reads a large external Vimeo triplet dataset, writes TensorBoard events, and repeatedly overwrites `train_log/flownet.pkl`. Prefer these safe actions first:

```bash
python skills/disco/eccv2022-rife/sub-skills/training/scripts/check_vimeo_triplet_layout.py --root vimeo_triplet
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
python -c "from torch.utils.tensorboard import SummaryWriter; print('tensorboard ok')"
```

Only launch training after the user confirms GPU allocation, data availability, wall time, and output side effects.

## Missing TensorBoard

Symptom:

```text
ModuleNotFoundError: No module named 'tensorboard'
```

Cause: the training entry point imports `SummaryWriter`, but TensorBoard is not listed in the base requirements file.

Fix:

```bash
python -m pip install tensorboard
```

Then re-run only the import preflight unless the user has approved a training job.

## Missing or malformed Vimeo triplet data

Common symptoms:

```text
FileNotFoundError: vimeo_triplet/tri_trainlist.txt
FileNotFoundError: vimeo_triplet/tri_testlist.txt
cv2.error ... !_src.empty()
TypeError: 'NoneType' object is not subscriptable
ValueError: high <= 0
```

Likely causes and fixes:

- `vimeo_triplet/` is not under the working directory used to run training. Run from the repository root or provide the dataset at the expected relative path.
- `tri_trainlist.txt` or `tri_testlist.txt` is missing. The dataset class opens both list files even when the default training loop does not use the test split.
- A list entry is not relative to `vimeo_triplet/sequences/` or has a leading slash / parent traversal. Entries should look like `00001/0001`, not full filesystem paths.
- A sequence directory is missing one of `im1.png`, `im2.png`, or `im3.png`. `im2.png` is the ground-truth middle frame; if it is missing, training cannot compute the loss.
- Sampled training images are smaller than the `224 x 224` random crop.
- Files are not valid PNGs or have inconsistent dimensions within a triplet.

Run the bundled validator before launching:

```bash
python skills/disco/eccv2022-rife/sub-skills/training/scripts/check_vimeo_triplet_layout.py --root vimeo_triplet --all
```

Use a bounded sample when the dataset is very large:

```bash
python skills/disco/eccv2022-rife/sub-skills/training/scripts/check_vimeo_triplet_layout.py --root vimeo_triplet --sample-per-list 50
```

## NCCL, CUDA, and launcher errors

Training is CUDA-only in this checkout. There is no CPU substitute for the default `train.py` workflow.

### `torch.cuda.is_available()` is false

Use a CUDA-enabled PyTorch wheel/conda package, verify the NVIDIA driver, and check that the scheduler exposes GPUs to the process. CPU wheels can pass some import checks but will fail training.

### `RuntimeError: Distributed package doesn't have NCCL built in`

Install a PyTorch build with NCCL/CUDA support. This error usually means the environment has a CPU-only or incompatible PyTorch build.

### Rank or world-size mismatch / launch hang

Keep launcher process count and `--world_size` identical:

```bash
python3 -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4
```

For a single visible GPU:

```bash
CUDA_VISIBLE_DEVICES=0 python3 -m torch.distributed.launch --nproc_per_node=1 train.py --world_size=1 --batch_size=4
```

Avoid plain `python train.py` because the script expects distributed rendezvous variables from the launcher. If several jobs share a host, set a free master port, for example:

```bash
MASTER_PORT=29601 python3 -m torch.distributed.launch --nproc_per_node=4 train.py --world_size=4
```

### `unrecognized arguments: --local-rank`

The source parser accepts `--local_rank` with an underscore. Some modern launch paths may pass `--local-rank` with a dash. Use the README-style launcher when it passes the underscore form in your environment, or deliberately add an alias in the local training script before launching. Treat that as a source adaptation, not a model-quality change.

### NCCL networking errors

On multi-node or restricted network hosts, NCCL may need environment configuration such as the intended network interface or disabled InfiniBand. Keep such settings scheduler-specific and record them with the run command. For single-node runs, first verify that all requested GPUs are visible and no other process owns the devices.

## CUDA out of memory

Likely controls:

- Lower `--batch_size`; it is per process, not global.
- Reduce the number of visible GPUs only if `--world_size` and launcher process count are reduced together.
- Make sure no unrelated CUDA jobs occupy the selected GPUs.
- Consider reducing DataLoader pressure if the host has few CPU workers, but remember that `num_workers=8` is hard-coded per loader in the training script.
- Do not try inference-only flags such as `--fp16`; the training parser does not support them.

A one-GPU reduced-batch command is still a real training job:

```bash
CUDA_VISIBLE_DEVICES=0 python3 -m torch.distributed.launch --nproc_per_node=1 train.py --world_size=1 --batch_size=4
```

Ask for approval before executing it.

## Checkpoint and log directory problems

### `train_log/flownet.pkl` cannot be written

The save path is fixed to `train_log/flownet.pkl`, and the code does not create the directory. Create it before launch:

```bash
mkdir -p train_log
```

### Previous checkpoint is overwritten

The training loop saves the same filename after every epoch. If intermediate checkpoints matter, copy or rename `train_log/flownet.pkl` externally after selected epochs, or adapt the save path intentionally.

### TensorBoard event directories contain old runs

The code writes to `train/` and `validate/` relative to the launch directory. Move old directories aside before a new experiment if you need clean curves:

```bash
mv train train.previous
mv validate validate.previous
```

Do that only if preserving old event files is not required.

## Validation loop issues

Validation runs every 5 epochs over the held-out 5% tail of `tri_trainlist.txt`, not over `tri_testlist.txt` in the default training loop. If the validation split is empty or malformed, training may run for several epochs before failing at validation. The validator reports the 95/5 split counts so this can be caught before launch.

## Post-training next steps

- To compute official metrics or choose a benchmark script, route to the evaluation sub-skill.
- To use `train_log/flownet.pkl` for image or video interpolation, route to the interpolation sub-skill and ensure the checkpoint directory contains the expected `.pkl` file.
