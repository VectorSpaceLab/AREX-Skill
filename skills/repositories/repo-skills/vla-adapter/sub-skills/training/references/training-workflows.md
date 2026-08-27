# Training workflows

This reference describes commands for an external native checkout. The helper
only renders commands; it never launches training. Set the root and enter it
before reviewing or running a native command:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
```

## Command shape

The bundled script prints a `torchrun` invocation for the native
`vla-scripts/finetune.py`; it is not that entrypoint.

```bash
cd <absolute-repo-root> && CUDA_VISIBLE_DEVICES=0 torchrun --standalone --nnodes 1 --nproc-per-node 1 vla-scripts/finetune.py \
  --vlm_path <vlm-path> \
  --config_file_path <config-file-path> \
  --data_root_dir <data-root-dir> \
  --dataset_name <dataset-name> \
  --run_root_dir <run-root-dir> \
  --use_film False \
  --num_images_in_input <1-or-3> \
  --use_proprio True \
  --use_l1_regression True \
  --use_diffusion False \
  --use_lora True \
  --use_fz False \
  --use_minivlm True \
  --image_aug True \
  --num_steps_before_decay <steps> \
  --max_steps <steps> \
  --save_freq <steps> \
  --save_latest_checkpoint_only False \
  --merge_lora_during_training True \
  --batch_size <per-device-batch> \
  --grad_accumulation_steps <accum> \
  --learning_rate 2e-4 \
  --lora_rank 64 \
  --use_pro_version True \
  --wandb_entity <entity> \
  --wandb_project <project>
```

## Benchmark recipes

### LIBERO

Use this recipe for `libero_spatial_no_noops`, `libero_object_no_noops`, `libero_goal_no_noops`, or `libero_10_no_noops`.

- `--data_root_dir data/libero`
- `--num_images_in_input 2`
- `--use_proprio True`
- `--use_minivlm True`
- `--use_pro_version True` is recommended
- `--use_lora True`, `--use_fz False`
- `--image_aug True`
- `--merge_lora_during_training True`
- `--save_latest_checkpoint_only False`

### CALVIN-style RLDS

Use this recipe for the CALVIN RLDS dataset.

- `--dataset_name calvin_abc`
- `--data_root_dir` should point to the parent directory that contains `calvin_abc`
- `--num_images_in_input 2`
- `--use_proprio True`
- `--use_minivlm True`
- `--use_pro_version True` is recommended
- `--use_lora True`, `--use_fz False`
- `--image_aug True`
- `--merge_lora_during_training True`
- `--save_latest_checkpoint_only False`

### ALOHA TFDS

Use this recipe for TFDS data prepared through the ALOHA setup helper.

- `--dataset_name bowl_stack_and_shelf_aloha_realworld_50` by default
- `--data_root_dir datasets/cobot_aloha/tfds`
- `--num_images_in_input 3`
- `--use_proprio True`
- `--use_minivlm True`
- `--use_pro_version True` is recommended
- `--use_lora True`, `--use_fz False`
- `--image_aug True`
- `--merge_lora_during_training True`
- `--save_latest_checkpoint_only False`
- The stock launcher also sets `WANDB_MODE=offline` and `WANDB_CONSOLE=off`
- The stock launcher uses 4 GPUs and writes outputs under `outputs/<dataset_name>/<MODE>-<timestamp>/`

## GPU profiles

The helper applies these profiles to LIBERO and CALVIN-style runs. ALOHA keeps the stock launcher defaults unless you manually override the emitted batch or accumulation values.

| Profile | Batch size | Grad accumulation | Intended VRAM | Notes |
| --- | --- | --- | --- | --- |
| `tiny` | `1` | `8` | 10-12 GB | README example uses `num_steps_before_decay=400000` and `max_steps=400005`; good for the smallest cards. |
| `low` | `4` | `4` | 24 GB | README example uses `num_steps_before_decay=200000` and `max_steps=200005`. |
| `medium` | `8` | `2` | 32-48 GB | README example uses `num_steps_before_decay=200000` and `max_steps=200005`. |
| `large` | `16` | `1` | 80 GB+ multi-GPU | README example uses `num_steps_before_decay=150000` and `max_steps=150005`; the Pro checkpoint note separately reports a 100000-step 4×H100 run. |

### Memory notes from the README

- `tiny` is described as fitting on roughly 9.6 GB when `batch_size=1` and `lora_rank=64`.
- `low` is described as using nearly 20 GB.
- `medium` is described as using nearly 29 GB.
- `large` is the multi-GPU recipe used for the reported H100 runs.

## Checkpoints and logging

- The run root stores `config.yaml`, `config.json`, dataset statistics, and checkpoints.
- When `save_latest_checkpoint_only=False`, each save lands in a step-specific directory named like `<run_root_dir>/<run_id>--<step>_chkpt`.
- When `save_latest_checkpoint_only=True`, the latest checkpoint is overwritten in the run root.
- With LoRA enabled, the checkpoint also contains a `lora_adapter/` directory.
- If `merge_lora_during_training=True`, the merged model is written alongside the adapter state; this can be slow on some machines.
- ALOHA training runs in offline W&B mode by default.

## Resume workflow

To resume a previous run, add these fields to the generated command manually:

- `--resume True`
- `--resume_step <step>`
- `--resum_vla_path <checkpoint-root>`

Cautions:

- `resume_step` must match the checkpoint suffix.
- If the run used `save_latest_checkpoint_only=False`, point `resum_vla_path` at the step-specific checkpoint directory.
- If the run used `save_latest_checkpoint_only=True`, point `resum_vla_path` at the run root itself.
- The helper does not infer resume values automatically, because the checkpoint root is user-specific.

## LoRA, Pro, and full-save notes

- `use_lora=True` is the default fine-tuning path.
- `use_pro_version=True` is the recommended policy variant for the paper-style recipes.
- `use_fz=True` tells the launcher to save the full model directly instead of a LoRA adapter.
- `use_fz` does not expose the backbone-freeze stages from the general VLA trainer; those stages live in the separate `vla-scripts/train.py` pipeline.
- If `merge_lora_during_training=False`, merge later with the offline LoRA merge helper after training finishes.

## Offline LoRA merge

If checkpoint merging during training is too slow, keep the adapter checkpoint and merge it later with the offline merge helper. Pass the base checkpoint and the LoRA checkpoint directory, then save the merged result back into the same checkpoint directory.
