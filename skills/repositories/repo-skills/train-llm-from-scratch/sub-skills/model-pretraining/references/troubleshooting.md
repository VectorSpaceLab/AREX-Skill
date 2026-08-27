# Model Pretraining Troubleshooting

Use this guide when model construction, pretraining, checkpoint loading, DDP launch, or memory planning fails. For data creation or schema repair, route to the data-preparation sub-skill.

## Quick Triage

1. Identify workflow: modern JSON/DDP pretraining or legacy single-GPU training.
2. Confirm model dimensions: `vocab_size`, `context_length`, `n_embed`, `n_head`, `n_blocks`/`N_BLOCKS`.
3. Confirm the token files exist and contain a flat HDF5 `tokens` dataset.
4. Run the bundled tiny Transformer smoke before blaming CUDA or DDP.
5. If loading a checkpoint, inspect and honor the checkpoint's stored config before applying overrides.

## Failure Modes

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| CUDA out of memory at startup | Model + AdamW state too large for VRAM | Parameter count; `n_embed`, `n_blocks`, `vocab_size`; memory report if using legacy | Reduce `n_embed`/`n_blocks`, use fewer heads only if divisibility holds, or use a smaller model. |
| CUDA out of memory during forward/backward | Activation memory dominated by `B * H * T^2 * blocks` attention scores | Compare `batch_size`, `context_length`, `n_head`, `n_blocks`; check if OOM appears only at longer sequences | Reduce `batch_size` first, then `context_length`; increase `grad_accum` to recover effective batch; use legacy `--grad-checkpointing` when on that path. |
| OOM appears after several steps | CUDA fragmentation or changing shapes | Peak allocated/reserved memory; whether sequence lengths vary | Keep fixed context, reduce batch, try `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in the shell, or restart the process after a failed OOM. |
| Loss scale changes when using gradient accumulation | Loss not divided by accumulation steps, or user compares microbatch loss to full-step loss | Modern loop divides loss by `grad_accum`; legacy memory path also scales before backward | Effective batch is `batch_size * grad_accum * world_size`; keep LR decisions tied to effective batch, not only microbatch size. |
| Training is slow but fits | Too much gradient accumulation, CPU data bottleneck, or DDP sync overhead | Tokens/sec after warmup; CPU vs GPU utilization | Increase microbatch if memory allows, lower eval frequency, ensure HDF5 is on fast local storage, and avoid DDP for one GPU. |
| bf16 autocast has no effect | Device is CPU or GPU lacks efficient bf16 support | `device`, CUDA availability, GPU generation | Set `amp_dtype` to `null` for CPU/smoke. On older CUDA GPUs use legacy fp16 AMP if needed; modern bf16 path intentionally does not use a GradScaler. |
| NaN loss under mixed precision | Too-high LR, unstable data, fp16 underflow/overflow, or invalid tokens | Check LR, token id range, and whether bf16/fp16 is active | Lower LR, verify tokens are `< vocab_size`, prefer bf16 over fp16 on supported GPUs, and keep `grad_clip` enabled. |
| `FileNotFoundError` for token files | Config points at a path that does not exist in the user's environment | Print resolved config; inspect `train_path` and `dev_path` | Override paths with user-controlled HDF5 files or route to data preparation. |
| `KeyError: tokens` or HDF5 shape errors | HDF5 file does not match the flat pretraining schema | Inspect HDF5 keys and `tokens` shape | Recreate/repair the pretraining HDF5 via data-preparation guidance. |
| DDP launch hangs or errors on rank setup | Launched with plain Python for multiple GPUs, wrong process count, unavailable NCCL, or port conflict | Environment has `RANK`, `LOCAL_RANK`, `WORLD_SIZE`; command uses `torchrun --standalone --nproc_per_node=N` | Use the command builder with `--nproc N`; keep `N <=` visible GPUs; use single-process Python for `N=1`; retry with a fresh shell if a previous distributed process crashed. |
| Multiple ranks write duplicate logs/checkpoints | Rank guard missing or custom command bypassed the normal trainer | Check only rank 0 should print main logs and save | Use the standard modern pretraining entrypoint; do not wrap or fork custom save logic unless rank-gated. |
| `RuntimeError: view size is not compatible...` in loss | A branch or custom edit used `.view()` on non-contiguous targets | Targets are produced by slicing `tokens[:, 1:]` | Use `.reshape()` for logits and targets before cross-entropy. The bundled smoke script exercises this path. |
| State-dict size mismatch on resume/load | Checkpoint config does not match current model dims | Compare checkpoint `cfg`/`config` to requested dims; common mismatches are `context_length`, `vocab_size`, `n_embed`, and `n_blocks` | Rebuild the model from checkpoint config or intentionally start a fresh run. Do not resume optimizer state across changed dimensions. |
| Position embedding mismatch | New `context_length` differs from checkpoint | Error mentions `position_embed.weight` | Use original context length, or start a new checkpoint. Cropping/expanding learned positions is a custom migration, not a normal resume. |
| Token/lm head mismatch | `vocab_size` differs from checkpoint/tokenizer | Error mentions `token_embed.weight` or `lm_head.weight` | Use the same tokenizer vocabulary size as the checkpoint. This repo does not tie input and output embeddings, so both matrices must match. |
| Legacy `--resume latest` finds nothing | Wrong checkpoint directory or no periodic checkpoint saved | Check `--checkpoint-dir`, configured final output path, and `--checkpoint-every` | Resume an explicit checkpoint path or rerun with periodic checkpointing enabled. |
| Modern `--resume latest` does not work | Modern resume expects an explicit path | Check command | Pass `--resume path/to/checkpoint.pt`; use legacy only if directory-based latest resolution is required. |
| Training starts near impossible low loss | Targets may equal inputs without a next-token shift, or data leakage | Inspect batch construction | Pretraining batches should use `xb = window[:-1]`, `yb = window[1:]`. Loss near `ln(vocab_size)` at step 0 is normal. |
| `n_embed`/`n_head` shape error | Head width is not integral | Compute `n_embed % n_head` | Choose `n_head` that divides `n_embed`, or change width. |

## Memory Planning Rules

Reduce memory pressure in this order:

1. Lower `batch_size`.
2. Increase `grad_accum` to keep effective batch size if optimization stability needs it.
3. Lower `context_length`; attention memory scales quadratically with this value.
4. Lower `n_blocks`.
5. Lower `n_embed`.
6. Adjust `n_head` only after preserving divisibility and a sensible head width.

Modern DDP keeps a full model replica on each GPU; it increases throughput and effective batch but does not shard parameters. Do not expect DDP alone to make an overlarge model fit.

## Checkpoint Compatibility Checklist

Before resuming or using a checkpoint downstream:

- Load the stored `cfg`/`config` metadata if present.
- Verify `vocab_size`, `context_length`, `n_embed`, `n_head`, and block count.
- Strip DDP `module.` prefixes only when loading a DDP-saved state into an unwrapped model.
- Ignore auxiliary heads only in downstream wrapper contexts that explicitly filter backbone keys.
- Do not reuse optimizer state after changing model dimensions.

## Smoke Before Long Runs

Run the tiny model smoke when debugging architecture, CUDA availability, or the `.reshape()` loss path:

```bash
python scripts/smoke_transformer.py
python scripts/smoke_transformer.py --device cuda
```

Then build a parser-only modern smoke command:

```bash
python scripts/build_pretrain_command.py --mode modern --smoke --extra=--print-config
```

Only after those checks pass should you execute a data-dependent pretraining command.
