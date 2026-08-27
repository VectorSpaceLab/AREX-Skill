# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `cfg.model.arch.head.num_classes must equal len(cfg.class_names)` | config mismatch | align the class list and head class count |
| old `.pth` checkpoint warning | checkpoint is in the legacy format | convert it before reuse |
| `save_key` not found in eval results | evaluator config and metric do not match | check the evaluator name and `save_key` |
| logger/TensorBoard import failure | `tensorboard` missing | install the logger dependency |
| multiprocessing warnings or hangs | start method or thread-count conflict | use the repo helper or set the config appropriately |
| resume/load state mismatch | the checkpoint comes from a different model shape | use the matching config or a converted checkpoint |
| CPU run behaves oddly with AMP settings | the config still requests GPU-oriented precision | set CPU mode and keep precision at 32 |

## Recovery pattern

1. Validate the config and dataset first.
2. Re-run the skill-owned training or test launcher.
3. If the checkpoint is old, convert it once and reuse the converted file.
4. Check the logs in `save_dir` before changing more code.
