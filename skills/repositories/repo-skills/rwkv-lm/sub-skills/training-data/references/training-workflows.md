# RWKV training workflows

## Current default: RWKV-7 `train_temp`

The repository explicitly points new RWKV-7 training work to the `RWKV-v7/train_temp`
implementation. Its documented runtime is Python 3.10+, PyTorch 2.5+ or newer,
CUDA 12.5+ or matching wheel, latest DeepSpeed, `ninja`, `wandb` when logging is
wanted, and `pytorch-lightning==1.9.5`.

A full training run has two conceptual phases:

1. **Initialize weights** with `train_stage 1` on a data prefix. This creates
   `rwkv-init.pth` in `proj_dir`.
2. **Train/resume** with `train_stage 3` (or stage 2/3 in older scripts). The
   trainer scans `proj_dir` for `rwkv-*.pth` and loads the latest checkpoint.

Keep these phases in separate command records. Do not run a shell launcher that
removes checkpoints until you have manually inspected what it deletes.

## RWKV-7 MiniPile command template

Use this as a starting point after computing the exact `--my_exit_tokens` and
`--magic_prime` for your dataset prefix:

```bash
python train.py --wandb "" --proj_dir out/L12-D768-x070 \
  --data_file data/minipile --data_type binidx --vocab_size 65536 \
  --my_testing x070 --ctx_len 512 --train_stage 1 \
  --epoch_count 1 --epoch_begin 0 --epoch_save 1 \
  --weight_decay 0 --head_size 64 \
  --num_nodes 1 --micro_bsz 1 --n_layer 12 --n_embd 768 \
  --my_exit_tokens 1498226207 --magic_prime 2926181 \
  --lr_init 1e-5 --lr_final 1e-5 --warmup_steps 10 \
  --beta1 0.9 --beta2 0.99 --adam_eps 1e-8 \
  --accelerator cpu --devices 1 --precision bf16 \
  --strategy deepspeed_stage_2 --grad_cp 1
```

Then run the GPU training phase with the same model dimensions, data prefix,
context length, exit tokens, and magic prime:

```bash
python train.py --load_model "0" --wandb "Test" \
  --proj_dir out/L12-D768-x070 --my_testing x070 \
  --ctx_len 512 --train_stage 3 --epoch_count 999999 --epoch_begin 0 \
  --data_file data/minipile --my_exit_tokens 1498226207 \
  --magic_prime 2926181 --num_nodes 1 --micro_bsz 16 \
  --n_layer 12 --n_embd 768 --kernel "@rwkv3" \
  --lr_init 6e-4 --lr_final 6e-5 --warmup_steps 10 \
  --beta1 0.9 --beta2 0.99 --adam_eps 1e-18 \
  --data_type binidx --vocab_size 65536 --weight_decay 0.001 \
  --epoch_save 10 --head_size 64 --head_chunk 0 \
  --accelerator gpu --devices 1 --precision bf16 \
  --strategy deepspeed_stage_2 --grad_cp 1 --enable_progress_bar True
```

Adjust `micro_bsz`, `devices`, `num_nodes`, `head_chunk`, and `grad_cp` for
available VRAM. Do not change `ctx_len`, `magic_prime`, `vocab_size`, `n_layer`,
or `n_embd` between init and training unless you intentionally start a new run.

## Pile-scale training

The Pile launchers use a much larger binidx prefix and `ctx_len 4096`, often
with `vocab_size 50304`, `micro_bsz 30`, `devices 8`, `weight_decay 0.1`, and
long exit-token counts. Treat these commands as cluster/GPU recipes, not local
smoke tests. Verify data path and checkpoint storage before launching.

## Resume behavior

For stage 2/3, the trainer scans `proj_dir` for `rwkv-*.pth`, sorts the numeric
checkpoint suffixes, and loads the latest. If the latest checkpoint is corrupt,
newer code may fall back to the previous suffix. This means a stale high-numbered
checkpoint can silently override the base model you intended. Before a resume:

- List `proj_dir/rwkv-*.pth` sorted by suffix.
- Confirm `rwkv-init.pth`, `rwkv-final.pth`, and numeric checkpoints have the
  expected size and timestamp.
- Move unwanted checkpoints out of the run directory rather than deleting them.
- Record the expected `### Loading ... ###` line from startup logs.

## Loss and logging expectations

The README's MiniPile RWKV-7 example shows early losses near `4.875856`, then
`4.028621`, `3.801625`, and `3.663070` for the reference configuration. Large
deviations with the same data/config usually indicate data, initialization,
learning-rate, weight-decay, precision, or checkpoint-resume mistakes.

`train_log.txt` is append-only in the project directory and includes `NEW RUN`,
the argument dictionary, optional DeepSpeed config, and one line per saved
mini-epoch. Keep it with checkpoints when archiving a run.
