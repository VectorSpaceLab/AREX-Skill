# Axolotl CLI Troubleshooting

Use this guide by symptom. Prefer lightweight checks before running commands that load models, datasets, vLLM, or training backends.

## `axolotl: command not found`

Likely causes:

- Axolotl is not installed in the active Python environment.
- The environment's console-script directory is not on `PATH`.
- The user installed from source but did not install the project as an editable/package install.

Checks:

```bash
python scripts/check_axolotl_install.py
python -m pip show axolotl
python -c "import axolotl; print(axolotl.__version__)"
```

Fix direction:

- Activate the intended environment or use that environment's Python.
- Install Axolotl in the environment using the project's documented install path.
- If package import works but `axolotl` is missing, use `python -m axolotl.cli.main --help` only as a temporary diagnostic; repair the console entry point for normal operation.

## Broken Import or Dependency Error

Likely causes:

- Partial install, incompatible dependency versions, or optional backend missing.
- Package metadata exists but importing the Click CLI pulls in a missing dependency.
- GPU/backend packages such as torch, vLLM, bitsandbytes, flash-attn, or torchao are absent or incompatible.

Checks:

```bash
python scripts/check_axolotl_install.py --json
axolotl --help
axolotl config-schema --field base_model
```

Fix direction:

- Treat package metadata/import success as a shallow check only.
- Read the first missing module or incompatible version from the traceback.
- Install optional extras only when the target operation needs them, such as vLLM for `vllm-serve` or torchao-related support for `quantize`.

## Config Path Rejected Before Command Runs

Click validates most `CONFIG` arguments as existing paths:

```bash
axolotl preprocess missing.yml
axolotl train missing.yml
axolotl merge-lora missing.yml
```

Fix direction:

- Confirm the working directory and config path.
- Use shell-safe quoting for paths with spaces.
- For cloud runs, remember that `--cloud` points to a cloud config and the positional argument points to the Axolotl training config.

## CLI Overrides Not Applied

Likely causes:

- Override placed after the standalone `--`, so it was passed to `torchrun` or `accelerate` instead of Axolotl.
- Used underscore-style legacy option names with the Click CLI.
- Used the wrong nested-field spelling.

Correct pattern:

```bash
axolotl train config.yml --launcher torchrun --learning-rate 2e-4 --micro-batch-size 4 -- --nproc_per_node=8
```

Fix direction:

- Move Axolotl overrides before `--`.
- Use dash-case: `--lora-model-dir`, not `--lora_model_dir`, for the Click CLI.
- Use `axolotl config-schema --field FIELD` to confirm field names and types.
- For legacy `python -m axolotl.cli.*` commands, expect underscore-style options in older examples.

## Launcher Extra Args Misplaced

Likely causes:

- `torchrun`/`accelerate` args placed before the separator.
- `--launcher python` used with launcher args.
- Shell quoting collapsed JSON or comma-separated values.

Correct patterns:

```bash
axolotl train config.yml --launcher torchrun -- --nproc_per_node=2 --nnodes=1
axolotl train config.yml --launcher accelerate -- --config_file=accelerate_config.yml --num_processes=4
```

Use `scripts/axolotl_command_builder.py` when the command is assembled programmatically; it prints argv JSON so the user can see exactly which process receives each argument.

## `--gradio` and `--chat` Conflict

Axolotl rejects combined interactive modes:

```bash
axolotl inference config.yml --chat --gradio
```

Fix direction:

- Use `--chat` for terminal multi-turn chat.
- Use `--gradio` for browser UI.
- Use default inference for piped prompts or legacy prompters.
- Chat mode requires a chat template and an interactive terminal.

## Merge or Inference Cannot Find Adapter/Model Files

Likely causes:

- `--lora-model-dir` points at the wrong checkpoint directory.
- The config's `output_dir`, `base_model`, or adapter path does not match the actual artifact.
- A full-model inference command was given a LoRA adapter path, or vice versa.

Fix direction:

- For LoRA inference, pass `--lora-model-dir` to the adapter output/checkpoint directory.
- For full fine-tuned model inference, pass `--base-model` to the completed model directory.
- For merging, use the same config used for training and point `--lora-model-dir` at the adapter checkpoint if not using the config default.
- Route adapter/model field corrections to `model-loading-and-adapters`.

## vLLM Server Problems

Symptoms and likely causes:

- Training hangs waiting for vLLM: server not started, wrong host/port, or health endpoint mismatch.
- vLLM OOM: `gpu_memory_utilization` too high or `max_model_len` too large.
- Accuracy stays at zero in GRPO/EBFT: stale vLLM server from a previous run or base model mismatch.
- `ResponseValidationError`: wrong serve module or incompatible vLLM response shape.

Fix direction:

```bash
curl http://localhost:8000/health/
curl http://localhost:8000/health
```

- Verify `trl.vllm_server_host` and `trl.vllm_server_port` match the server.
- Verify the server and trainer use the same `base_model`.
- Restart vLLM between runs and after crashes.
- Reduce vLLM memory settings or context length for OOM.
- Prefer Axolotl's `axolotl vllm-serve` over raw `trl vllm-serve` for Axolotl GRPO/EBFT configs.

## `agent-docs` Cannot Find Docs

Likely causes:

- Pip-only install without fetched docs.
- Installed package does not include bundled agent docs and the user has not fetched a local docs copy.
- Unknown topic name.

Fix direction:

```bash
axolotl agent-docs --list
axolotl fetch docs
axolotl agent-docs grpo
```

Known topics include `overview`, `sft`, `grpo`, `preference_tuning`, `reward_modelling`, `pretraining`, `model_architectures`, and `new_model_support`.

## `config-schema` Fails or Field Is Unknown

Likely causes:

- Schema generation hit a non-serializable default and used simplified fallback.
- Field name is misspelled or nested differently.
- Installed Axolotl version differs from the config or examples the user is adapting.

Fix direction:

```bash
axolotl config-schema
axolotl config-schema --format yaml
axolotl config-schema --field adapter
```

If `--field` is unknown, dump the full schema and inspect property names. Use the installed schema as the source of truth for the active environment.

## Cloud Config Path or Provider Issues

Likely causes:

- `--cloud` points to the training config instead of cloud YAML.
- Cloud YAML provider is unsupported.
- Remote mount paths differ from local paths.
- Required secrets/env vars are not available in the cloud provider.

Fix direction:

- Keep `axolotl train CONFIG --cloud CLOUD_CONFIG` ordering clear.
- Validate that the cloud YAML has a supported provider and expected GPU/count settings.
- Do not inline secrets in prompts, generated skill content, or logs.
- Treat provider-specific mount paths as remote runtime details, not local paths.

## Fetch Fails

Likely causes:

- Offline environment or network restrictions.
- Invalid fetch directory name.
- Destination path is not writable.

Fix direction:

- Valid directories are `examples`, `deepspeed_configs`, and `docs`.
- Use `--dest` for a writable target.
- If offline, use already available bundled or local examples/docs rather than running `fetch`.
