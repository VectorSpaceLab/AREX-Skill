# Policy-training workflows

## Purpose

This reference covers the main ACT++ training and evaluation pathways: ACT/CNNMLP/Diffusion policy training, policy evaluation, and the latent VQ model pass used after ACT training.

## 1) Training entry point

The main CLI is `imitate_episodes.py`. It collects all training configuration, dataset loading, validation cadence, checkpoint saving, and optional evaluation in one script.

### Key flags

- `--task_name`: selects the dataset/task config.
- `--ckpt_dir`: checkpoint and result directory.
- `--policy_class`: `ACT`, `CNNMLP`, or `Diffusion`.
- `--batch_size`, `--seed`, `--num_steps`, `--lr`: core optimization parameters.
- `--eval_every`, `--validate_every`, `--save_every`: step-based scheduling.
- `--resume_ckpt_path`: optional resume checkpoint.
- `--skip_mirrored_data`: skip mirrored episodes during loading.
- `--temporal_agg`: enable temporal action aggregation during eval.
- `--load_pretrain`: load a hard-coded pretraining checkpoint path from source; use only if that path exists or the code is patched.
- ACT-specific flags: `--kl_weight`, `--chunk_size`, `--hidden_dim`, `--dim_feedforward`, `--use_vq`, `--vq_class`, `--vq_dim`, `--no_encoder`.

### Output artifacts

Training writes these files into `ckpt_dir`:

- `config.pkl`
- `dataset_stats.pkl`
- `policy_step_<step>_seed_<seed>.ckpt`
- `policy_last.ckpt`
- `policy_best.ckpt`
- `result_policy_last.txt` after evaluation
- rollout videos when evaluation saving is enabled

### Data flow

1. Task config supplies dataset directory and camera names.
2. `utils.load_data` builds train/validation dataloaders.
3. The selected policy class wraps the DETR or diffusion backbone.
4. Training loops over `num_steps` and validates on schedule.
5. Evaluation reloads `policy_last.ckpt` and `dataset_stats.pkl`, then runs rollouts.

## 2) ACT and CNNMLP

- ACT uses a DETR-VAE model and a KL weight.
- CNNMLP uses ResNet image features and an MLP head.
- Both normalize actions by mean/std and use the same 14-D joint-state convention plus 2-D base action when present.

Common user expectations:

- `chunk_size` is the action-sequence horizon for ACT and Diffusion.
- `camera_names` must match the dataset/task config exactly.
- `qpos` normalization and action normalization are applied inside the dataset loader.

## 3) Diffusion Policy

Diffusion policy uses visual encoders from robomimic, a `ConditionalUnet1D` noise predictor, and a DDIM scheduler. The training path normalizes actions to `[-1, 1]` and uses image augmentation.

Important dependency note:

- The policy wrapper expects `robomimic.algo.diffusion_policy` to expose `replace_bn_with_gn` and `ConditionalUnet1D`.
- The repository code does not ship that external dependency itself.
- If the import fails, stop and fix the robomimic build before assuming the training stack is usable.

## 4) Latent model pass

`train_latent_model.py` trains a `Latent_Model_Transformer` on VQ codes from a previously trained ACT checkpoint.

Workflow shape:

1. Load a trained ACT checkpoint.
2. Use `policy.vq_encode` to create ground-truth latent labels.
3. Train the latent transformer with cross-entropy.
4. Save `latent_model_last.ckpt` and `latent_model_epoch_*` checkpoints.

This workflow is separate from the main ACT policy training and requires an existing VQ-enabled ACT checkpoint.

## 5) Validation checklist

- Confirm the checkpoint directory exists and is writable.
- Confirm CUDA is available before launching training.
- Confirm the dataset task name maps to the expected dataset directory and camera list.
- Confirm the dataset contains the expected HDF5 schema before launching long runs.
- If eval or rollout fails, check whether the action/observation normalization files in `ckpt_dir` exist and correspond to the same dataset family.
