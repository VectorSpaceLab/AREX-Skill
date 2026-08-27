# Training workflows

Use this reference to select a StarVLA training entry point and produce a launch plan. Do not run the plan unless the user has explicitly requested execution and the required GPU/DeepSpeed/data environment is ready.

## Entry-point selection

| Entry point | Use when | Data needed | Losses used | Notes |
| --- | --- | --- | --- | --- |
| `starVLA/training/train_starvla.py` | Fine-tune a VLA policy on robot/action data. | `datasets.vla_data` | `action_loss` | Calls config compatibility normalization; has the most complete latest-checkpoint scan for `trainer.is_resume`. |
| `starVLA/training/train_starvla_cotrain.py` | Train VLA action behavior while also training the VLM interface on VLM data. | `datasets.vla_data` and `datasets.vlm_data` | `action_loss` plus VLM loss scaled by `trainer.loss_scale.vlm` | Handles DeepSpeed gradient accumulation through the DeepSpeed engine when needed. |
| `starVLA/training/train_starvlm.py` | Tune VLM behavior only. | `datasets.vlm_data` | VLM loss scaled by `trainer.loss_scale.vlm` | No-op action evaluation; W&B init is always called but can run in disabled mode. |

Architecture names, framework internals, action-head semantics, and checkpoint compatibility belong in [model-frameworks](../../model-frameworks/SKILL.md). Dataset registry and LeRobot layout belong in [data-integration](../../data-integration/SKILL.md).

## Launch anatomy

A standard single-machine launch has this shape:

```bash
WANDB_MODE=disabled TOKENIZERS_PARALLELISM=false \
accelerate launch \
  --config_file starVLA/config/deepseeds/deepspeed_zero2.yaml \
  --num_processes 8 \
  starVLA/training/train_starvla.py \
  --config_yaml path/to/config.yaml \
  --framework.name=QwenGR00T \
  --datasets.vla_data.data_root_dir=path/to/lerobot_data \
  --datasets.vla_data.data_mix=libero_all \
  --run_root_dir=results/Checkpoints \
  --run_id=my_run
```

Key points:

- Use `--config_file` for the Accelerate/DeepSpeed config.
- Use `--config_yaml` for the StarVLA training YAML.
- Put extra StarVLA config changes after `--config_yaml` as dotlist overrides.
- Prefer `--key=value` style for overrides so empty values remain explicit, for example `--trainer.freeze_modules=`.
- Set `WANDB_MODE=disabled` or `WANDB_DISABLED=true` when online logging should not happen.

Use the bundled planner to generate a command without executing it:

```bash
python skills/disco/star-vla/sub-skills/training-config/scripts/plan_training_command.py \
  --config-yaml path/to/config.yaml \
  --entrypoint vla \
  --num-processes 2 \
  --override run_id=dry_run_plan \
  --override trainer.max_train_steps=10 \
  --override trainer.freeze_modules=
```

The planner validates `KEY=VALUE` override shape and prints a shell-quoted command plan only.

## Multi-node anatomy

Source launchers show this Accelerate shape for schedulers or multi-node environments:

```bash
accelerate launch \
  --config_file starVLA/config/deepseeds/deepspeed_zero2.yaml \
  --main_process_ip "$MASTER_ADDR" \
  --main_process_port "$MASTER_PORT" \
  --machine_rank "$MACHINE_RANK" \
  --num_machines "$NUM_MACHINES" \
  --num_processes "$TOTAL_PROCESSES" \
  starVLA/training/train_starvla.py \
  --config_yaml path/to/config.yaml \
  --run_root_dir results/Checkpoints \
  --run_id distributed_run
```

Before launching, verify the scheduler variables, networking, NCCL settings, and DeepSpeed stage outside this skill. Keep site-specific interface names and cluster settings out of reusable command snippets.

## VLA-only policy training checklist

1. Pick the framework and base model with [model-frameworks](../../model-frameworks/SKILL.md).
2. Confirm `datasets.vla_data.dataset_py`, `data_root_dir`, `data_mix`, batch size, and modality/action dimensions with [data-integration](../../data-integration/SKILL.md).
3. Confirm `framework.action_model.action_horizon`, `action_dim`, and `state_dim` match the dataset action/state shapes.
4. Choose `trainer.learning_rate` groups and `freeze_modules` paths. Use module paths relative to the built model.
5. Plan `run_root_dir` and a unique `run_id`.
6. Disable W&B if the user does not want online logging.
7. Generate a dry-run plan with `plan_training_command.py`.
8. Only then run the command in the prepared StarVLA environment with the intended backend.

## VLA + VLM co-training checklist

Co-training adds these checks:

- `datasets.vlm_data.dataset_py` should be `vlm_datasets` for the standard VLM loader.
- `datasets.vlm_data.dataset_use` can be a single dataset or a comma-separated mixture string from the source examples.
- Per-device VLA and VLM batch sizes are independent overrides.
- `trainer.loss_scale.vlm` controls how much VLM loss contributes. Some benchmark configs set it to `0.0` to effectively disable VLM contribution despite a VLM data section.
- The co-train loop has a DeepSpeed-specific branch because ZeRO gradient partitioning is incompatible with Accelerate's `no_sync()` accumulation context. If a custom trainer reintroduces `no_sync` errors, follow the co-train engine-boundary pattern.

## VLM-only training checklist

For `train_starvlm.py`:

- Ensure `datasets.vlm_data.dataset_use` is present; it is used in logging.
- Ensure the selected framework has a usable `qwen_vl_interface` or equivalent VLM interface.
- Expect checkpoints in the same `run_root_dir/run_id` layout.
- Use W&B disabled mode when online logging is unwanted; the source calls `wandb.init`, but W&B disabled mode prevents online logging.

## CPU-safe validation before an expensive run

The construction evidence included CPU-safe checks showing that trainer utilities and data-preparation helper functions are safe without an initialized distributed process group. In a StarVLA checkout, useful pre-launch checks are:

```bash
python skills/disco/star-vla/sub-skills/training-config/scripts/plan_training_command.py --help
python skills/disco/star-vla/sub-skills/training-config/scripts/plan_training_command.py --config-yaml path/to/config.yaml --override trainer.max_train_steps=1
pytest tests/test_single_process_dist_safety.py -q
pytest tests/test_config_overrides.py -q
```

The first two are safe skill-bundled checks. The pytest commands are optional source-checkout validation; they do not validate GPU memory, model downloads, actual dataloading, or DeepSpeed correctness.

## Source launchers are reference-only

Representative `examples/*/train_files/run_*.sh` source launchers were inspected but are not bundled because they are environment-specific. They commonly hard-code or derive:

- NCCL interface and timeout settings.
- GPU process counts.
- data root and pretrained model paths.
- W&B project/entity names.
- run IDs and result/log directories.
- checkpoint-output safeguards for a particular example.

Use them as evidence for command anatomy, not as reusable runtime scripts. Produce a new launch plan with explicit user-provided values instead.

## After training

- Benchmark evaluation routes to [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
- Serving checkpoints routes to [policy-deployment](../../policy-deployment/SKILL.md).
- Missing or mismatched `dataset_statistics.json` usually crosses into both [data-integration](../../data-integration/SKILL.md) and [policy-deployment](../../policy-deployment/SKILL.md).
