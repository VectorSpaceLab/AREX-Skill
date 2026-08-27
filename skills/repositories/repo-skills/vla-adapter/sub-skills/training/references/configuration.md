# Configuration reference

This reference maps the bundled training command builder to the actual `FinetuneConfig` fields used by the fine-tune launcher. The values below are drawn from the installed package facts and the repo training scripts.

## Command-to-config mapping

The helper emits CLI flags that map 1:1 to `vla-scripts/finetune.py` fields. Path-like values are emitted as strings, and booleans are emitted as `True` / `False` so the launcher can parse them directly.

## `FinetuneConfig` fields

### Paths and dataset inputs

| Field | Default | Purpose |
| --- | --- | --- |
| `config_file_path` | `openvla/openvla-7b` | Config source for the adapter model. |
| `vlm_path` | `openvla/openvla-7b` | Base VLM or local model path. |
| `use_minivlm` | `False` | Use the MiniVLM loading path. |
| `resum_vla_path` | `openvla/openvla-7b` | Checkpoint root used when resuming. |
| `data_root_dir` | `datasets/rlds` | Root that contains the benchmark dataset. |
| `dataset_name` | `aloha_scoop_x_into_bowl` | Dataset name inside the root. |
| `run_root_dir` | `runs` | Root directory for logs and checkpoints. |
| `shuffle_buffer_size` | `100000` | Shuffle buffer for RLDS-style input. |

### Model shape and objective

| Field | Default | Purpose |
| --- | --- | --- |
| `use_l1_regression` | `True` | Train the continuous action head with L1 regression. |
| `use_diffusion` | `False` | Switch to diffusion-style action modeling. |
| `num_diffusion_steps` | `50` | Diffusion steps when diffusion is enabled. |
| `use_film` | `False` | Enable FiLM conditioning. |
| `num_images_in_input` | `1` | Number of images provided to the VLM. |
| `use_proprio` | `False` | Add proprioceptive state to the input. |
| `phase1_path` | `None` | Optional stage-1 checkpoint path. |

### Training schedule and checkpoints

| Field | Default | Purpose |
| --- | --- | --- |
| `batch_size` | `8` | Per-device batch size. |
| `learning_rate` | `0.0005` | AdamW learning rate. |
| `lr_warmup_steps` | `0.1` | Linear warmup fraction/step value used by the launcher. |
| `num_steps_before_decay` | `100000` | Step at which the LR scheduler decays by 10x. |
| `grad_accumulation_steps` | `1` | Gradient accumulation factor. |
| `max_steps` | `200000` | Maximum training steps. |
| `use_val_set` | `False` | Enable validation dataloader and periodic eval. |
| `val_freq` | `10000` | Validation frequency in steps. |
| `val_time_limit` | `180` | Validation wall-clock cap in seconds. |
| `save_freq` | `10000` | Checkpoint save frequency in steps. |
| `save_latest_checkpoint_only` | `False` | Overwrite the latest checkpoint instead of keeping all steps. |
| `resume` | `False` | Resume from a saved checkpoint. |
| `resume_step` | `None` | Step number that matches the checkpoint you are resuming from. |
| `image_aug` | `True` | Enable image augmentation. |
| `diffusion_sample_freq` | `50` | Sampling cadence when diffusion or L1 logging is enabled. |

### LoRA, full-save, and logging

| Field | Default | Purpose |
| --- | --- | --- |
| `use_lora` | `False` | Enable LoRA fine-tuning. |
| `lora_rank` | `32` | LoRA rank. |
| `lora_dropout` | `0.0` | LoRA dropout. |
| `merge_lora_during_training` | `False` | Merge LoRA weights into the checkpoint during training. |
| `use_fz` | `False` | Save the full model directly instead of a LoRA adapter. |
| `wandb_entity` | `your-wandb-entity` | W&B entity or team. |
| `wandb_project` | `your-wandb-project` | W&B project name. |
| `run_id_note` | `None` | Optional suffix for run naming. |
| `run_id_override` | `None` | Force a specific run ID. |
| `wandb_log_freq` | `10` | Logging cadence in gradient steps. |
| `use_pro_version` | `True` | Use the Pro policy variant. |
| `phase` | `Training` | Phase label passed into the action head. |

## Benchmark-specific defaults used by the helper

### LIBERO

- `data_root_dir`: `data/libero`
- `dataset_name`: one of `libero_spatial_no_noops`, `libero_object_no_noops`, `libero_goal_no_noops`, or `libero_10_no_noops`
- `num_images_in_input`: `2`
- `use_proprio`: `True`
- `use_lora`: `True`
- `use_fz`: `False`
- `use_minivlm`: `True`
- `image_aug`: `True`
- `merge_lora_during_training`: `True`
- `save_latest_checkpoint_only`: `False`
- `use_pro_version`: `True`

### CALVIN-style RLDS

- `data_root_dir`: the parent directory that contains `calvin_abc`
- `dataset_name`: `calvin_abc`
- `num_images_in_input`: `2`
- `use_proprio`: `True`
- `use_lora`: `True`
- `use_fz`: `False`
- `use_minivlm`: `True`
- `image_aug`: `True`
- `merge_lora_during_training`: `True`
- `save_latest_checkpoint_only`: `False`
- `use_pro_version`: `True`

### ALOHA TFDS

- `data_root_dir`: `datasets/cobot_aloha/tfds`
- `dataset_name`: `bowl_stack_and_shelf_aloha_realworld_50`
- `num_images_in_input`: `3`
- `use_proprio`: `True`
- `use_lora`: `True`
- `use_fz`: `False`
- `use_minivlm`: `True`
- `image_aug`: `True`
- `merge_lora_during_training`: `True`
- `save_latest_checkpoint_only`: `False`
- `use_pro_version`: `True`
- `wandb_project`: `vla_adapter`
- `WANDB offline mode`: the stock launcher sets `WANDB_MODE=offline` and `WANDB_CONSOLE=off`

## Action, tokenizer, and normalization constants

| Scope | Values |
| --- | --- |
| LIBERO / CALVIN | `NUM_ACTIONS_CHUNK=8`, `ACTION_DIM=7`, `PROPRIO_DIM=8`, `ACTION_PROPRIO_NORMALIZATION_TYPE=bounds_q99` |
| ALOHA | `NUM_ACTIONS_CHUNK=25`, `ACTION_DIM=14`, `PROPRIO_DIM=14`, `ACTION_PROPRIO_NORMALIZATION_TYPE=bounds` |
| Shared tokenizer | `NUM_TOKENS=64`, `ACTION_TOKEN_BEGIN_IDX=151386`, `STOP_INDEX=2`, `ActionTokenizer(bins=256)` |

## ALOHA launcher variables

`train_aloha.sh` uses shell variables rather than a dataclass. The helper mirrors the same names when it renders the command.

| Variable | Default | Meaning |
| --- | --- | --- |
| `ROOT_DIR` | `/path/to/root` | Storage root used to build model and dataset paths. |
| `DATA_ROOT_DIR` | `${ROOT_DIR}/datasets/cobot_aloha/tfds` | TFDS data directory. |
| `VLM_PATH` | `${ROOT_DIR}/ai_models/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b` | Vision-language backbone path. |
| `DATASET_NAME` | `bowl_stack_and_shelf_aloha_realworld_50` | ALOHA TFDS dataset name. |
| `WANDB_ENTITY` | `your-wandb-entity` | W&B entity or team. |
| `WANDB_PROJECT` | `vla_adapter` | W&B project name. |

### Built-in ALOHA hyperparameters

| Variable | Default |
| --- | --- |
| `batch_size` | `12` |
| `grad_accumulation_steps` | `1` |
| `learning_rate` | `2e-4` |
| `max_steps` | `10005` |
| `num_steps_before_decay` | `5000` |
| `save_freq` | `2000` |
| `lr_warmup_steps` | `0` |
| `num_images_in_input` | `3` |
| `lora_rank` | `64` |
| `use_film` | `False` |
| `use_proprio` | `True` |
| `use_lora` | `True` |
| `use_fz` | `False` |
| `use_minivlm` | `True` |
| `image_aug` | `True` |
| `save_latest_checkpoint_only` | `False` |
| `merge_lora_during_training` | `True` |
| `use_pro_version` | `True` |
| `WANDB_CONSOLE` | `off` |
| `WANDB_MODE` | `offline` |

## ALOHA dataset registration note

The bundled ALOHA setup helper registers a bimanual TFDS dataset with:

- `image_obs_keys`: primary camera, left wrist, and right wrist
- `state_encoding`: `JOINT_BIMANUAL`
- `action_encoding`: `JOINT_POS_BIMANUAL`

That is the expected shape for the fine-tune command emitted by the helper.
