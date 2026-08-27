# Training and fine-tuning troubleshooting

Use this reference when `llmfoundry train <config.yaml> [overrides...]` fails or when adapting a YAML to a new dataset, model, backend, or checkpoint path.

## Fast triage

1. Run the static probe:

```bash
python scripts/llmfoundry_config_probe.py <config.yaml> [overrides...]
```

2. Confirm the actual launch is bounded:

```bash
llmfoundry train <config.yaml> max_duration=2ba eval_interval=0 save_folder=null
```

3. Confirm environment class: CPU-only, single GPU, multi-GPU, multi-node, or platform job.
4. Confirm model/tokenizer/data/checkpoint access before increasing duration.
5. Route data conversion, eval task schema, checkpoint export, or registry-extension questions to the owning sub-skill.

## Missing required config or unused top-level keys

Symptoms:

- `MissingMandatoryValue` for fields such as `model`, `tokenizer`, `optimizer`, `scheduler`, `train_loader`, `device_eval_batch_size`, `max_duration`, or `max_seq_len`.
- Error like `Unused parameters [...] found in cfg`.

Fix:

- Add required sections listed in [configuration-reference.md](configuration-reference.md).
- Use `global_train_batch_size` plus `device_train_microbatch_size` in normal YAMLs so LLM Foundry transforms compute `device_train_batch_size`.
- Put arbitrary constants under `variables`, not at top level, unless a known config transform consumes them.
- Check for misspellings: `eval_loader` not `eval_loaders` in user-facing multi-eval input, `device_train_microbatch_size` not `microbatch_size`, `save_folder` not `checkpoint_dir`.

## Data split and path errors

Symptoms:

- Train loader construction fails before model initialization.
- MDS split folder not found.
- Remote streaming path works on one node but not another.
- Local JSON SFT loader cannot find `train` split or `data_dir`.

Fix:

- For MDS text pretraining, ensure `train_loader.dataset.local` points to a folder containing the named split, or `remote` points to the dataset source and `local` is a writable cache.
- Keep `train_loader.dataset.split` and `eval_loader.dataset.split` aligned with prepared splits such as `train`, `val`, `train_small`, or `val_small`.
- For local JSON/JSONL fine-tuning, use `train_loader.dataset.hf_name: json` and set `train_loader.dataset.hf_kwargs.data_dir=<data-local>` or equivalent HF `datasets` kwargs.
- If prompt/response keys or conversion policy are wrong, route to data-preparation before training.
- For multi-node streaming, every worker needs credentials and a writable local cache path.

## Bad batch size or gradient accumulation

Symptoms:

- Error that global batch size is not divisible by world size.
- OOM on first train batch.
- Microbatch is automatically reduced.
- Evaluation OOMs even though training fits.

Fix:

- Choose `global_train_batch_size` divisible by the effective data-parallel world size.
- Reduce `device_train_microbatch_size`; try `1` for a debugging run.
- Reduce `device_eval_batch_size`, especially for long-context eval or ICL.
- Use `device_train_microbatch_size: auto` only after a fixed small microbatch proves the rest of the config works.
- Keep optimization math (`global_train_batch_size`) separate from system execution (`device_train_microbatch_size`).

## Missing tokenizer or model downloads

Symptoms:

- Hugging Face 401/403/404 errors.
- Model or tokenizer download timeouts.
- Tokenizer has no EOS token.
- Gated model fails only on worker ranks.

Fix:

- Verify `model.pretrained_model_name_or_path` and `tokenizer.name`.
- For gated models, set `model.use_auth_token: true` only when `HF_TOKEN` or equivalent auth is available on every worker.
- Pre-populate model/tokenizer cache or run a short single-rank cache warmup if downloads are large.
- Keep `tokenizer.kwargs.model_max_length` aligned with `max_seq_len`.
- If a tokenizer lacks EOS, choose a compatible tokenizer or explicitly configure one through the tokenizer's supported kwargs.

## Setuptools or `pkg_resources` warnings

Symptoms:

- Warnings about `pkg_resources` deprecation or setuptools metadata during import.
- Warning noise but command continues.

Fix:

- Treat deprecation warnings as non-fatal when imports and the probe succeed.
- If import fails, check package installation and Python environment rather than editing YAML.
- Avoid installing broad optional extras just to silence warnings; only install backend extras required by the selected workflow.

## CUDA optional extras and attention backends

Symptoms:

- Import errors for `flash_attn`, TransformerEngine, CUDA fused ops, or MegaBlocks.
- Runtime error when `attn_impl: flash` is selected.
- `amp_fp8` warns that TE layers are not enabled.
- GPU kernel works on H100 but not on CPU or a consumer GPU.

Fix:

- For CPU smoke runs, use `attn_impl: torch`, small model dimensions, and `precision: fp32`.
- Use `attn_impl: flash` or HF `attn_implementation: flash_attention_2` only in an environment with matching CUDA, PyTorch, and flash-attn versions.
- Use `precision: amp_fp8` only with TransformerEngine layers, for example `model.fc_type: te` or TE FFN config, and appropriate H100-class hardware.
- MegaBlocks/MoE configs require optional dependencies and may impose FSDP `use_orig_params` constraints.
- If optional kernels fail, first fall back to torch attention for a tiny run to separate config/data issues from backend issues.

## Out-of-memory (OOM)

Symptoms:

- CUDA OOM during model initialization, first forward/backward pass, eval, or checkpoint save.
- Only one GPU appears active.

Fix:

- Confirm the job was launched with the intended process count; one process will not shard a large FSDP model.
- Enable or keep `fsdp_config.sharding_strategy: FULL_SHARD` for large models.
- Use `precision: amp_bf16` on supported GPUs.
- Reduce `device_train_microbatch_size`; if needed set it to `1`.
- Reduce `device_eval_batch_size` and disable eval temporarily with `eval_interval=0` for debugging.
- Enable `fsdp_config.activation_checkpointing: true` and `activation_checkpointing_reentrant: false`.
- Consider `activation_cpu_offload: true` only as a last resort because it can slow training substantially.
- For checkpoint OOMs, consider `fsdp_config.state_dict_type: sharded`.

## FSDP and init-device errors

Symptoms:

- Warning that FSDP is not applicable for single-GPU training.
- Warning that `init_device: meta` is only valid with FSDP and is reverted to CPU.
- Error that `init_device: mixed` requires FSDP.
- TE activation checkpointing warning.

Fix:

- For single-process CPU/GPU smoke runs, set `model.init_device: cpu`.
- For large FSDP runs, use a launcher or platform that starts the required distributed processes.
- Keep `fsdp_config.activation_checkpointing_reentrant: false` with TransformerEngine layers.
- For sharded checkpointing, set `fsdp_config.state_dict_type: sharded` and check latest-checkpoint names.

## Tensor parallel errors

Symptoms:

- `tp_config` requires `strategy` and `tensor_parallel_degree`.
- Tensor parallelism rejected for MoE models.
- Model layers are not partitioned as expected.

Fix:

- Include both required TP fields:

```yaml
tp_config:
  strategy: <strategy-name>
  tensor_parallel_degree: <degree>
```

- Remove TP for MoE/MegaBlocks configs unless the package version explicitly supports it.
- Validate the non-TP FSDP run first.
- Route strategy registry details to package-apis-configuration.

## Checkpoint upload, download, or credentials errors

Symptoms:

- Training succeeds but remote checkpoint upload fails.
- Resume cannot find latest checkpoint.
- Object-store path works locally but not on worker nodes.
- HF checkpoint callback errors because more than one callback is configured.

Fix:

- Confirm `save_folder`, `load_path`, and path schemes.
- Ensure credentials are present on every worker and grant the required read/write permissions.
- For smoke runs, set `save_folder=null` or a temporary local folder to avoid remote side effects.
- Use `save_num_checkpoints_to_keep: 1` for bounded local storage.
- Use `load_weights_only: true` for fine-tuning from model weights; use full state loading only for same-run resume.
- If `only_hf_checkpoint: true`, configure exactly one `hf_checkpointer` callback.
- If `run_name` and `save_folder` are set and overwrite/weights-only are false, be aware that autoresume may be enabled by default.

## Multi-node launch issues

Symptoms:

- Hang at distributed initialization or barrier.
- NCCL timeout.
- Some ranks cannot read data or checkpoints.
- Different ranks use different code or config.

Fix:

- Ensure all ranks receive the same YAML and override list.
- Set world size, rank, node rank, master address, and master port consistently through the launcher or platform.
- Increase `dist_timeout` for very large model initialization or slow clusters.
- Confirm network connectivity between nodes.
- Confirm object-store credentials and local cache paths on every node.
- Keep a one-node smoke run as the baseline before scaling.

## MCLI/platform adaptation pitfalls

Platform examples are reference-only. Do not copy:

- cluster names;
- account/project names;
- private Git settings;
- object-store bucket paths;
- credentials or tokens;
- GPU counts that do not match your model size and budget.

Adapt only the generic structure: image, dependency install, command, compute, injected parameters, environment variables, and checkpoint/data paths. Run the same config locally or on a small platform job before a full-scale submission.
