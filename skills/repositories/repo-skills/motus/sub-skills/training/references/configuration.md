# Configuration contract

Motus training loads one YAML file with OmegaConf in `train/train.py`. The
command-line values are applied after YAML loading, so these CLI overrides have
higher precedence:

| CLI flag | Effective field |
|---|---|
| `--checkpoint_dir DIR` | `system.checkpoint_dir` |
| `--report_to VALUE` | `logging.report_to` |
| `--wandb_project NAME` | `logging.wandb_project` |
| `--run_name NAME` | `logging.run_name` |
| `--log_level LEVEL` | process logging setup (not the YAML `system.log_level`) |
| `--deepspeed JSON` | Accelerator DeepSpeed plugin; not a YAML field |

The parser also accepts `--config`, `--local_rank`; `local_rank` is parsed for
launcher compatibility, while distributed setup primarily consumes the
`RANK`, `WORLD_SIZE`, and `LOCAL_RANK` environment variables supplied by
`torchrun`.

## Three-stage intent and mode

The repository describes the training pyramid as follows:

| Intent | Typical config/data | What is trained |
|---|---|---|
| Foundation models | external Wan2.2 and Qwen3-VL checkpoints | pretrained inputs, not a Motus launch itself |
| Stage 1 VGM training | Levels 2, 3, and 5; often a video-oriented preparation | only the VGM/WAN component |
| Stage 2 Motus pretraining | `configs/latent_action.yaml`, `latent_action` data, Levels 2–5 | all three experts with latent actions |
| Stage 3 Motus SFT | embodiment config such as `robotwin.yaml`, Levels 6 | all three experts with target-robot actions |

`training_mode` is a top-level value accepted by `MotusConfig` and should be
`pretrain` or `finetune` (the source defaults to `finetune` when absent). The
provided latent-action config explicitly sets `pretrain`; the embodiment
configs omit it and therefore use `finetune`. In pretrain mode, the model uses
no register tokens; in finetune mode the model keeps its default four
registers. Do not infer Stage 1 from the presence of a dataset name: the
visible training entry point is the three-expert Motus trainer, so confirm any
Stage 1-only change against the source model before launching.

The derived value is:

```text
action_chunk_size = common.num_video_frames * common.video_action_freq_ratio
```

`train/train.py` writes this derived field into the in-memory config. It is not
necessarily present in the input YAML.

## Required hierarchy

### `common`

- `action_dim`, `state_dim`: robot action/state dimensions; example configs use
  14.
- `num_video_frames`: target video frame count; examples use 8.
- `video_height`, `video_width`: resized training dimensions; examples use
  384 × 320.
- `global_downsample_rate`: temporal downsampling used by the selected dataset.
- `video_action_freq_ratio`: action steps per video frame. Together with frame
  count it determines `action_chunk_size`.

Check that the dataset and model agree on dimensions and sampling. A mismatch
usually appears later as tensor-shape errors, not as a friendly parser error.

### `dataset`

The factory currently recognizes `robotwin`, `ac_one`, `latent_action`,
`aloha_agilex_2`, and `lerobot`.

Common keys:

- `type`: one of the supported factory values.
- `dataset_dir`: a path for embodiment datasets, or a list for
  `latent_action`. `lerobot` uses `dataset.params.repo_id` and `root`.
- `max_episodes`: `null` for all or a small integer for bounded debugging.
- `image_aug`: augmentation for training; validation disables it.
- `task_mode` and `task_name`: used by robot/embodiment datasets. `task_mode`
  may be `single` or `multi`; `task_name: null` means all tasks in the
  multi-task examples. `robotwin` additionally has `data_mode` (`clean`,
  `randomized`, or `both`) and optional `randomized_limit_per_task`.
- `params`: dataset-specific extra values passed through to the dataset class.

Dataset layouts and conversion are intentionally out of scope; use the sibling
[data-preparation skill](../../data-preparation/SKILL.md).

### `model`

`model.wan`:

- `config_path`: directory containing the WAN architecture `config.json`.
- `checkpoint_path`: WAN weights directory or supported weight file.
- `vae_path`: WAN 2.2 VAE `.pth` required for video encoding/decoding.
- `precision`: examples use `bfloat16`.

`model.vlm`:

- `checkpoint_path`: Qwen3-VL checkpoint directory.
- `precision`: examples use `bfloat16`.
- `frozen`: intended VLM freeze setting in examples; confirm behavior if
  changing it, because the training entry point constructs the model from the
  config and the VLM is used for understanding features.

Expert and objective fields:

- `action_expert.hidden_size` (example 1024; must be a multiple of 128 for the
  configured head dimension), `ffn_dim_multiplier`, `norm_eps`.
- `und_expert.hidden_size` (example 512), `ffn_dim_multiplier`, `norm_eps`, and
  `und_expert.vlm.input_dim` (example 2048) plus `projector_type` (example
  `mlp3x_silu`).
- `time_distribution.timestep_sample_method`: `logit_normal` or `uniform`;
  `sigmoid_scale`, `min_t`, and `max_t` define timestep sampling.
- `loss_weights.video_loss_weight` and `action_loss_weight`.
- `inference.num_inference_timesteps` is not a training launch control; leave
  inference-specific tuning to [model-inference](../../model-inference/SKILL.md).
- `ema` is present in examples but marked not currently used.
- `load_pretrained_backbones` is an internal override. The entry point forces it
  to `false` whenever either `resume.checkpoint_path` or a non-null
  `finetune.checkpoint_path` is present. Do not rely on a YAML `true` to defeat
  that safety behavior.

### `training`

- `batch_size`: per-process DataLoader batch size in the source path.
- `max_steps`: stopping step count; the loop saves a final checkpoint on rank 0.
- `learning_rate`, `weight_decay`; optional `wan_learning_rate` creates a
  separate WAN parameter group and otherwise falls back to `learning_rate`.
- Scheduler values: `scheduler_type`, `warmup_steps`, and either the linear
  scheduler's `cycle_length`, `f_max`, `f_min`, or the latent-action config's
  `diffusers_cosine`, `lr_schedule_steps`, and `min_lr`.
- `grad_clip_norm`, `use_amp`, `find_unused_parameters`.
- Optional `gradient_accumulation_steps` is read by Accelerate and defaults to
  1 if absent. Do not assume a value from DeepSpeed unless it is explicit and
  consistent with the launcher.

### `system`, `logging`, and checkpoint selectors

`system` contains `checkpoint_dir`, `log_interval`, `save_interval`,
`val_interval`, `num_workers`, and `pin_memory`. The code appends the YAML file
stem (for example `robotwin`) and then `logging.run_name` below the base
checkpoint directory. Rank 0 creates the resulting directory.

`logging.report_to` is one of `wandb`, `tensorboard`, `all`, or `none`:

- `wandb`: rank 0 calls `wandb.init` and step logging uses `wandb.log`.
- `tensorboard`: rank 0 writes `tensorboard_logs` (or the configured
  `tensorboard_log_dir`) and scalar/evaluation summaries.
- `all`: expanded to both backends; both dependencies and credentials/settings
  must be ready.
- `none`: no reporting backend; this is useful for isolated parser or launch
  smoke checks, but it does not make model execution CPU-safe.

`wandb_project` and `run_name` are metadata, not checkpoint selectors.

`resume`:

```yaml
resume:
  checkpoint_path: null
  reset_scheduler: false  # optional; latent_action sets false explicitly
```

A non-null path is passed to `Accelerator.load_state`, restoring model,
optimizer, scheduler, dataloader, and RNG state. The trainer extracts a step
from a path matching `step_<number>` and continues until `training.max_steps`.
If `reset_scheduler` is true, the custom scheduler is reset to the current YAML
schedule; otherwise its progress is synchronized to the resumed step. Use a
checkpoint directory produced by the same distributed setup where possible.

`finetune`:

```yaml
finetune:
  checkpoint_path: null
```

In `training_mode: finetune`, a non-null value is loaded *partially* by
`load_pretrain_weights`. For a directory, the source tries
`pytorch_model/mp_rank_00_model_states.pt` and then
`mp_rank_00_model_states.pt`; it accepts either a checkpoint containing
`module` or a direct state dict. It deliberately skips
`action_expert.input_encoder.*` and `action_expert.decoder.*`, because these
can differ between state/latent-action and action fine-tuning. It is not a full
optimizer-state resume.

## Mode matrix

Use exactly one of these intentional states:

| Purpose | `training_mode` | `resume.checkpoint_path` | `finetune.checkpoint_path` | Backbone effect |
|---|---|---|---|---|
| Stage 2 / latent-action pretraining from WAN/VLM | `pretrain` | null | null | load WAN and VLM paths |
| Stage 3 from a Stage 2 Motus checkpoint | `finetune` | null | Stage 2 checkpoint | skip initial WAN/VLM reload; partial Motus load |
| Continue interrupted same run | usually same as prior run | checkpoint step directory | null | restore full Accelerator state; WAN/VLM are not reloaded |
| Deliberate scratch experiment | explicit mode | null | null | load WAN and VLM paths |

The source does not reject both selectors being non-null. Treat that as a
configuration error and clear one before launch: the entry point will disable
backbone loading, then separately attempt both a partial fine-tune load and a
full resume, which is ambiguous and unsafe.

## DeepSpeed semantics

The `--deepspeed PATH` value is passed to Accelerate's
`DeepSpeedPlugin(hf_ds_config=PATH)`. The bundled `configs/zero1.json` and
`configs/zero2.json` both enable bf16 and set `train_micro_batch_size_per_gpu`,
`train_batch_size`, and `gradient_accumulation_steps` to `auto`. Both currently
say `zero_optimization.stage: 1`; the file named `zero2.json` adds
`reduce_scatter: true` but is not ZeRO stage 2 as written. Do not describe or
select it as stage 2 without correcting and validating the JSON.

`overlap_comm`, `contiguous_gradients`, `reduce_scatter`, and `sub_group_size`
are memory/communication choices, not model hyperparameters. Keep the JSON
consistent with the actual GPU count and Accelerate version. A missing
`--deepspeed` means Accelerator is still used for bf16/multi-process handling,
but no DeepSpeed sharding is requested.

## Safe validation checklist

Before launching, check without constructing the model:

1. YAML parses as a mapping and contains `common`, `dataset`, `model`,
   `training`, `system`, `logging`, `resume`; require `finetune` when using its
   selector.
2. `dataset.type` is supported; `training_mode` is absent or in
   `{pretrain, finetune}`; `logging.report_to` is in its four choices.
3. All common dimensions, batch/step/interval/worker counts, learning rates,
   and downsample/frequency values are positive where required; hidden size is
   divisible by 128.
4. `0 <= time_distribution.min_t < max_t <= 1` and the timestep method is
   recognized.
5. `resume` and `finetune` are not both non-null. If fine-tuning, mode must be
   `finetune`; if `pretrain`, do not silently attach a fine-tune checkpoint.
6. Existing local paths are readable: dataset roots, WAN config/checkpoint, VAE,
   VLM checkpoint, DeepSpeed JSON, and resume/fine-tune checkpoint. Missing
   model/data paths are blockers, not reasons to fall back to random weights.
7. Compute `action_chunk_size` and compare the selected dataset's action shape
   with `common.action_dim`.
8. On the target node, check `torch.cuda.is_available()`, GPU count, bf16
   support, free VRAM, `flash_attn` import, `deepspeed` import when requested,
   and NCCL visibility. Do not treat a CPU import pass as a training pass.

The bundled exporter intentionally filters only `common`,
`model.action_expert`, `model.und_expert`, `model.time_distribution`, and
`model.ema`, matching the source helper. It does not export dataset paths,
optimizer settings, logging metadata, or a complete restart config.
