# StarVLA configuration reference

This reference describes how future agents should inspect and edit StarVLA training YAMLs before planning a launch. It distills source behavior from the StarVLA training entry points, trainer utilities, DeepSpeed configs, docs, examples, and CPU-safe tests.

## Configuration load and precedence

StarVLA training entry points load one YAML with OmegaConf, normalize remaining CLI tokens into dotlist entries, then merge:

1. Base YAML from `--config_yaml`.
2. CLI dotlist overrides produced by `normalize_dotlist_args`.

The CLI layer has higher precedence than the YAML. For duplicate dotlist keys, the later value wins under OmegaConf merge semantics. Dotlist values are parsed by OmegaConf, so strings such as `false`, `12`, `[128,128]`, and `1.0e-05` become typed values when OmegaConf can parse them.

The training entry points use the underscore option `--config_yaml`. This skill's planner script accepts `--config-yaml` for convenience but emits StarVLA's underscore form.

### Training CLI token normalization

`normalize_dotlist_args` accepts forms commonly used in the source launchers:

- `--framework.name QwenGR00T` becomes `framework.name=QwenGR00T`.
- `--framework.name=QwenGR00T` becomes `framework.name=QwenGR00T`.
- `--is_debug` becomes `is_debug=true`.
- Orphaned non-option tokens are ignored.

For safer planning, prefer explicit `KEY=VALUE` entries. This avoids accidental `flag=true` behavior when an intended value is empty, such as `--trainer.freeze_modules` followed immediately by the next option.

### Checkpoint/policy override syntax

Checkpoint loading and policy serving use a stricter `config_overrides` contract in the framework layer:

- Overrides must be a sequence of `KEY=VALUE` strings.
- A bare string is rejected with a type error.
- Entries missing `=` are rejected with a value error.
- Overrides are applied after the checkpoint's saved config and do not resolve unrelated interpolations.

Route serving-time override behavior to [policy-deployment](../../policy-deployment/SKILL.md), but use the same `KEY=VALUE` habit while planning training.

## Top-level YAML fields

Typical StarVLA YAMLs contain:

```yaml
run_id: starvla
run_root_dir: results/Checkpoints
seed: 42
wandb_entity: your_wandb_entity
wandb_project: starvla
is_debug: false
version_id: "0.21"
```

`run_root_dir` and `run_id` determine `output_dir = run_root_dir/run_id`. Choose a unique `run_id` before launching; overwriting an existing non-empty run directory can mix checkpoints and logs.

## `framework` section

Training YAMLs configure the model family under `framework`. Keep model-family decisions in [model-frameworks](../../model-frameworks/SKILL.md); for training planning, check only the fields that affect launch validity:

- `framework.name`: registry/framework name to build.
- `framework.qwenvl.base_vlm`: base VLM or action-extended VLM checkpoint location/name.
- `framework.qwenvl.attn_implementation`: often `flash_attention_2`; use a non-flash implementation only if the selected framework supports it.
- `framework.action_model.action_dim` and `state_dim`: must match data modality dimensions.
- `framework.action_model.action_horizon`: canonical action chunk length in current configs.
- `framework.action_model.future_action_window_size`: legacy alias; when compatibility normalization is used, it should equal `action_horizon - 1`.

`train_starvla.py` and `train_starvla_cotrain.py` call `apply_config_compat`, which stamps `version_id: "0.21"`, fills legacy aliases, and makes `action_horizon` canonical when both horizon keys disagree. `train_starvlm.py` does not perform the same compatibility call in the inspected source, so VLM-only YAMLs should already be compatible with the selected framework.

## `datasets` section

The training entry points read dataset settings but do not define registries. Route registry and layout problems to [data-integration](../../data-integration/SKILL.md).

Common fields:

```yaml
datasets:
  vla_data:
    dataset_py: lerobot_datasets
    data_root_dir: playground/Datasets/LEROBOT_DATA
    data_mix: libero_all
    per_device_batch_size: 16
    action_type: delta_qpos
    video_backend: torchvision_av
    load_all_data_for_training: true
  vlm_data:
    dataset_py: vlm_datasets
    dataset_use: sharegpt4v_coco
    dataformat: llava_json
    per_device_batch_size: 4
```

Entry-point expectations:

- `train_starvla.py`: requires `datasets.vla_data`.
- `train_starvla_cotrain.py`: requires both `datasets.vla_data` and `datasets.vlm_data`.
- `train_starvlm.py`: requires `datasets.vlm_data` and uses `dataset_use` in logging.

When VLA data is built, the dataloader saves `dataset_statistics.json` into `output_dir`. Serving a checkpoint later relies on this file; if it is absent, the training job likely failed before or during VLA dataloader construction.

## `trainer` section

Frequently used trainer fields:

```yaml
trainer:
  max_train_steps: 100000
  num_warmup_steps: 5000
  save_interval: 5000
  eval_interval: 100
  logging_frequency: 10
  learning_rate:
    base: 2.5e-05
    qwen_vl_interface: 1.0e-05
    action_model: 1.0e-04
  lr_scheduler_type: cosine_with_min_lr
  scheduler_specific_kwargs:
    min_lr: 1.0e-06
  freeze_modules: "qwen_vl_interface"
  loss_scale:
    vla: 1.0
    vlm: 0.1
  gradient_clipping: 1.0
  gradient_accumulation_steps: 4
  optimizer:
    name: AdamW
    betas: [0.9, 0.95]
    eps: 1.0e-08
    weight_decay: 1.0e-08
  save_format: pt
```

Important source-backed details:

- `learning_rate` is a mapping of module path to learning rate. `base` catches all parameters not assigned to a specific module and not frozen.
- `freeze_modules` is a comma-separated list of module paths relative to the built model, for example `qwen_vl_interface` or `qwen_vl_interface.model.model.visual,dino_encoder`.
- The inspected VLA and co-train loops multiply VLM loss by `trainer.loss_scale.vlm`. `trainer.loss_scale.vla` is present in configs but is not applied to the VLA action loss in the inspected loops.
- `gradient_accumulation_steps` is normally an Accelerate/DeepSpeed concern. Source configs include it in YAML, while the runtime `Accelerator` reports the effective accumulation setting.
- `save_format` supports `pt` and `safetensors` in the trainer checkpoint writers.

## Accelerate and DeepSpeed configs

Representative source configs under `starVLA/config/deepseeds/` include:

- `deepspeed_zero2.yaml`: Accelerate config pointing to `ds_config.yaml`, `distributed_type: DEEPSPEED`, `num_machines: 1`, `num_processes: 8`.
- `ds_config.yaml`: JSON-style DeepSpeed ZeRO-2 settings, BF16 enabled, auto train batch sizes, no CPU optimizer offload.
- `deepspeed_zero3.yaml`: Accelerate config pointing to `zero3.yaml`.
- `zero3.yaml`: DeepSpeed ZeRO-3 JSON-style config with auto precision, auto accumulation, and parameter-gather-on-save.
- `zero2.yaml`: full Accelerate ZeRO-2 config with BF16 mixed precision and `num_processes: 8`.

When planning a launch, match all of these:

1. `--num_processes` equals the intended number of local worker processes/GPUs.
2. The Accelerate config's `num_processes` is consistent, or the CLI override is intentional.
3. ZeRO stage matches model size and memory budget.
4. BF16/FP16 choices match hardware support.
5. Multi-node launches add `--main_process_ip`, `--main_process_port`, `--machine_rank`, `--num_machines`, and total `--num_processes` consistently.

## Output and checkpoint layout

The training scripts create:

```text
{run_root_dir}/{run_id}/
  config.full.yaml        # complete merged config, saved early on main process
  config.yaml             # accessed-config snapshot, updated at checkpoints
  dataset_statistics.json # saved after VLA dataloader construction
  summary.jsonl           # appended with saved checkpoint steps
  wandb/                  # W&B local files if logging is enabled
  checkpoints/
    steps_{N}_pytorch_model.pt
    steps_{N}_model.safetensors
  final_model/
    pytorch_model.pt
    model.safetensors
```

VLA-only resume (`train_starvla.py`) can scan `checkpoints/` for the latest `steps_{N}_pytorch_model.pt` or `steps_{N}_model.safetensors` when `trainer.is_resume` is true. Source FAQ notes that StarVLA checkpoints do not save optimizer state; resume/reload behavior restores model weights and adjusts scheduler steps, but it is not a full optimizer-state resume.
