# Configuration

## Shipped configs

### `normal_lora.yaml`

- `flux_path`: `black-forest-labs/flux.1-fill-dev`
- `dtype`: `bfloat16`
- `train.batch_size`: `2`
- `train.accumulate_grad_batches`: `1`
- `train.gradient_checkpointing`: `true`
- `train.dataset.type`: `edit_with_omini`
- `train.dataset.path`: `parquet/*.parquet`
- `train.wandb.project`: `ICEdit`
- `train.lora_config`: standard LoRA only
- `train.optimizer.type`: `Prodigy`

### `moe_lora.yaml`

- `flux_path`: `../ckpt/FLUX.1-Fill-dev`
- `dtype`: `bfloat16`
- `train.batch_size`: `1`
- `train.accumulate_grad_batches`: `2`
- `train.gradient_checkpointing`: `false`
- `train.dataset.type`: `edit_with_omini`
- `train.dataset.path`: should resolve to the parquet shards used by the OmniEdit side of the mix
- `train.wandb.project`: `OminiControl`
- `train.lora_config`: adds MoE fields on top of the normal LoRA settings
- `train.optimizer.type`: `Prodigy`

The MoE YAML in the repo should be sanity-checked before launch: for `edit_with_omini`, the loader expects a parquet source, not a MagicBrush directory.

## Keys consumed by the current code

### Top level

| Key | Meaning | Notes |
| --- | --- | --- |
| `flux_path` | Base Flux Fill model id or local checkpoint path | Passed into `FluxFillPipeline.from_pretrained(...)` |
| `dtype` | Torch dtype name | Must resolve through `getattr(torch, dtype)` |
| `use_offset_noise` | Optional bool | Default `false` when absent |

### `model`

| Key | Meaning | Notes |
| --- | --- | --- |
| `union_cond_attn` | Model layout flag | Forwarded into `model_config` |
| `add_cond_attn` | Model layout flag | Forwarded into `model_config` |
| `latent_lora` | Enables LoRA on `x_embedder` | Used inside `tranformer_forward` |
| `use_sep` | Saves extra embedding tensors | Triggers `t5_embedding.pth` and `clip_embedding.pth` on save |

### `train`

| Key | Meaning | Notes |
| --- | --- | --- |
| `batch_size` | DataLoader batch size | Required |
| `accumulate_grad_batches` | Lightning gradient accumulation | Required |
| `dataloader_workers` | DataLoader workers | Required |
| `save_interval` | LoRA save cadence | Used by `TrainingCallback` |
| `sample_interval` | Sample-image cadence | Used by `TrainingCallback` |
| `max_steps` | Trainer step limit | Defaults to `-1` |
| `max_epochs` | Trainer epoch limit | Optional |
| `gradient_clip_val` | Lightning gradient clip | Defaults to `0.5` |
| `gradient_checkpointing` | Transformer checkpointing | Saves memory at speed cost |
| `save_path` | Output root | Defaults to `./output` |
| `wandb.project` | Wandb project name | Only used if `WANDB_API_KEY` is present |

### `train.dataset`

| Key | Meaning | Notes |
| --- | --- | --- |
| `type` | Dataset branch | Supported values: `edit`, `omini`, `edit_with_omini` |
| `path` | Dataset source | For `edit_with_omini`, this must be the parquet source; for `omini`, it is passed to `load_dataset(...)` |
| `condition_size` | Input side width / height | Used by the dataset wrappers |
| `target_size` | Target side width / height | Used by the dataset wrappers |
| `drop_text_prob` | Prompt dropout probability | Used by the dataset wrappers |
| `image_size` | Declared in the YAML examples | Not consumed by the current `train.py` path |
| `padding` | Declared in the YAML examples | Not consumed by the current `train.py` path |
| `drop_image_prob` | Declared in the YAML examples | Not consumed by the current `train.py` path |
| `specific_task` | Declared in the YAML examples | `OminiDataset` supports it, but `train.py` does not pass it through |
| `condition_type` | Declared in the YAML examples | Not read by `train.py`; the dataset objects already return their own condition type |

### `train.lora_config`

| Key | Meaning | Notes |
| --- | --- | --- |
| `r` | Base LoRA rank | Used by both launch paths |
| `lora_alpha` | Base LoRA scaling | Used by both launch paths |
| `init_lora_weights` | LoRA init mode | The shipped configs use `gaussian` |
| `target_modules` | Regex for target module names | Must match Flux transformer module names |
| `num_experts` | MoE expert count | MoE-only |
| `expert_rank` | Expert rank | MoE-only |
| `expert_alpha` | Expert scale | MoE-only |
| `top_k` | Expert routing width | MoE-only |

### `train.optimizer`

| Key | Meaning | Notes |
| --- | --- | --- |
| `type` | Optimizer family | Supported by code: `AdamW`, `Prodigy`, `SGD` |
| `params.lr` | Learning rate | The shipped configs use `1` |
| `params.use_bias_correction` | Prodigy option | Used only by Prodigy |
| `params.safeguard_warmup` | Prodigy option | Used only by Prodigy |
| `params.weight_decay` | Weight decay | Used by the shipped configs |

## Checkpoint and sample outputs

- `run_name` is timestamp-based.
- `save_path/<run_name>/config.yaml` stores the resolved config snapshot.
- `save_path/<run_name>/ckpt/<step>/` stores LoRA weights at every `save_interval`.
- `save_path/<run_name>/lora_<step>*` sample images are written at every `sample_interval`.
- `enable_checkpointing=False` means the run does not emit standard Lightning checkpoint files.

## Resume caveat

The current code path does not implement true LoRA resume: `OminiModel.init_lora(lora_path=...)` raises `NotImplementedError`. Treat the saved LoRA folders as export artifacts unless you extend the code.
