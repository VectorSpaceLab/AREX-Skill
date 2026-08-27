# ESPnet2 Training Troubleshooting

## Parser and config errors

- Use underscores in Python CLI flags (`--batch_size`, `--iterator_type`, `--optim_conf`).
- If `--print_config` output does not show a component option, select the class first, e.g. `--encoder conformer --print_config`.
- `*_conf` values can be repeated (`--optim_conf lr=0.001`) or passed as a YAML-style string; quote braces in shells.
- Many tasks require `--token_list` or a config entry. Dry-run placeholders are acceptable only when the task accepts them.

## Optional dependency failures

Map the traceback to the selected component: S3PRL frontend, Whisper encoder, Longformer, k2 inference/rescoring, FlashAttention, G2P, pyworld, or task metrics. Install the narrow dependency only if the user needs that component.

## Dry-run versus real training

`--iterator_type none --dry_run true` validates much of the parser/config/model construction path, but it does not validate real `data/`, dumps, tokenizer files, GPU memory, distributed setup, or recipe stage outputs. If dry-run passes and training fails, route data-file issues to `recipes-and-data` and backend/OOM issues to GPU diagnostics.

## Runtime training issues

- **CUDA OOM**: reduce `batch_size`, `batch_bins`, beam/nbest, model size, or mixed precision settings; verify GPU memory separately.
- **Resume/fine-tune mismatch**: check `--init_param` source/destination key mapping and `--ignore_init_mismatch` risk.
- **W&B failure**: disable `--use_wandb` for offline smoke checks or complete login/network setup.
- **Distributed hang**: verify `dist_backend`, launcher, world size/rank, NCCL availability, and cluster command settings.
