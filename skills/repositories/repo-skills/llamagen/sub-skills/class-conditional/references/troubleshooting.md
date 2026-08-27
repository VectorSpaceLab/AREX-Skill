# Troubleshooting

## DDP and FSDP launch failures
### Symptom
- `AssertionError: Batch size must be divisible by world size`
- NCCL init or `torchrun` rendezvous errors
- ranks disagree about `WORLD_SIZE`, `RANK`, or `LOCAL_RANK`

### What to check
- Match `nnodes`, `nproc_per_node`, `node_rank`, `master_addr`, and `master_port`.
- Make sure every process sees the same distributed env.
- Confirm `torch.cuda.device_count()` is at least the per-node process count.
- For DDP, `global_batch_size` must divide world size.

## FSDP resume issues
### Symptom
- `Resuming from a checkpoint with unmatched world size`
- Missing `consolidated.pth`, `optimizer.*.pth`, or `resume_step.txt`

### What to check
- Resume from the checkpoint directory, not from a single file.
- Reuse the same world size that wrote the optimizer shards.
- If the world size changed, start a new run or re-export a compatible checkpoint.

## Checkpoint-shape mismatches
### Symptom
- Loader says to add `--from-fsdp`
- `model`, `module`, or `state_dict` keys are missing
- Weights load but shapes still mismatch

### What to check
- DDP checkpoints usually carry `model`.
- Deepspeed-style checkpoints may carry `module`.
- Some checkpoints carry `state_dict`.
- Raw FSDP consolidated weights need `--from-fsdp`.
- Confirm the selected `--gpt-model` family matches the checkpoint family.

## vLLM serving issues
### Symptom
- Invalid model path or model-id resolution errors
- KV-cache / memory sizing failures
- vLLM initialization errors around the fake JSON config

### What to check
- Use the bundled fake JSON model name that matches the family.
- Check that `--gpt-ckpt` points to a local checkpoint file or raw FSDP weight in the expected form.
- Reduce GPU memory usage if the worker complains about cache blocks or KV cache capacity.
- Confirm `--from-fsdp` for raw consolidated weights.

## Evaluator input mistakes
### Symptom
- Missing `.npz` sample batch
- Missing `arr_0`
- Reference batch path points to a PNG folder instead of an `.npz`

### What to check
- Package the sample folder first.
- Use the bundled helper to create `sample_dir.npz`.
- Confirm the reference batch is the actual ImageNet `.npz` file.

## Gradio demo caveat
### Symptom
- Import-time checkpoint loading or remote model-id resolution fails

### What to check
- Do not use `app.py` as a bundled runtime script.
- Treat it as a reference-only example for manual exploration.
- Use the shell wrappers in this sub-skill for automation.
