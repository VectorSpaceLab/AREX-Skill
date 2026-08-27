# Protenix Training and Fine-Tuning Workflows

## Entry Point

The training entry point is `runner.train`. For portable command planning, use `python -m runner.train` for single-process jobs and `torchrun -m runner.train` for DDP jobs. The repository demo scripts call the file path directly, but module form avoids relying on the current working directory in generated plans.

Start with the no-run builder:

```bash
python scripts/build_training_command.py --mode train --data-root DATA_ROOT --base-dir OUTPUT_DIR
```

The builder never imports Protenix, checks CUDA, downloads data, initializes W&B, or launches training. It only prints commands and warnings.

## Required Training Fields

Direct `runner.train` commands must provide these required base fields:

- `--project`
- `--run_name`
- `--base_dir`
- `--eval_interval`
- `--log_interval`
- `--max_steps`

Most practical commands should also specify `--use_wandb false`, dataset sets, dtype, crop/batch sizes, checkpoint interval, learning rate, warmup, `--model.N_cycle`, `--sample_diffusion.N_step`, and triangle kernel choices.

## Safe Single-Process Pattern

Use this pattern only after data root, dependencies, GPU policy, and output location are confirmed:

```bash
export PROTENIX_ROOT_DIR=DATA_ROOT
python -m runner.train \
  --run_name protenix_train \
  --model_name protenix_base_default_v1.0.0 \
  --seed 42 \
  --base_dir OUTPUT_DIR \
  --dtype bf16 \
  --project protenix \
  --use_wandb false \
  --diffusion_batch_size 48 \
  --eval_interval 400 \
  --log_interval 50 \
  --checkpoint_interval 400 \
  --ema_decay 0.999 \
  --train_crop_size 384 \
  --max_steps 100000 \
  --warmup_steps 2000 \
  --lr 0.001 \
  --model.N_cycle 4 \
  --sample_diffusion.N_step 20 \
  --triangle_attention cuequivariance \
  --triangle_multiplicative cuequivariance \
  --data.train_sets weightedPDB_before2109_wopb_nometalc_0925 \
  --data.test_sets recentPDB_1536_sample384_0925,posebusters_0925
```

For portability debugging, switch triangle kernels to `torch` and consider `LAYERNORM_TYPE=torch`. This can be slower and is not a replacement for adequate GPU memory.

## Fine-Tuning Pattern

Fine-tuning commonly loads pretrained and EMA checkpoints, then restricts training to a text file of PDB IDs:

```bash
export PROTENIX_ROOT_DIR=DATA_ROOT
python -m runner.train \
  --model_name protenix_base_default_v1.0.0 \
  --run_name protenix_finetune \
  --seed 42 \
  --base_dir OUTPUT_DIR \
  --dtype bf16 \
  --project protenix \
  --use_wandb false \
  --load_checkpoint_path CHECKPOINT.pt \
  --load_ema_checkpoint_path CHECKPOINT.pt \
  --data.train_sets weightedPDB_before2109_wopb_nometalc_0925 \
  --data.weightedPDB_before2109_wopb_nometalc_0925.base_info.pdb_list SUBSET.txt \
  --data.test_sets recentPDB_1536_sample384_0925,posebusters_0925 \
  --max_steps 100000 \
  --eval_interval 400 \
  --log_interval 50
```

A subset file is plain text, one PDB ID per line:

```text
6hvq
5mqc
5zin
```

For released-data fine-tuning, a `base_info.pdb_list` override is lower risk than custom dataset code. For custom CIFs, first preprocess CIFs to bioassembly and index outputs, validate them, then override `base_info.indices_fpath`, `base_info.bioassembly_dict_dir`, and related paths.

## Multi-GPU and DDP

Use `torchrun` for DDP:

```bash
torchrun --nproc_per_node 8 -m runner.train \
  --model_name protenix_base_default_v1.0.0 \
  --run_name protenix_ddp_train \
  --base_dir OUTPUT_DIR \
  --project protenix \
  --use_wandb false \
  --max_steps 100000 \
  --eval_interval 400 \
  --log_interval 50 \
  --data.train_sets weightedPDB_before2109_wopb_nometalc_0925
```

`AF3Trainer` initializes NCCL when world size is greater than one and uses DistributedDataParallel. Dataloading uses weighted samplers and `configs.data.num_dl_workers`; every rank must see the same data paths.

If startup hangs, inspect `CUDA_VISIBLE_DEVICES`, `LOCAL_RANK`, `MASTER_ADDR`, `MASTER_PORT`, shared filesystem visibility, and `NCCL_TIMEOUT_SECOND`. Increasing `NCCL_TIMEOUT_SECOND` can help slow startup or slow data loading, but it does not fix wrong device visibility or missing shared data.

## W&B Behavior

`use_wandb` defaults to `true` in base configs. Demo scripts and this sub-skill's command builder explicitly pass `--use_wandb false` unless `--wandb true` is requested.

Only rank 0 initializes W&B and logs metrics. The trainer sets `WANDB_CONSOLE=off`, but W&B can still require credentials, network, and non-interactive login handling. Confirm project naming and credentials before enabling it.

## Run Directories and Checkpoints

The trainer appends a timestamp to `run_name` and creates a run directory under `base_dir`. It creates:

- `checkpoints/`: checkpoint files by step and EMA-suffixed checkpoints when EMA is enabled.
- `predictions/`: evaluation/prediction outputs from training evaluation.
- `structures/`: generated structures from evaluation.
- `dumps/`: intermediate dumps.
- `errors/`: problematic samples, data errors, and permutation errors.
- `config.yaml`: saved merged configuration for the run.

Checkpoint payloads contain model, optimizer, scheduler, and step. Loading is controlled by `load_checkpoint_path`, `load_ema_checkpoint_path`, `load_strict`, `load_params_only`, `skip_load_optimizer`, `skip_load_scheduler`, `skip_load_step`, and `load_step_for_scheduler`.

If a DDP checkpoint has `module.` prefixes and is loaded outside DDP, the trainer strips the prefix automatically.

## Kernel Choices

Demo training uses:

- `--triangle_attention cuequivariance`
- `--triangle_multiplicative cuequivariance`

Triangle attention options are `triattention`, `cuequivariance`, `deepspeed`, and `torch`. Triangle multiplicative options are `cuequivariance` and `torch`.

For `--triangle_attention deepspeed`, `runner.train` asserts that `CUTLASS_PATH` is set. The dependency stack can also be sensitive to DeepSpeed/Pydantic compatibility; repository tests document a `json_schema_input_schema` failure mode and suggest pinning Pydantic below 2.0 or updating DeepSpeed when that issue appears. Use `torch` kernels for conservative debugging.

## Training Cost Expectations

Training is disk-, GPU-, and wall-clock-heavy. Repository docs report full data at terabyte scale and recommend A100/H20/H100-class GPUs. Smaller GPUs can require reducing `diffusion_batch_size`, `train_crop_size`, dataset `base_info.max_n_token`, model block counts, evaluation frequency, or test-set size.

Do not suggest full training as a quick smoke test. Use `check_training_data_layout.py`, command builders, and help-only commands first.
