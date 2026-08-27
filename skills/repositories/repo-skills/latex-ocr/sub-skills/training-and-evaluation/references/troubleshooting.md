# Training and Evaluation Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: torchtext`, `Levenshtein`, `imagesize`, or `wandb` | `[train]` extra missing or partially installed. | Install `pip install "pix2tex[train]"`; install W&B only if logging is desired. |
| Config references missing `train.pkl`, `val.pkl`, or tokenizer | Dataset preparation not complete or paths wrong. | Use the data-preparation sub-skill and config summary helper before training. |
| `RuntimeError` from GPU memory check | Batch or maximum image size too large for GPU. | Lower `batchsize` or set `micro_batchsize`; reduce `max_width`/`max_height` only with compatible data/checkpoints. |
| Checkpoint load shape mismatch | Architecture/tokenizer/config differs from checkpoint. | Use the original config/tokenizer with the checkpoint or retrain from compatible settings. |
| Training starts W&B unexpectedly | `wandb` is enabled when not in debug mode. | Set `debug: true`, disable W&B in config, or configure W&B credentials intentionally. |
| Evaluation prints low/zero metrics | Wrong validation data, tokenizer mismatch, or bad checkpoint. | Verify dataset pickle, tokenizer JSON, config, and checkpoint were produced together. |
| CPU training/evaluation is very slow | Model is deep-learning heavy and CPU-only. | Use CPU only for tiny smoke checks; use CUDA after verifying a compatible PyTorch build. |
| `python -m pix2tex.eval --help` fails before showing help | Module imports `torchtext` before argparse. | Install `[train]` or inspect commands from this reference instead of relying on `--help`. |
