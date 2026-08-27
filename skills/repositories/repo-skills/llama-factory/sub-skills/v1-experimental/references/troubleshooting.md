# V1 Troubleshooting

V1 is experimental. Start with routing and static config checks before debugging model, dataset, or distributed behavior.

## Forgot `USE_V1=1`

Symptoms:

- A v1 example containing `train_dataset`, `micro_batch_size`, `peft_config`, or `dist_config` is parsed by the default v0 stack.
- Errors mention v0 argument dataclasses, v0 stages, v0 dataset names, or unused arguments that look valid in v1.
- A v1-style YAML passed to the default `train` command behaves like a v0 training invocation.

Fix:

```bash
USE_V1=1 llamafactory-cli sft config.yaml
```

or:

```bash
USE_V1=1 lmf sft config.yaml
```

For distributed smoke tests, add `FORCE_TORCHRUN=1` only when the user actually wants a torchrun launch.

## Mixing V0 And V1 Config Fields

Symptoms:

- `HfArgumentParser` reports unused or unknown args.
- A config contains `stage`, `do_train`, `dataset`, `dataset_dir`, `finetuning_type`, `per_device_train_batch_size`, `gradient_accumulation_steps`, or `deepspeed` alongside v1 fields.
- A v0-style config was copied into a v1 command or a v1-style config was copied into a v0 command.

Fix:

1. Run the bundled static checker:

```bash
python scripts/check_v1_config_keys.py config.yaml
```

2. Replace v0 train fields with v1 fields:
   - `dataset` -> `train_dataset`.
   - `finetuning_type: lora` -> `peft_config.name: lora`.
   - `per_device_train_batch_size` -> `micro_batch_size`.
   - gradient accumulation intent -> `global_batch_size` relative to `micro_batch_size`.
   - `deepspeed` -> `dist_config.name: deepspeed` plus `config_file`.
3. Remove `stage` and select the v1 CLI subcommand instead.

Use `ALLOW_EXTRA_KEYS=1` only as a deliberate development escape hatch. It can hide stale config fields and should not be the default recommendation for user-facing fixes.

## Plugin Config Missing `name`

Symptoms:

- Error like `Plugin configuration must have a 'name' field`.
- A config has `peft_config`, `quant_config`, `kernel_config`, `init_config`, `dist_config`, `optim_config`, or `lr_scheduler_config` as a dict without `name`.

Fix:

```yaml
peft_config:
  name: lora
  r: 16
```

Use `null` for disabled plugin configs:

```yaml
quant_config: null
```

## Unsupported Trainer Or Command

Symptoms:

- `NotImplementedError` for v1 `dpo`, `env`, or `version`.
- User expects v0 PPO/KTO/DPO behavior from the v1 launcher.

Fix:

- For production DPO/PPO/KTO/default training, route to v0 sibling sub-skills unless the user is explicitly developing v1 internals.
- For v1 SFT use `USE_V1=1 llamafactory-cli sft config.yaml` or `train`.
- For v1 RM use `USE_V1=1 llamafactory-cli rm config.yaml` and pair-format data.

## Dataset Shape Problems

Symptoms:

- RM raises that samples lack `chosen_messages` and `rejected_messages`.
- Rendering fails because messages do not contain v1 `role`, `content`, and `loss_weight` shape.
- Streaming dataset index access raises an error.

Fix:

- Use v1 dataset-info YAML and set `converter: alpaca`, `sharegpt`, or `pair` when raw records are not already in v1 message format.
- For RM, verify the first sample contains `chosen_messages` and `rejected_messages`; raw chosen/rejected text usually needs `converter: pair`.
- Do not index streaming datasets; current `DataEngine.__getitem__` rejects streaming index access.
- Keep all datasets either streaming or non-streaming; mixed mode is rejected.

## Batching And Flash Attention

Symptoms:

- `dynamic_batching` rejects missing `max_steps`.
- `dynamic_batching` rejects `save_epochs`.
- `padding_free` rejects the current attention implementation.
- Sequence/context parallelism complains about flash attention or model type.

Fix:

```yaml
batching_strategy: dynamic_batching
max_steps: 10
save_steps: 5
```

For padding-free or sequence-parallel cases:

```yaml
flash_attn: flash_attention_2
```

Then verify the target model and hardware actually support flash attention. Some model-specific attention implementations remain unsupported for sequence parallelism.

## Quantization Problems

Symptoms:

- Missing bitsandbytes dependency.
- 8-bit training with auto device map or FSDP/QLoRA fails.
- Quantization with `init_on_meta` fails.

Fix:

- For QLoRA-style v1 training, prefer `quant_config.name: bnb` with `quantization_bit: 4`.
- Do not use quantization with meta-device initialization.
- Verify bitsandbytes version and accelerator support before running.
- Treat 8-bit quantization as inference-oriented unless the exact v1 path has been verified.

## Kernel Plugin Problems

Symptoms:

- Kernel ID not found.
- Liger or device-specific fused kernel import fails.
- Kernel patching behaves differently across CUDA, NPU, and CPU.

Fix:

- Use `kernel_config: null` or remove the kernel block for a conservative smoke test.
- Use `kernel_config.name: auto` only when optional dependencies and target accelerator are available.
- Use `liger_kernel` only when the package, model, and requested fused ops are supported.

## Distributed Launch Problems

Symptoms:

- Torchrun relaunch fails before parsing the config.
- DeepSpeed complains that `config_file` is required.
- Context parallelism with DeepSpeed fails.
- RM fails with `cp_size > 1`.

Fix:

- Start with one visible device and no `FORCE_TORCHRUN` for parser/config validation.
- For FSDP2:

```yaml
dist_config:
  name: fsdp2
  dcp_path: null
```

- For DeepSpeed:

```yaml
dist_config:
  name: deepspeed
  config_file: path/to/deepspeed.json
```

- Use FSDP2, not DeepSpeed, for context parallel experiments.
- Avoid RM context parallelism; current RM trainer rejects it.

## Optional Dependency And Test Gating

Symptoms:

- `tests_v1` skips or fails based on Transformers version.
- Tests are skipped unless `RUN_SLOW=1`, matching accelerator type, or multiple devices are visible.
- Tiny-model tests download models or datasets.

Fix:

- Treat native tests as evidence candidates, not always-safe verification.
- Run parser-only tests first when dependencies are partial.
- Prefer static config inspection when full dependency install, model downloads, GPU/NPU, or distributed backends are unavailable.
