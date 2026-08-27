# Training troubleshooting

Start with the symptom, then check the likely source area. Do not run training, downloads, or credentialed actions without user approval.

## Fast triage checklist

1. Capture the exact command and whether it used `simpletuner train`, `simpletuner-train`, `ENV`, `CONFIG_BACKEND`, `CONFIG_PATH`, or a packaged example.
2. Identify the backend and platform: CUDA, CUDA 13, ROCm, Apple/MPS, or CPU-only.
3. Record model family/flavour/type, output directory, config backend, `num_processes`, `gradient_accumulation_steps`, `train_batch_size`, DeepSpeed/FSDP/context-parallel settings, and whether this is a resume.
4. Turn on debug logs only when needed: `SIMPLETUNER_LOG_LEVEL=DEBUG` and `SIMPLETUNER_TRAINING_LOOP_LOG_LEVEL=DEBUG` add detail to logs.
5. If the run is distributed, confirm all ranks/nodes see the same config, model access, data/cache roots, and output/checkpoint storage.

## Symptom table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No config file found in current directory or config/ subdirectory` | `simpletuner train` was run without a discoverable config and without `--env`/`--example`. | Run `simpletuner configure`, copy an example into `config/<env>/`, or pass `simpletuner train --env <env>`. For a specific JSON file, use `CONFIG_BACKEND=json CONFIG_PATH=<path> simpletuner-train`. |
| `Configuration for environment '<env>' not found` | Non-default `--env` did not resolve to `config/<env>/config.json`, `config.toml`, or `config.env`, or backend/path override was inconsistent. | Check the environment name, backend, and file layout. Use `json` for arbitrary `CONFIG_PATH`; TOML/env backends are environment-layout based in this snapshot. |
| Invalid or unsupported config backend | `CONFIG_BACKEND` is not one of `json`, `toml`, `env`, `cmd`, or casing/spelling is wrong. | Normalize to lower-case `json`, `toml`, `env`, or `cmd`. Use the bundled command builder to print the intended shell command. |
| Dataset will produce zero usable batches / insufficient samples | Each aspect bucket must satisfy `train_batch_size × num_processes × gradient_accumulation_steps` after repeats. | Reduce batch size, GPU/process count, or accumulation; add samples; increase dataset `repeats`; or enable `allow_dataset_oversubscription` when automatic repeat padding is acceptable. Route bucket/schema details to `sub-skills/data-and-config/`. |
| `Cannot enable FSDP when a DeepSpeed configuration is also provided` or `FSDP and DeepSpeed cannot be enabled simultaneously` | Both distributed plugins are configured. | Choose exactly one. Use FSDP2 for DTensor sharding/context parallel plans; use DeepSpeed ZeRO for CUDA optimizer/state offload full-model plans. |
| DeepSpeed unavailable on platform | DeepSpeed is selected on MPS/Apple or ROCm. | Remove DeepSpeed and choose DDP/FSDP/offload alternatives appropriate to the platform. |
| Context parallelism requires FSDP2 / context size errors | `context_parallel_size > 1` with missing FSDP2 sharding plugin, invalid strategy, unknown process count, or size not dividing world size. | Set `fsdp_enable=true`, `fsdp_version=2`, and a valid `num_processes`, or return `context_parallel_size=1`. Use `allgather` unless the model/example requires `alltoall`. |
| MiniMax H3 sparse/context errors | H3 sparse attention needs CUDA FlexAttention-style support and rejects some combinations such as ring CP, TREAD, CachedKV reference mode, or hidden-state capture. | Use a dense attention backend or the documented H3 sparse profile with `alltoall` and compatible CP/FSDP2 settings. Treat sparse H3 as an ablation, not a guaranteed speedup. |
| FSDP2 rejects Quanto precision | FSDP2 DTensor-sharded parameters are incompatible with Quanto kernels. | Disable Quanto precision for FSDP2, use another precision route, or use non-FSDP LoRA if it fits. |
| FSDP2 CPU offload rejects optimizer path | CPU parameter offload conflicts with optimi post-accumulate gradient release or TorchAO CPU-offload optimizer mode. | Use a standard optimizer/offload combination, disable `fsdp_cpu_offload`, or disable the incompatible optimizer release/offload path. |
| Resume fails after topology/config changes | Checkpoint state encodes trainer topology, model identity, sampler/bucket state, optimizer state, and sometimes distributed backend. | Resume only with the same family/type/flavour, DDP/DeepSpeed/FSDP mode, world size, context-parallel plan, batch sizing, gradient accumulation, dataset repeats, and dataloader semantics. Start a new run or export model-only weights when changing topology. |
| Batch-size mismatch on resume | Dataset sampler checkpoint recorded a different per-dataset batch size. | Restore the original batch size. Only use `SIMPLETUNER_ALLOW_MODIFYING_BSZ=1` or `--i_know_what_i_am_doing` when the user explicitly accepts sampler-state risk. |
| CUDA/ROCm/MPS package mismatch | Installed extra does not match hardware, torch build, driver, or custom attention kernel. | Reinstall with the correct extra (`cuda`, `cuda13`, `rocm`, `apple`, `cpu`) and matching indexes. Rebuild/install FlashAttention/Flex/UMFA/SLA only on supported hardware. |
| Out of memory during startup/cache | Text encoder, VAE cache, quantization, or model load exceeds memory before training starts. | Use `quantize_via=cpu`, text/base precision from the quickstart, `offload_during_startup`, lower VAE/text batch sizes, VAE tiling/chunking where supported, and lower resolution/frame counts. |
| Out of memory during train/validation | Batch/resolution/frames/model precision/attention/backend too heavy, or validation uses a larger shape than training. | Lower `train_batch_size`, resolution, frames, validation resolution/steps, LoRA rank, and validation batch; enable `gradient_checkpointing`, group offload, or a compatible distributed memory strategy. |
| Model download or Hugging Face access failure | Gated model not accepted, user not logged in, network restrictions, or mirror needed. | Ask user to accept model terms, run `huggingface-cli login`, configure a mirror such as `HF_ENDPOINT` where appropriate, or supply local cached model paths. Do not perform credentialed downloads without approval. |
| External validation script fails before first checkpoint | `validation_method=external-script` with `{local_checkpoint_path}` but no checkpoint exists. | Delay external validation until after a checkpoint, use built-in validation, or remove the placeholder. Ensure the script path exists and is executable. |
| Checkpoint path/upload/resume errors | Missing `output_dir`, invalid local checkpoint, missing remote publishing config, absent checkpoint manifest, or insufficient disk space. | Verify `output_dir`, checkpoint name/path, `checkpoint_manifest.json` for remote resume, S3 publishing config when using remote checkpoints, and disk-low settings. Use `delete_invalid_checkpoints` only for local checkpoints under `output_dir`. |
| SLA checkpoint resumes without learned SLA state | `sla_attention.pt` was removed or not saved with the checkpoint. | Keep `sla_attention.pt` beside the checkpoint. Recreate state only by running an approved short SLA training/resume job. |
| CLIP/eval loss results are confusing | CLIP measures prompt-image feature alignment, not image quality; eval loss uses eval datasets and can add overhead. | Use many validation prompts for CLIP if making claims. Use `eval_loss_disable` when eval datasets are configured but loss should not run. |

## Difficult case: Flux LoRA command without resume topology drift

For a Flux LoRA command from a copied environment:

1. Keep the existing `resume_from_checkpoint`, `model_family=flux`, `model_type=lora`, `model_flavour`, `train_batch_size`, `gradient_accumulation_steps`, dataset repeats, and process count unchanged.
2. Add only safe command-line overrides such as `max_train_steps` for a bounded smoke test or `report_to=none` to avoid tracker credentials.
3. Use the wrapper form for an environment:

```bash
simpletuner train --env flux-lora max_train_steps=100 report_to=none
```

If using a JSON file path directly:

```bash
CONFIG_BACKEND=json CONFIG_PATH=config/flux-lora/config.json simpletuner-train --max_train_steps=100 --report_to=none
```

## Difficult case: multi-GPU video FSDP/DeepSpeed/CP diagnosis

For a multi-GPU video job that requests FSDP, DeepSpeed, and context parallelism:

1. Reject the simultaneous FSDP+DeepSpeed configuration first.
2. If context parallelism is required for sequence length, keep FSDP2 and remove DeepSpeed.
3. Ensure `context_parallel_size` divides `num_processes`; start with `allgather` unless the selected example uses `alltoall`.
4. Check model-specific CP support and attention backend. Large Wan/LTX examples often pair context parallelism with FlashAttention hub backends on H100-class systems; MiniMax H3 sparse attention has stricter CUDA/Flex/all-to-all constraints.
5. Only after the topology is valid should you inspect dataset bucket sizing and memory knobs.
