# Training troubleshooting

Use this checklist before launching expensive Otter training.

## Preflight checklist

- Confirm the user explicitly authorized a training run, not just command construction.
- Confirm GPU count, GPU memory, CUDA/PyTorch compatibility, expected runtime, and disk budget.
- Confirm `PYTHONPATH=.` will be set from the repository root.
- Confirm the model path or identifier is accessible. With `--offline`, it must already be cached or local.
- Confirm data files exist. For SFT, the YAML and referenced MIMIC-IT/media paths must exist. For pretraining, shard patterns must expand to actual tar shards.
- Generate the command with `scripts/build_training_command.py` first and inspect it.

## Common failures and fixes

### YAML verification failed

`instruction_following.py` runs a prerun YAML verification on rank 0, and the MIMIC-IT loader checks that referenced paths exist. If startup fails here, route to [data-preparation](../../data-preparation/SKILL.md). Do not paper over schema/path errors in the training command.

### `save_checkpoints_to_wandb requires report_to_wandb`

Both SFT and pretraining parsers reject `--save_checkpoints_to_wandb` unless `--report_to_wandb` is also set. Either add W&B reporting with `--wandb_project` and `--wandb_entity`, or remove checkpoint upload.

### W&B or model download should not use network

Use `--offline` for SFT/pretraining when the user wants offline mode. This sets W&B offline mode and Transformer local-files-only behavior in the SFT script. Offline mode is not a downloader: every required model/tokenizer/config/data file must already be present.

### CUDA out of memory

Try these before switching to CPU offload:

- Reduce per-process batch size (`--batch_size`, `--batch_size_mmc4`, `--batch_size_laion`, or `--batch_size_cc3m`).
- Increase `--gradient_accumulation_steps` to preserve effective batch size.
- Reduce `--max_seq_len` for SFT or `--max-src-length` / `--max-tgt-length` for pretraining.
- For Fuyu/OtterHD, reduce resolution or disable dynamic-resolution experiments when not required.
- Enable `--gradient_checkpointing` where the selected model path supports it.
- Use ZeRO-3 instead of ZeRO-2 for large Otter weights.
- Use CPU offload configs only as a slower fallback when memory still does not fit.

### Fuyu/OtterHD fused-operator failures

OtterHD/Fuyu finetuning depends on Flash-Attention 2 and fused operators for the documented high-throughput path. Failures often come from CUDA, PyTorch, compiler, or ABI mismatch. Validate a small import/smoke under the target environment before a multi-node job. If fused ops are intentionally unavailable, avoid claiming the documented throughput and expect slower or blocked Fuyu runs.

### Accelerate or DeepSpeed config mismatch

- Ensure `--num_processes` matches intended total processes; override config defaults when needed.
- Keep CLI `--gradient_accumulation_steps` aligned with the Accelerate/DeepSpeed config's gradient accumulation intent.
- Override `--main_process_port` when running concurrent jobs.
- For multi-node jobs, pass `--machine_rank`, `--main_process_ip`, `--main_process_port`, `--num_machines`, and total `--num_processes` explicitly.
- Treat the file named `accelerate_config_fsdp.yaml` cautiously because its contents are single-process/non-distributed.

### Checkpoint or resume confusion

- SFT writes under `external_save_dir/run_name` when `--external_save_dir` is supplied.
- SFT final saving is implemented through `save_final_weights`; intermediate step saving uses `--save_steps_interval`; `--save_ckpt_each_epoch` saves after each epoch.
- SFT can load a checkpoint state with `--trained_ckpt`. Its parser exposes `--resume_from_checkpoint`, but it does not implement the same directory-scanning resume path used by pretraining.
- Pretraining scripts implement `--resume_from_checkpoint`, but expected checkpoint filename patterns differ between scripts and save paths. Inspect the run directory before relying on resume.
- `--delete_previous_checkpoint` is irreversible for earlier checkpoints.

### Fuyu argument mismatch

For OtterHD/Fuyu, keep these together:

```bash
--model_name=fuyu --instruction_format=fuyu --pretrained_model_name_or_path=adept/fuyu-8b
```

Common Fuyu additions are `--dynamic_resolution`, low `--workers` for stability, `--gradient_accumulation_steps=2`, and `--image_resolution=x,y` when overriding resolution. The tuple parser expects no spaces.

### Disk pressure during saves

`--save_hf_model` writes Hugging Face-format model assets and can be very large for 8B/9B models. ZeRO-3 gather-on-save can also add save-time memory/disk pressure. Ensure the save directory has enough space before the job starts.

## Route non-training problems

- Data format, MIMIC-IT conversion, parquet/image JSON, Syphus: [data-preparation](../../data-preparation/SKILL.md).
- Inference and prompt/media construction: [model-inference](../../model-inference/SKILL.md).
- Benchmark configs and evaluator behavior: [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
- Controller/worker/Gradio serving: [serving](../../serving/SKILL.md).
