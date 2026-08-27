# ImageNet Benchmark Workflows

## Purpose

Read this when you need to launch or sample the ImageNet benchmark branches.

## Training

### Single-node route

- `bash scripts/run_8gpus.sh`

### Slurm route

- `srun -n8 --ntasks-per-node=8 --gres=gpu:8 bash scripts/slurm/run_8gpus.sh`
- `srun -N4 --ntasks-per-node=8 --gres=gpu:8 bash scripts/slurm/run_32gpus.sh`

### Stage script editing

The `exps/*.sh` files set the model size, batch size, learning rate, and `train_data_root`.
Edit the local ImageNet path before launching.

### High-value flags in the training scripts

- `--data_path` / `train_data_root`
- `--results_dir`
- `--model`
- `--image_size`
- `--global_batch_size`
- `--micro_batch_size`
- `--precision`
- `--grad_precision`
- `--data_parallel sdp|fsdp`
- `--resume`
- `--init_from`
- `--snr_type`

## Sampling / evaluation

The Next-DiT benchmark branches provide a sampling script.
The parser supports ODE and SDE modes plus class labels.

### Typical route

- `python sample.py --ckpt <ckpt_dir> --class_labels <id> <id> ... --image_save_path <out_dir>`
- Use `ODE` or `SDE` as the first positional mode when the script expects it.

### High-value sampling flags

- `--precision tf32|fp32|fp16|bf16`
- `--ema` / `--no_ema`
- `--sampling-method`
- `--path-type`, `--prediction`, `--loss-weight`, `--sample-eps`, `--train-eps`
- `--atol`, `--rtol`, `--reverse`, `--likelihood`
- `--class_labels` to choose the ImageNet classes to sample

## Model family notes

- Flag-DiT is the baseline backbone.
- Next-DiT adds the newer backbone and the class-conditional sampling route.
- Next-DiT-MoE adds the MoE variant and its own sample/train scripts.
- The README notes that larger models need more than a single 8-GPU node.
