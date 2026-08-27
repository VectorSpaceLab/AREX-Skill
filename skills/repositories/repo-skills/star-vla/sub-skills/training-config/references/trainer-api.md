# Trainer API and utility behavior

This reference covers the trainer utilities and source behaviors most relevant to planning and debugging StarVLA training commands.

## `normalize_dotlist_args(args)`

The helper turns unknown CLI tokens into OmegaConf dotlist entries:

| Input tokens | Normalized dotlist |
| --- | --- |
| `--a.b value` | `a.b=value` |
| `--a.b=value` | `a.b=value` |
| `--flag` | `flag=true` |
| `orphan` | ignored |

Practical advice:

- Use explicit `--key=value` in generated commands.
- Use `--trainer.freeze_modules=` for an empty freeze list; do not leave an empty shell variable unquoted after `--trainer.freeze_modules`.
- For planner input, use `KEY=VALUE` without the leading dashes.

## `build_param_lr_groups(model, cfg)`

`build_param_lr_groups` creates optimizer parameter groups from `cfg.trainer.learning_rate`:

1. Read `base` LR, defaulting to `1e-4` if absent.
2. Parse `cfg.trainer.freeze_modules` as comma-separated module paths.
3. Resolve each freeze path from the model root and collect frozen parameter IDs.
4. For each non-`base` learning-rate key, resolve the module path and create a named parameter group excluding frozen parameters.
5. Put all remaining non-frozen parameters in a `base` group.

Operational implications:

- Learning-rate keys are module paths, not regexes.
- Freeze paths are also module paths relative to the built model.
- Frozen parameters are excluded from both specific and base LR groups.
- Missing freeze paths print warnings and continue.
- A missing LR-group path is not a reliable hard failure in the inspected utility; inspect logged LR groups and trainable parameter counts.

## `TrainerUtils.freeze_backbones(model, freeze_modules)`

`freeze_backbones` applies `requires_grad = False` to comma-separated module paths relative to the model. Example values:

```text
qwen_vl_interface
qwen_vl_interface.model.model.visual,dino_encoder
action_model.net
```

The trainer calls this before `accelerator.prepare`. If the path cannot be resolved, the source prints a warning and continues. For a new architecture, first inspect the model structure with [model-frameworks](../../model-frameworks/SKILL.md) before writing freeze/LR paths.

## Optimizer and scheduler setup

The common utility builds:

- AdamW optimizer.
- `betas`, `weight_decay`, and `eps` from `cfg.trainer.optimizer`.
- Transformers scheduler from `cfg.trainer.lr_scheduler_type`.
- Warmup and max step counts from `num_warmup_steps` and `max_train_steps`.
- `scheduler_specific_kwargs` passed through to the scheduler.

The utility uses fused AdamW only when CUDA is available. The local helper inside `train_starvla.py` uses `fused=True` directly in the inspected source, which reinforces that actual training recipes are GPU-oriented; do not treat CPU-only command planning as a full training validation.

## Losses and metrics

- `train_starvla.py` forwards VLA batches and backpropagates `action_loss`.
- `train_starvla_cotrain.py` forwards VLA batches for `action_loss` and VLM batches for `vlm_loss * trainer.loss_scale.vlm`.
- `train_starvlm.py` forwards only VLM batches and applies `trainer.loss_scale.vlm`.
- `trainer.loss_scale.vla` appears in source configs, but the inspected training loops do not multiply the action loss by it.
- LR metrics are logged as `learning_rate/{group_name}` for each optimizer group.
- VLA evaluation computes a simple action distance/MSE-style score on a current batch; it is not a benchmark evaluation.

## Checkpoint loading and saving

### Saving

At training start, main process writes:

- `config.full.yaml`: full merged config.
- `config.yaml`: accessed-config snapshot when access tracking is active.

At save intervals, main process writes one of:

- `checkpoints/steps_{N}_pytorch_model.pt`
- `checkpoints/steps_{N}_model.safetensors`

It also appends `{"steps": N}` to `summary.jsonl` and refreshes `config.yaml` when access tracking is active. At the end, it writes final weights under `final_model/`.

### Loading and reloading

`TrainerUtils.load_pretrained_backbones` supports:

- Full-model load when `reload_modules` is empty or absent. It calls `model.load_state_dict(checkpoint, strict=False)`.
- Partial load when `reload_modules` is comma-separated. Each module path must resolve from the model root; the source filters checkpoint keys by prefix and loads the sub-state with `strict=True`.
- `.safetensors` paths via `safetensors.torch.load_file`; other paths via `torch.load(..., map_location="cpu")`.

Source FAQ notes that StarVLA does not save optimizer state, so checkpoint resume/reload is mainly model-weight reload plus scheduler-step adjustment in the VLA-only latest-checkpoint path.

### Latest-checkpoint scan

The VLA-only trainer can scan `checkpoints/` for filenames matching:

```text
steps_{integer}_pytorch_model.pt
steps_{integer}_model.safetensors
```

It picks the highest integer step and uses that as `completed_steps`. If files are named differently, resume discovery will not find them.

## Distributed-safety helpers

The inspected CPU test evidence shows these paths are safe without an initialized `torch.distributed` process group:

- `TrainerUtils.print_trainable_parameters`.
- `TrainerUtils.load_pretrained_backbones` on a small CPU model.
- `prepare_data` functions when `build_dataloader` is mocked.
- `_reset_dataloader`, which only calls `sampler.set_epoch` when the sampler exposes it.

Actual training still requires the intended backend. The source loops use CUDA autocast and common launchers use Accelerate/DeepSpeed.
