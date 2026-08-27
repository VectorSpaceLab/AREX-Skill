# Training and Evaluation Workflows

## Dependency boundary

Training uses more than inference. In addition to `torch` and `transformers`, expect PyTorch Lightning, torchmetrics, datasets, Hydra, rich, pyrootutils, and optional loggers. Install only the dependencies needed for the selected workflow.

## Command pattern

The source launchers set `TOKENIZERS_PARALLELISM=false` and run the train/eval entry point with Hydra arguments. Use the bundled command builder first:

```bash
python scripts/build_train_command.py --mode train --experiment cws --trainer cpu
python scripts/build_train_command.py --mode train --experiment multi --trainer gpu --overrides seed=123 tags='[custom]'
python scripts/build_train_command.py --mode eval --experiment dep --ckpt-path /models/best.ckpt
```

The output is a command template; it does not run training.

## Train flow

1. Choose a task experiment: `cws`, `pos`, `ner`, `srl`, `dep`, `sdp`, `multi`, `multi_bi`, or `cls` if using sentence classification code.
2. Validate data layout with `validate_ltp_training_data.py`.
3. Choose trainer backend: `cpu`, `gpu`, `mps`, or a distributed variant only when the environment supports it.
4. Decide logger policy. Use no logger or local CSV/TensorBoard unless credentials are available.
5. Build the command and review Hydra overrides.
6. Run only after user approval for compute, data, model backbone downloads, and output writes.

## Eval flow

Evaluation requires a checkpoint path.

```bash
python scripts/build_train_command.py --mode eval --experiment dep --ckpt-path /path/to/best.ckpt --trainer cpu
```

If `ckpt_path` is omitted, `ltp_core.eval` asserts/fails. Validate the checkpoint path before starting a job.

## Tiny verification vs real training

- A tiny data-format validation or command-builder test can run in ordinary CPU environments.
- `python/core/tests/test_crf.py` is a safe native CPU candidate for the CRF component after skill integration.
- Real training is long-running and may download/load pretrained backbones. Treat it as user-approved execution, not an automatic diagnostic.

## Checkpoint and output handling

- Training can evaluate on the test set using the best checkpoint selected by callbacks.
- If no best checkpoint exists, code may fall back to current weights and log a warning.
- Preserve run directories, Hydra configs, and metrics together so results can be reproduced.
- For eval-only runs, record the exact checkpoint path, config overrides, and package versions.
